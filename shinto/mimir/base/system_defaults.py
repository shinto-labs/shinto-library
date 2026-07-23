"""System defaults management functions for Shinto Mimir."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.query_execution_handler import execute_query, execute_query_async

if TYPE_CHECKING:
    from datetime import datetime

    from shinto.pg.connection import AsyncConnection, Connection


CREATE_SYSTEM_DEFAULT_QUERY = """
SELECT to_json(base.create_system_default(
    %(name)s::text, %(value)s::text
))
"""
GET_SYSTEM_DEFAULT_QUERY = """
SELECT to_json(base.get_system_default(
    %(name)s::text, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_SYSTEM_DEFAULT_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM base.get_system_default_history(%(name)s::text) AS row"""
GET_SYSTEM_DEFAULT_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM base.get_system_default_list(%(timestamp)s::TIMESTAMPTZ) AS row"""
UPDATE_SYSTEM_DEFAULT_QUERY = """
SELECT to_json(base.update_system_default(
    %(name)s::text, %(value)s::text
))
"""
DELETE_SYSTEM_DEFAULT_QUERY = "SELECT to_json(base.delete_system_default(%(name)s::text))"


def create_system_default(connection: Connection, name: str, value: str) -> dict:
    """Create a system default."""
    params = {"name": name, "value": value}
    return execute_query(connection, CREATE_SYSTEM_DEFAULT_QUERY, **params)


async def create_system_default_async(connection: AsyncConnection, name: str, value: str) -> dict:
    """Create a system default."""
    params = {"name": name, "value": value}
    return await execute_query_async(connection, CREATE_SYSTEM_DEFAULT_QUERY, **params)


def get_system_default(
    connection: Connection, name: str, timestamp: datetime | str | None = None
) -> dict:
    """Get a system default by name."""
    params = {"name": name, "timestamp": normalize_timestamp(timestamp)}
    return execute_query(connection, GET_SYSTEM_DEFAULT_QUERY, **params)


async def get_system_default_async(
    connection: AsyncConnection, name: str, timestamp: datetime | str | None = None
) -> dict:
    """Get a system default by name."""
    params = {"name": name, "timestamp": normalize_timestamp(timestamp)}
    return await execute_query_async(connection, GET_SYSTEM_DEFAULT_QUERY, **params)


def get_system_default_history(connection: Connection, name: str) -> list[dict]:
    """Get the history of a system default."""
    params = {"name": name}
    return execute_query(connection, GET_SYSTEM_DEFAULT_HISTORY_QUERY, **params)


async def get_system_default_history_async(connection: AsyncConnection, name: str) -> list[dict]:
    """Get the history of a system default."""
    params = {"name": name}
    return await execute_query_async(connection, GET_SYSTEM_DEFAULT_HISTORY_QUERY, **params)


def get_system_default_list(
    connection: Connection, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of system defaults."""
    params = {"timestamp": normalize_timestamp(timestamp)}
    return execute_query(connection, GET_SYSTEM_DEFAULT_LIST_QUERY, **params)


async def get_system_default_list_async(
    connection: AsyncConnection, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of system defaults."""
    params = {"timestamp": normalize_timestamp(timestamp)}
    return await execute_query_async(connection, GET_SYSTEM_DEFAULT_LIST_QUERY, **params)


def update_system_default(connection: Connection, name: str, value: str) -> dict:
    """Update a system default."""
    params = {"name": name, "value": value}
    return execute_query(connection, UPDATE_SYSTEM_DEFAULT_QUERY, **params)


async def update_system_default_async(connection: AsyncConnection, name: str, value: str) -> dict:
    """Update a system default."""
    params = {"name": name, "value": value}
    return await execute_query_async(connection, UPDATE_SYSTEM_DEFAULT_QUERY, **params)


def delete_system_default(connection: Connection, name: str) -> dict:
    """Delete a system default."""
    params = {"name": name}
    return execute_query(connection, DELETE_SYSTEM_DEFAULT_QUERY, **params)


async def delete_system_default_async(connection: AsyncConnection, name: str) -> dict:
    """Delete a system default."""
    params = {"name": name}
    return await execute_query_async(connection, DELETE_SYSTEM_DEFAULT_QUERY, **params)
