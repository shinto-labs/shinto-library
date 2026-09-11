"""Query execution handler for Mimir context."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from psycopg.errors import RaiseException

from shinto.mimir.exception import (
    MimirAccessDeniedException,
    MimirEntityAlreadyExistsException,
    MimirEntityNotFoundException,
    MimirException,
)

if TYPE_CHECKING:
    from psycopg import AsyncConnection, Connection


def _get_identifier_from_params(params: dict) -> str:
    """Extract an identifier from the query parameters."""
    return ", ".join(
        f"{key}={value}" for key, value in params.items() if "id" in key or "name" in key
    )


def _rollback(connection: Connection) -> None:
    """Clear aborted transaction state after a failed statement."""
    try:
        connection.rollback()
    except Exception:
        logging.debug("rollback after failed query failed", exc_info=True)


async def _rollback_async(connection: AsyncConnection) -> None:
    """Clear aborted transaction state after a failed statement."""
    try:
        await connection.rollback()
    except Exception:
        logging.debug("rollback after failed query failed", exc_info=True)


def _raise_from_pg_exception(e: RaiseException, query: str, params: dict) -> None:
    """Map a Postgres RAISE EXCEPTION to a Mimir exception (always raises)."""
    logging.debug("Query: %s failed with params: %s", query, params)
    msg = e.diag.message_primary
    if "does not have access" in msg:
        raise MimirAccessDeniedException(
            f"User does not have access: {params.get('action_by')}"
        ) from e
    if "already in use" in msg:
        identifier = _get_identifier_from_params(params)
        raise MimirEntityAlreadyExistsException(
            f"Entity already exists with: {identifier}"
        ) from e
    raise MimirException(msg) from e


def execute_query(
    connection: Connection, query: str, return_result: bool = True, **params: dict
) -> Any:  # noqa: ANN401
    """Execute a database query with Mimir Exception handling."""
    try:
        with connection.cursor() as cur:
            cur.execute(query, params)
            result = cur.fetchall()
    except RaiseException as e:
        _rollback(connection)
        _raise_from_pg_exception(e, query, params)

    if not return_result:
        return None

    if not result or not result[0] or result[0][0] is None:
        logging.debug("Query: %s failed with params: %s", query, params)
        identifier = _get_identifier_from_params(params)
        raise MimirEntityNotFoundException(f"Entity not found with: {identifier}")

    return result[0][0]


async def execute_query_async(
    connection: AsyncConnection, query: str, return_result: bool = True, **params: dict
) -> Any:  # noqa: ANN401
    """Execute a database query asynchronously."""
    try:
        async with connection.cursor() as cur:
            await cur.execute(query, params)
            result = await cur.fetchall()
    except RaiseException as e:
        await _rollback_async(connection)
        _raise_from_pg_exception(e, query, params)

    if not return_result:
        return None

    if not result or not result[0] or result[0][0] is None:
        logging.debug("Query: %s failed with params: %s", query, params)
        identifier = _get_identifier_from_params(params)
        raise MimirEntityNotFoundException(f"Entity not found with: {identifier}")

    return result[0][0]