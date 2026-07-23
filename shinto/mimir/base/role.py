"""Role management functions for Shinto Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.query_execution_handler import execute_query, execute_query_async

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import AsyncConnection, Connection


CREATE_ROLE_QUERY = """
SELECT to_json(base.create_role(
    %(action_by)s::uuid, %(name)s::text, %(data)s::jsonb, %(action_info)s::jsonb
))
"""
GET_ROLE_QUERY = "SELECT to_json(base.get_role(%(name)s::text, %(timestamp)s::TIMESTAMPTZ))"
GET_ROLE_BY_NAME_QUERY = "SELECT to_json(base.get_role_by_name(%(name)s::text))"
GET_ROLE_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM base.get_role_history(%(name)s::text) AS row"""
GET_ROLE_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM base.get_role_list(%(timestamp)s::TIMESTAMPTZ) AS row"""
UPDATE_ROLE_QUERY = """
SELECT to_json(base.update_role(
    %(action_by)s::uuid, %(name)s::text, %(data)s::jsonb, %(action_info)s::jsonb
))
"""
DELETE_ROLE_QUERY = """
SELECT to_json(base.delete_role(
    %(action_by)s::uuid, %(name)s::text, %(action_info)s::jsonb
))
"""


def create_role(
    connection: Connection,
    action_by: UUID,
    name: str,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Create a role."""
    params = {
        "action_by": action_by,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, CREATE_ROLE_QUERY, **params)


async def create_role_async(
    connection: AsyncConnection,
    action_by: UUID,
    name: str,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Create a role."""
    params = {
        "action_by": action_by,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, CREATE_ROLE_QUERY, **params)


def get_role(connection: Connection, name: str, timestamp: datetime | str | None = None) -> dict:
    """Get a role by name."""
    params = {"name": name, "timestamp": normalize_timestamp(timestamp)}
    return execute_query(connection, GET_ROLE_QUERY, **params)


async def get_role_async(
    connection: AsyncConnection, name: str, timestamp: datetime | str | None = None
) -> dict:
    """Get a role by name."""
    params = {"name": name, "timestamp": normalize_timestamp(timestamp)}
    return await execute_query_async(connection, GET_ROLE_QUERY, **params)


def get_role_by_name(connection: Connection, name: str) -> dict:
    """Get a role by name."""
    params = {"name": name}
    return execute_query(connection, GET_ROLE_BY_NAME_QUERY, **params)


async def get_role_by_name_async(connection: AsyncConnection, name: str) -> dict:
    """Get a role by name."""
    params = {"name": name}
    return await execute_query_async(connection, GET_ROLE_BY_NAME_QUERY, **params)


def get_role_history(connection: Connection, name: str) -> list[dict]:
    """Get the history of a role."""
    params = {"name": name}
    return execute_query(connection, GET_ROLE_HISTORY_QUERY, **params)


async def get_role_history_async(connection: AsyncConnection, name: str) -> list[dict]:
    """Get the history of a role."""
    params = {"name": name}
    return await execute_query_async(connection, GET_ROLE_HISTORY_QUERY, **params)


def get_role_list(connection: Connection, timestamp: datetime | str | None = None) -> list[dict]:
    """Get a list of roles."""
    params = {"timestamp": normalize_timestamp(timestamp)}
    return execute_query(connection, GET_ROLE_LIST_QUERY, **params)


async def get_role_list_async(
    connection: AsyncConnection, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of roles."""
    params = {"timestamp": normalize_timestamp(timestamp)}
    return await execute_query_async(connection, GET_ROLE_LIST_QUERY, **params)


def update_role(
    connection: Connection,
    action_by: UUID,
    name: str,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a role."""
    params = {
        "action_by": action_by,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, UPDATE_ROLE_QUERY, **params)


async def update_role_async(
    connection: AsyncConnection,
    action_by: UUID,
    name: str,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a role."""
    params = {
        "action_by": action_by,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, UPDATE_ROLE_QUERY, **params)


def delete_role(
    connection: Connection, action_by: UUID, name: str, action_info: dict | None = None
) -> dict:
    """Delete a role."""
    params = {
        "action_by": action_by,
        "name": name,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, DELETE_ROLE_QUERY, **params)


async def delete_role_async(
    connection: AsyncConnection, action_by: UUID, name: str, action_info: dict | None = None
) -> dict:
    """Delete a role."""
    params = {
        "action_by": action_by,
        "name": name,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, DELETE_ROLE_QUERY, **params)
