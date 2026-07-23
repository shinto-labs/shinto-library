"""Base internal functions for Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.mimir.query_execution_handler import execute_query, execute_query_async

if TYPE_CHECKING:
    from uuid import UUID

    from shinto.pg.connection import AsyncConnection, Connection


GET_DEFAULT_USER_QUERY = "SELECT to_json(base.get_shintolabs_user())"
GET_DEFAULT_USER_ID_QUERY = "SELECT (base.get_shintolabs_user()).id"
GET_MIMIR_VERSION_QUERY = "SELECT base.mimir_version()"
DUMP_DATABASE_TO_JSON_QUERY = """
SELECT base.dump_database_to_json(
    %(include_base)s, %(include_audit)s
)
"""
LOAD_JSON_TO_TABLE_QUERY = """
SELECT base.load_json_to_table(
    %(table_name)s, %(data)s::jsonb, %(update_action_by)s
)
"""


def get_default_user(connection: Connection) -> dict:
    """Get the default user."""
    return execute_query(connection, GET_DEFAULT_USER_QUERY)


async def get_default_user_async(connection: AsyncConnection) -> dict:
    """Get the default user asynchronously."""
    return await execute_query_async(connection, GET_DEFAULT_USER_QUERY)


def get_default_user_id(connection: Connection) -> UUID:
    """Get the default user ID."""
    return execute_query(connection, GET_DEFAULT_USER_ID_QUERY)


async def get_default_user_id_async(connection: AsyncConnection) -> UUID:
    """Get the default user ID asynchronously."""
    return await execute_query_async(connection, GET_DEFAULT_USER_ID_QUERY)


def get_mimir_version(connection: Connection) -> str:
    """Get the Mimir version."""
    return execute_query(connection, GET_MIMIR_VERSION_QUERY)


async def get_mimir_version_async(connection: AsyncConnection) -> str:
    """Get the Mimir version asynchronously."""
    return await execute_query_async(connection, GET_MIMIR_VERSION_QUERY)


def dump_database_to_json(
    connection: Connection, include_base: bool = True, include_audit: bool = True
) -> str:
    """Dump the entire database as JSON."""
    params = {"include_base": include_base, "include_audit": include_audit}
    return execute_query(connection, DUMP_DATABASE_TO_JSON_QUERY, **params)


async def dump_database_to_json_async(
    connection: AsyncConnection, include_base: bool = True, include_audit: bool = True
) -> str:
    """Dump the entire database as JSON asynchronously."""
    params = {"include_base": include_base, "include_audit": include_audit}
    return await execute_query_async(connection, DUMP_DATABASE_TO_JSON_QUERY, **params)


def load_table(
    connection: Connection, table_name: str, data: list[dict], update_action_by: bool = False
) -> None:
    """Load JSON data into a table."""
    params = {
        "table_name": table_name,
        "data": json.dumps(data),
        "update_action_by": update_action_by,
    }
    execute_query(connection, LOAD_JSON_TO_TABLE_QUERY, **params, return_result=False)


async def load_table_async(
    connection: AsyncConnection, table_name: str, data: list[dict], update_action_by: bool = False
) -> None:
    """Load JSON data into a table asynchronously."""
    params = {
        "table_name": table_name,
        "data": json.dumps(data),
        "update_action_by": update_action_by,
    }
    await execute_query_async(connection, LOAD_JSON_TO_TABLE_QUERY, **params, return_result=False)
