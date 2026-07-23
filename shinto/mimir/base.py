"""Internal functions for Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.mimir.exception import MimirException

if TYPE_CHECKING:
    from uuid import UUID

    from shinto.pg.connection import Connection


GET_DEFAULT_USER_QUERY = "SELECT to_json(base.get_shintolabs_user())"
GET_DEFAULT_USER_ID_QUERY = "SELECT (base.get_shintolabs_user()).id"
GET_MIMIR_VERSION_QUERY = "SELECT base.mimir_version()"
DUMP_DATABASE_TO_JSON_QUERY = "SELECT base.dump_database_to_json(%s, %s)"
LOAD_JSON_TO_TABLE_QUERY = "SELECT base.load_json_to_table(%s, %s::jsonb, %s)"


def get_default_user(connection: Connection) -> dict:
    """Get the default user."""
    result = connection.execute_query(GET_DEFAULT_USER_QUERY)

    if not result or not result[0][0]:
        raise MimirException("Failed to get default user")
    return result[0][0]


def get_default_user_id(connection: Connection) -> UUID:
    """Get the default user ID."""
    result = connection.execute_query(GET_DEFAULT_USER_ID_QUERY)

    if not result or not result[0][0]:
        raise MimirException("Failed to get default user ID")
    return result[0][0]


def get_mimir_version(connection: Connection) -> str:
    """Get the Mimir version."""
    result = connection.execute_query(GET_MIMIR_VERSION_QUERY)

    if not result or not result[0][0]:
        raise MimirException("Failed to get Mimir version")
    return result[0][0]


def dump_database_to_json(
    connection: Connection, include_base: bool = True, include_audit: bool = True
) -> str:
    """Dump the entire database as JSON."""
    result = connection.execute_query(DUMP_DATABASE_TO_JSON_QUERY, (include_base, include_audit))
    if not result or not result[0][0]:
        raise MimirException("Failed to dump database to JSON.")
    return result[0][0]


def load_table(
    connection: Connection, table_name: str, data: list[dict], update_action_by: bool = False
) -> None:
    """Load JSON data into a table."""
    try:
        connection.execute_query(
            LOAD_JSON_TO_TABLE_QUERY,
            (table_name, json.dumps(data), update_action_by),
        )
    except Exception as e:
        raise MimirException(f"Failed to load table: {e}.") from e
