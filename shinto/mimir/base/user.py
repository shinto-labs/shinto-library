"""User management functions for Shinto Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.query_execution_handler import execute_query, execute_query_async

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import AsyncConnection, Connection


GET_USER_QUERY = """
SELECT to_json(base.get_user(
    %(action_by)s::uuid, %(user_id)s::uuid, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_USER_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM base.get_user_history(%(action_by)s::uuid, %(user_id)s::uuid) AS row"""
GET_USER_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM base.get_user_list(%(action_by)s::uuid, %(timestamp)s::TIMESTAMPTZ) AS row"""
CREATE_USER_QUERY = """SELECT to_json(base.create_user(
    %(action_by)s::uuid,
    %(username)s::text,
    %(data)s::jsonb,
    %(roles)s::text[],
    %(password_hash)s::text,
    %(verified)s::boolean,
    %(action_info)s::jsonb
))"""
UPDATE_USER_QUERY = """SELECT to_json(base.update_user(
    %(action_by)s::uuid,
    %(user_id)s::uuid,
    %(data)s::jsonb,
    %(roles)s::text[],
    %(password_hash)s::text,
    %(verified)s::boolean,
    %(action_info)s::jsonb,
    %(force_update)s::boolean
))"""
DELETE_USER_QUERY = """
SELECT to_json(base.delete_user(
    %(action_by)s::uuid, %(user_id)s::uuid, %(action_info)s::jsonb
))
"""
AUTHENTICATE_USER_QUERY = """
SELECT to_json(base.authenticate_user(
    %(username)s::text, %(password_hash)s::text
))
"""


def get_user(
    connection: Connection,
    action_by: UUID,
    user_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a user by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "user_id": user_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_USER_QUERY, **params)


async def get_user_async(
    connection: AsyncConnection,
    action_by: UUID,
    user_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a user by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "user_id": user_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_USER_QUERY, **params)


def get_user_history(connection: Connection, action_by: UUID, user_id: UUID) -> list[dict]:
    """Get the history of a user."""
    params = {"action_by": action_by, "user_id": user_id}
    return execute_query(connection, GET_USER_HISTORY_QUERY, **params)


async def get_user_history_async(
    connection: AsyncConnection, action_by: UUID, user_id: UUID
) -> list[dict]:
    """Get the history of a user."""
    params = {"action_by": action_by, "user_id": user_id}
    return await execute_query_async(connection, GET_USER_HISTORY_QUERY, **params)


def get_user_list(
    connection: Connection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return execute_query(connection, GET_USER_LIST_QUERY, **params)


async def get_user_list_async(
    connection: AsyncConnection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return await execute_query_async(connection, GET_USER_LIST_QUERY, **params)


def create_user(
    connection: Connection,
    action_by: UUID,
    username: str,
    data: dict | None = None,
    roles: list[str] | None = None,
    password_hash: str | None = None,
    verified: bool = False,
    action_info: dict | None = None,
) -> dict:
    """Create a user."""
    params = {
        "action_by": action_by,
        "username": username,
        "data": json.dumps(data) if data else None,
        "roles": roles,
        "password_hash": password_hash,
        "verified": verified,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, CREATE_USER_QUERY, **params)


async def create_user_async(
    connection: AsyncConnection,
    action_by: UUID,
    username: str,
    data: dict | None = None,
    roles: list[str] | None = None,
    password_hash: str | None = None,
    verified: bool = False,
    action_info: dict | None = None,
) -> dict:
    """Create a user."""
    params = {
        "action_by": action_by,
        "username": username,
        "data": json.dumps(data) if data else None,
        "roles": roles,
        "password_hash": password_hash,
        "verified": verified,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, CREATE_USER_QUERY, **params)


def update_user(
    connection: Connection,
    action_by: UUID,
    user_id: UUID,
    data: dict | None = None,
    roles: list[str] | None = None,
    password_hash: str | None = None,
    verified: bool | None = None,
    action_info: dict | None = None,
    force_update: bool = False,
) -> dict:
    """Update a user. NULL parameters preserve existing values."""
    params = {
        "action_by": action_by,
        "user_id": user_id,
        "data": json.dumps(data) if data else None,
        "roles": roles,
        "password_hash": password_hash,
        "verified": verified,
        "action_info": json.dumps(action_info) if action_info else None,
        "force_update": force_update,
    }
    return execute_query(connection, UPDATE_USER_QUERY, **params)


async def update_user_async(
    connection: AsyncConnection,
    action_by: UUID,
    user_id: UUID,
    data: dict | None = None,
    roles: list[str] | None = None,
    password_hash: str | None = None,
    verified: bool | None = None,
    action_info: dict | None = None,
    force_update: bool = False,
) -> dict:
    """Update a user. NULL parameters preserve existing values."""
    params = {
        "action_by": action_by,
        "user_id": user_id,
        "data": json.dumps(data) if data else None,
        "roles": roles,
        "password_hash": password_hash,
        "verified": verified,
        "action_info": json.dumps(action_info) if action_info else None,
        "force_update": force_update,
    }
    return await execute_query_async(connection, UPDATE_USER_QUERY, **params)


def delete_user(
    connection: Connection, action_by: UUID, user_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a user."""
    params = {
        "action_by": action_by,
        "user_id": user_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, DELETE_USER_QUERY, **params)


async def delete_user_async(
    connection: AsyncConnection, action_by: UUID, user_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a user."""
    params = {
        "action_by": action_by,
        "user_id": user_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, DELETE_USER_QUERY, **params)


def authenticate_user(connection: Connection, username: str, password_hash: str) -> dict:
    """Authenticate a user by username and password hash."""
    params = {"username": username, "password_hash": password_hash}
    return execute_query(connection, AUTHENTICATE_USER_QUERY, **params)


async def authenticate_user_async(
    connection: AsyncConnection, username: str, password_hash: str
) -> dict:
    """Authenticate a user by username and password hash."""
    params = {"username": username, "password_hash": password_hash}
    return await execute_query_async(connection, AUTHENTICATE_USER_QUERY, **params)
