"""
Resolve pinned artifacts and build runContext for QC reports.

HTTP QC runs are pin-driven: callers select a schema_package (datakader), and this
module loads refs.qc_pack + refs.project_data from Postgres. We intentionally do
not fall back to module files or "latest by name" for those artifacts at runtime —
missing or ambiguous pins fail fast so reports stay auditable.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any
from uuid import UUID

from shinto.mimir.base import get_mimir_version_async
from shinto.mimir.data import (
    get_qc_pack_by_id_async,
    get_schema_package_by_id_async,
    get_schema_package_by_name_async,
    get_schema_package_list_async,
    get_taxonomy_by_id_async,
)

if TYPE_CHECKING:
    from shinto.pg.connection import AsyncConnection

logger = logging.getLogger(__name__)

QC_RUNNER_VERSION = "1.1.0"
DEFAULT_SCHEMA_PACKAGE_NAME = "default"


def record_to_pack(record: dict[str, Any] | None) -> dict[str, Any] | None:
    """Merge Bifrost qc_pack record into portable pack export shape."""
    if not record:
        return None
    data = record.get("data")
    if not isinstance(data, dict):
        return None
    pack = dict(data)
    if record.get("id"):
        pack["id"] = str(record["id"])
    if record.get("timestamp"):
        pack["publishedAt"] = record["timestamp"]
    return pack


def _taxonomy_data(record: Any) -> dict | None:
    if not record:
        return None
    if isinstance(record, dict):
        if isinstance(record.get("fields"), list):
            return record
        data = record.get("data")
        if isinstance(data, dict) and isinstance(data.get("fields"), list):
            return data
        if isinstance(data, dict):
            return data
    return None


def artifact_pin(record: dict[str, Any] | None, *, extra: dict[str, Any] | None = None) -> dict[str, Any] | None:
    if not record:
        return None
    summary: dict[str, Any] = {
        "id": str(record["id"]),
        "timestamp": record["timestamp"],
    }
    if record.get("name") is not None:
        summary["name"] = record["name"]
    if record.get("action") is not None:
        summary["action"] = record["action"]
    data = record.get("data")
    if isinstance(data, dict):
        if data.get("version") is not None:
            summary["version"] = data.get("version")
        if isinstance(data.get("fields"), list):
            summary["fieldCount"] = len(data["fields"])
        if isinstance(data.get("rules"), list):
            summary["rulesCount"] = len(data["rules"])
    if extra:
        summary.update(extra)
    return summary


async def _load_schema_package_record(
    user_id: UUID,
    connection: AsyncConnection,
    *,
    schema_package_id: UUID | None = None,
    timestamp: str | None = None,
    schema_package_name: str | None = None,
) -> dict[str, Any]:
    from fastapi import HTTPException

    if schema_package_id:
        logger.debug(
            "Loading schema_package by id=%s timestamp=%s",
            schema_package_id,
            timestamp,
        )
        return await get_schema_package_by_id_async(
            connection, user_id, schema_package_id, timestamp
        )

    name = schema_package_name or DEFAULT_SCHEMA_PACKAGE_NAME
    last_exc: Exception | None = None
    try:
        logger.debug("Loading schema_package by name=%r timestamp=%s", name, timestamp)
        return await get_schema_package_by_name_async(
            connection, user_id, name, timestamp
        )
    except Exception as exc:
        last_exc = exc
        logger.warning("schema_package by name %r failed: %s", name, exc)

    packages = await get_schema_package_list_async(connection, user_id, timestamp)
    if len(packages) == 1:
        logger.info(
            "Falling back to sole schema_package id=%s name=%s",
            packages[0].get("id"),
            packages[0].get("name"),
        )
        return packages[0]
    if not packages:
        logger.error("No schema_package found for user_id=%s", user_id)
        raise HTTPException(
            status_code=404,
            detail="No schema_package (datakader) in database. Load a tenant dump or publish a pin.",
        ) from last_exc
    logger.error(
        "Ambiguous schema_package selection: count=%s user_id=%s",
        len(packages),
        user_id,
    )
    raise HTTPException(
        status_code=400,
        detail=(
            "Multiple schema packages found; pass schema_package_id (and optional timestamp) "
            "to select the datakader for this QC run."
        ),
    ) from last_exc


async def _load_qc_pack_from_ref(
    user_id: UUID,
    connection: AsyncConnection,
    ref: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    from fastapi import HTTPException

    if not ref or not ref.get("id"):
        logger.error("schema_package missing refs.qc_pack")
        raise HTTPException(
            status_code=400,
            detail="schema_package is missing refs.qc_pack; cannot run QC.",
        )
    logger.debug(
        "Loading qc_pack ref id=%s timestamp=%s",
        ref.get("id"),
        ref.get("timestamp"),
    )
    record = await get_qc_pack_by_id_async(
        connection,
        user_id,
        UUID(str(ref["id"])),
        ref.get("timestamp"),
    )
    pack = record_to_pack(record)
    if not pack:
        logger.error("QC pack not found for ref id=%s", ref.get("id"))
        raise HTTPException(
            status_code=404,
            detail=f"QC pack not found for ref {ref.get('id')}",
        )
    logger.debug(
        "Loaded qc_pack version=%s rules=%s",
        pack.get("version"),
        len(pack.get("rules") or []),
    )
    return pack, record


async def _load_taxonomy_from_ref(
    user_id: UUID,
    connection: AsyncConnection,
    ref: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    from fastapi import HTTPException

    if not ref or not ref.get("id"):
        logger.error("schema_package missing refs.project_data")
        raise HTTPException(
            status_code=400,
            detail="schema_package is missing refs.project_data; cannot run QC.",
        )
    logger.debug(
        "Loading taxonomy ref id=%s timestamp=%s",
        ref.get("id"),
        ref.get("timestamp"),
    )
    record = await get_taxonomy_by_id_async(
        connection,
        user_id,
        UUID(str(ref["id"])),
        ref.get("timestamp"),
    )
    taxonomy = _taxonomy_data(record)
    field_count = len((taxonomy or {}).get("fields") or [])
    logger.debug("Loaded taxonomy fields=%s", field_count)
    return taxonomy, record


async def platform_context(connection: AsyncConnection) -> dict[str, Any]:
    ctx: dict[str, Any] = {"qcRunnerVersion": QC_RUNNER_VERSION}
    try:
        ctx["mimirVersion"] = await get_mimir_version_async(connection)
    except Exception as exc:
        logger.warning("Failed to read mimir version: %s", exc)
        ctx["mimirVersion"] = None
    try:
        import shinto
        from importlib.metadata import version
        from pathlib import Path

        # Prefer version next to the loaded package (PYTHONPATH mount), then
        # fall back to installed distribution metadata (backend image pin).
        ctx["shintoLibraryVersion"] = None
        pyproject = Path(shinto.__file__).resolve().parents[1] / "pyproject.toml"
        if pyproject.is_file():
            for line in pyproject.read_text(encoding="utf-8").splitlines():
                if line.startswith("version"):
                    # version = "1.2.40"
                    ctx["shintoLibraryVersion"] = line.split("=", 1)[1].strip().strip("\"'")
                    break
        if not ctx["shintoLibraryVersion"]:
            ctx["shintoLibraryVersion"] = version("shinto")
    except Exception as exc:
        logger.warning("Failed to resolve shinto library version: %s", exc)
        ctx["shintoLibraryVersion"] = None
    tag = os.environ.get("BACKEND_IMAGE_TAG")
    if tag:
        ctx["backendImageTag"] = tag
    logger.debug("Platform context: %s", ctx)
    return ctx


def build_run_context(
    *,
    schema_package_record: dict[str, Any],
    qc_pack_record: dict[str, Any],
    taxonomy_record: dict[str, Any] | None,
    platform: dict[str, Any],
) -> dict[str, Any]:
    refs = (schema_package_record.get("data") or {}).get("refs") or {}
    pack_body = qc_pack_record.get("data") or {}

    return {
        "schemaPackage": schema_package_record,
        "refs": refs,
        "artifacts": {
            "qcPack": artifact_pin(
                qc_pack_record,
                extra={
                    "policyVersion": pack_body.get("version"),
                    "taxonomyName": pack_body.get("taxonomyName"),
                },
            ),
            "projectDataTaxonomy": artifact_pin(taxonomy_record),
            "config": refs.get("config"),
        },
        "platform": platform,
    }


async def resolve_qc_run(
    user_id: UUID,
    connection: AsyncConnection,
    *,
    schema_package_id: UUID | None = None,
    timestamp: str | None = None,
    schema_package_name: str | None = None,
) -> dict[str, Any]:
    """Load pack, taxonomy, and runContext from an explicit schema_package pin.

    Used by GET /juno/qc_report. The returned pack/taxonomy are the only inputs
    passed to run_qc().
    """
    logger.info(
        "Resolving QC run: user_id=%s schema_package_id=%s schema_package_name=%s timestamp=%s",
        user_id,
        schema_package_id,
        schema_package_name,
        timestamp,
    )
    schema_package_record = await _load_schema_package_record(
        user_id,
        connection,
        schema_package_id=schema_package_id,
        timestamp=timestamp,
        schema_package_name=schema_package_name,
    )
    refs = (schema_package_record.get("data") or {}).get("refs") or {}
    pack, qc_pack_record = await _load_qc_pack_from_ref(
        user_id, connection, refs.get("qc_pack")
    )
    taxonomy, taxonomy_record = await _load_taxonomy_from_ref(
        user_id, connection, refs.get("project_data")
    )
    platform = await platform_context(connection)
    run_context = build_run_context(
        schema_package_record=schema_package_record,
        qc_pack_record=qc_pack_record,
        taxonomy_record=taxonomy_record,
        platform=platform,
    )
    logger.info(
        "QC run resolved: schema_package_id=%s pack_version=%s taxonomy_fields=%s",
        schema_package_record.get("id"),
        pack.get("version"),
        len((taxonomy or {}).get("fields") or []),
    )
    return {
        "pack": pack,
        "taxonomy": taxonomy,
        "runContext": run_context,
    }
