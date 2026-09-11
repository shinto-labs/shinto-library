"""QC pack management functions for Shinto Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.query_execution_handler import execute_query, execute_query_async

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import AsyncConnection, Connection

GET_QC_PACK_QUERY = """
SELECT to_json(data.get_qc_pack(
    %(action_by)s::uuid, %(qc_pack_id)s::uuid, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_QC_PACK_BY_NAME_QUERY = """
SELECT to_json(data.get_qc_pack_by_name(
    %(action_by)s::uuid, %(qc_pack_name)s::text, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_QC_PACK_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_qc_pack_history(%(action_by)s::uuid, %(qc_pack_id)s::uuid) AS row"""
GET_QC_PACK_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_qc_pack_list(%(action_by)s::uuid, %(timestamp)s::TIMESTAMPTZ) AS row"""
CREATE_QC_PACK_QUERY = """
SELECT to_json(data.create_qc_pack(
    %(action_by)s::uuid, %(name)s::text, %(data)s::jsonb, %(action_info)s::jsonb
))
"""
UPDATE_QC_PACK_QUERY = """
SELECT to_json(data.update_qc_pack(
    %(action_by)s::uuid,
    %(qc_pack_id)s::uuid,
    %(name)s::text,
    %(data)s::jsonb,
    %(action_info)s::jsonb
))
"""
DELETE_QC_PACK_QUERY = """
SELECT to_json(data.delete_qc_pack(
    %(action_by)s::uuid, %(qc_pack_id)s::uuid, %(action_info)s::jsonb
))
"""


def get_qc_pack_by_id(
    connection: Connection,
    action_by: UUID,
    qc_pack_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a QC pack by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "qc_pack_id": qc_pack_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_QC_PACK_QUERY, **params)


async def get_qc_pack_by_id_async(
    connection: AsyncConnection,
    action_by: UUID,
    qc_pack_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a QC pack by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "qc_pack_id": qc_pack_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_QC_PACK_QUERY, **params)


def get_qc_pack_by_name(
    connection: Connection,
    action_by: UUID,
    qc_pack_name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a QC pack by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "qc_pack_name": qc_pack_name,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_QC_PACK_BY_NAME_QUERY, **params)


async def get_qc_pack_by_name_async(
    connection: AsyncConnection,
    action_by: UUID,
    qc_pack_name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a QC pack by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "qc_pack_name": qc_pack_name,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_QC_PACK_BY_NAME_QUERY, **params)


def get_qc_pack_history(connection: Connection, action_by: UUID, qc_pack_id: UUID) -> list[dict]:
    """Get the history of a QC pack."""
    params = {"action_by": action_by, "qc_pack_id": qc_pack_id}
    return execute_query(connection, GET_QC_PACK_HISTORY_QUERY, **params)


async def get_qc_pack_history_async(
    connection: AsyncConnection, action_by: UUID, qc_pack_id: UUID
) -> list[dict]:
    """Get the history of a QC pack."""
    params = {"action_by": action_by, "qc_pack_id": qc_pack_id}
    return await execute_query_async(connection, GET_QC_PACK_HISTORY_QUERY, **params)


def get_qc_pack_list(
    connection: Connection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of QC packs. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return execute_query(connection, GET_QC_PACK_LIST_QUERY, **params)


async def get_qc_pack_list_async(
    connection: AsyncConnection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of QC packs. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return await execute_query_async(connection, GET_QC_PACK_LIST_QUERY, **params)


def create_qc_pack(
    connection: Connection,
    action_by: UUID,
    name: str,
    data: dict | None,
    action_info: dict | None = None,
) -> dict:
    """Create a QC pack."""
    params = {
        "action_by": action_by,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, CREATE_QC_PACK_QUERY, **params)


async def create_qc_pack_async(
    connection: AsyncConnection,
    action_by: UUID,
    name: str,
    data: dict | None,
    action_info: dict | None = None,
) -> dict:
    """Create a QC pack."""
    params = {
        "action_by": action_by,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, CREATE_QC_PACK_QUERY, **params)


def update_qc_pack(
    connection: Connection,
    action_by: UUID,
    qc_pack_id: UUID,
    name: str | None = None,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a QC pack. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "qc_pack_id": qc_pack_id,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, UPDATE_QC_PACK_QUERY, **params)


async def update_qc_pack_async(
    connection: AsyncConnection,
    action_by: UUID,
    qc_pack_id: UUID,
    name: str | None = None,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a QC pack. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "qc_pack_id": qc_pack_id,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, UPDATE_QC_PACK_QUERY, **params)


def delete_qc_pack(
    connection: Connection, action_by: UUID, qc_pack_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a QC pack. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "qc_pack_id": qc_pack_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, DELETE_QC_PACK_QUERY, **params)


async def delete_qc_pack_async(
    connection: AsyncConnection, action_by: UUID, qc_pack_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a QC pack. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "qc_pack_id": qc_pack_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, DELETE_QC_PACK_QUERY, **params)
