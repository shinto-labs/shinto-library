"""Query execution handler for Mimir context."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from psycopg.errors import RaiseException

from shinto.mimir.exception import (
    MimirEntityAlreadyExistsException,
    MimirEntityException,
    MimirEntityNotFoundException,
    MimirException,
)

if TYPE_CHECKING:
    from shinto.pg.connection import AsyncConnection, Connection


def _get_identifier_from_params(params: None | dict | tuple | list) -> str:
    """Extract an identifier from the query parameters."""
    if isinstance(params, dict):
        return next(
            (str(value) for key, value in params.items() if "id" in key or "name" in key),
            "",
        )
    return ""


def execute_query(
    connection: Connection, query: str, params: None | dict | tuple | list = None
) -> Any:  # noqa: ANN401
    """Execute a database query."""
    """Execute a database query asynchronously."""
    try:
        result = connection.execute_query(query, params)
    except RaiseException as e:
        logging.debug("Query: %s failed with params: %s", query, params)
        msg = e.diag.message_primary
        if "does not have access" in msg:
            raise MimirEntityException(msg) from e
        if "already in use" in msg:
            raise MimirEntityAlreadyExistsException(msg) from e
        raise MimirException(msg) from e

    if not result or not result[0] or not result[0][0]:
        logging.debug("Query: %s failed with params: %s", query, params)
        identifier = _get_identifier_from_params(params)
        raise MimirEntityNotFoundException(f"Entity not found by name or id: {identifier}")
    return result[0][0]


async def execute_query_async(
    connection: AsyncConnection, query: str, params: None | dict | tuple | list = None
) -> Any:  # noqa: ANN401
    """Execute a database query asynchronously."""
    try:
        result = await connection.execute_query(query, params)
    except RaiseException as e:
        logging.debug("Query: %s failed with params: %s", query, params)
        msg = e.diag.message_primary
        if "does not have access" in msg:
            raise MimirEntityException(msg) from e
        if "already in use" in msg:
            raise MimirEntityAlreadyExistsException(msg) from e
        raise MimirException(msg) from e

    if not result or not result[0] or not result[0][0]:
        logging.debug("Query: %s failed with params: %s", query, params)
        identifier = _get_identifier_from_params(params)
        raise MimirEntityNotFoundException(f"Entity not found by name or id: {identifier}")
    return result[0][0]
