"""Query execution handler for Mimir context."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from psycopg.errors import RaiseException

from shinto.mimir.exception import (
    MimirAccessDeniedException,
    MimirEntityAlreadyExistsException,
    MimirEntityException,
    MimirEntityNotFoundException,
    MimirException,
)

if TYPE_CHECKING:
    from shinto.pg.connection import AsyncConnection, Connection


def _get_identifier_from_params(params: dict) -> str:
    """Extract an identifier from the query parameters."""
    return ", ".join(
        f"{key}={value}" for key, value in params.items() if "id" in key or "name" in key
    )


def execute_query(
    connection: Connection, query: str, return_result: bool = True, **params: dict
) -> Any:  # noqa: ANN401
    """Execute a database query with Mimir Exception handling."""
    try:
        result = connection.execute_query(query, params)
    except RaiseException as e:
        logging.debug("Query: %s failed with params: %s", query, params)
        msg = e.diag.message_primary
        if "does not have access" in msg:
            raise MimirEntityException(
                f"User does not have access: {params.get('action_by')}"
            ) from e
        if "already in use" in msg:
            identifier = _get_identifier_from_params(params)
            raise MimirEntityAlreadyExistsException(
                f"Entity already exists with: {identifier}"
            ) from e
        raise MimirException(msg) from e

    if not return_result:
        return None

    if not result or not result[0] or not result[0][0]:
        logging.debug("Query: %s failed with params: %s", query, params)
        identifier = _get_identifier_from_params(params)
        raise MimirEntityNotFoundException(f"Entity not found with: {identifier}")

    return result[0][0]


async def execute_query_async(
    connection: AsyncConnection, query: str, return_result: bool = True, **params: dict
) -> Any:  # noqa: ANN401
    """Execute a database query asynchronously."""
    try:
        result = await connection.execute_query(query, params)
    except RaiseException as e:
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

    if not return_result:
        return None

    if not result or not result[0] or not result[0][0]:
        logging.debug("Query: %s failed with params: %s", query, params)
        identifier = _get_identifier_from_params(params)
        raise MimirEntityNotFoundException(f"Entity not found with: {identifier}")

    return result[0][0]
