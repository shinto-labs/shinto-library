"""User pending management functions for Shinto Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.query_execution_handler import execute_query, execute_query_async

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import AsyncConnection, Connection


CREATE_USER_PENDING_QUERY = """SELECT to_json(base.create_user_pending(
    %(action_by)s::uuid,
    %(email)s::text,
    %(expires)s::TIMESTAMPTZ,
    %(data)s::jsonb,
    %(roles)s::text[],
    %(action_info)s::jsonb,
    %(verified)s::boolean
))"""
GET_USER_PENDING_QUERY = """
SELECT to_json(base.get_user_pending(
    %(action_by)s::uuid, %(user_pending_id)s::uuid, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_USER_PENDING_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM base.get_user_pending_history(%(action_by)s::uuid, %(user_pending_id)s::uuid) AS row"""
GET_USER_PENDING_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM base.get_user_pending_list(%(action_by)s::uuid, %(timestamp)s::TIMESTAMPTZ) AS row"""
UPDATE_USER_PENDING_QUERY = """SELECT to_json(base.update_user_pending(
    %(action_by)s::uuid,
    %(user_pending_id)s::uuid,
    %(email)s::text,
    %(expires)s::TIMESTAMPTZ,
    %(data)s::jsonb,
    %(roles)s::text[],
    %(action_info)s::jsonb,
    %(verified)s::boolean
))"""
DELETE_USER_PENDING_QUERY = """SELECT to_json(base.delete_user_pending(
%(action_by)s::uuid, %(user_pending_id)s::uuid, %(user_id)s::uuid, %(action_info)s::jsonb
))"""


def create_user_pending(
    connection: Connection,
    action_by: UUID,
    email: str,
    expires: datetime | str,
    data: dict | None = None,
    roles: list[str] | None = None,
    action_info: dict | None = None,
    verified: bool = False,
) -> dict:
    """Create a pending user."""
    params = {
        "action_by": action_by,
        "email": email,
        "expires": normalize_timestamp(expires),
        "data": json.dumps(data) if data else None,
        "roles": roles or [],
        "action_info": json.dumps(action_info) if action_info else None,
        "verified": verified,
    }
    return execute_query(connection, CREATE_USER_PENDING_QUERY, **params)


async def create_user_pending_async(
    connection: AsyncConnection,
    action_by: UUID,
    email: str,
    expires: datetime | str,
    data: dict | None = None,
    roles: list[str] | None = None,
    action_info: dict | None = None,
    verified: bool = False,
) -> dict:
    """Create a pending user."""
    params = {
        "action_by": action_by,
        "email": email,
        "expires": normalize_timestamp(expires),
        "data": json.dumps(data) if data else None,
        "roles": roles or [],
        "action_info": json.dumps(action_info) if action_info else None,
        "verified": verified,
    }
    return await execute_query_async(connection, CREATE_USER_PENDING_QUERY, **params)


def get_user_pending(
    connection: Connection,
    action_by: UUID,
    user_pending_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a pending user by ID."""
    params = {
        "action_by": action_by,
        "user_pending_id": user_pending_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_USER_PENDING_QUERY, **params)


async def get_user_pending_async(
    connection: AsyncConnection,
    action_by: UUID,
    user_pending_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a pending user by ID."""
    params = {
        "action_by": action_by,
        "user_pending_id": user_pending_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_USER_PENDING_QUERY, **params)


def get_user_pending_history(
    connection: Connection, action_by: UUID, user_pending_id: UUID
) -> list[dict]:
    """Get the history of a pending user."""
    params = {"action_by": action_by, "user_pending_id": user_pending_id}
    return execute_query(connection, GET_USER_PENDING_HISTORY_QUERY, **params)


async def get_user_pending_history_async(
    connection: AsyncConnection, action_by: UUID, user_pending_id: UUID
) -> list[dict]:
    """Get the history of a pending user."""
    params = {"action_by": action_by, "user_pending_id": user_pending_id}
    return await execute_query_async(connection, GET_USER_PENDING_HISTORY_QUERY, **params)


def get_user_pending_list(
    connection: Connection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of pending users."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return execute_query(connection, GET_USER_PENDING_LIST_QUERY, **params)


async def get_user_pending_list_async(
    connection: AsyncConnection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of pending users."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return await execute_query_async(connection, GET_USER_PENDING_LIST_QUERY, **params)


def update_user_pending(
    connection: Connection,
    action_by: UUID,
    user_pending_id: UUID,
    email: str | None = None,
    expires: datetime | str | None = None,
    data: dict | None = None,
    roles: list[str] | None = None,
    action_info: dict | None = None,
    verified: bool | None = None,
) -> dict:
    """Update a pending user."""
    params = {
        "action_by": action_by,
        "user_pending_id": user_pending_id,
        "email": email,
        "expires": normalize_timestamp(expires) if expires else None,
        "data": json.dumps(data) if data else None,
        "roles": roles,
        "action_info": json.dumps(action_info) if action_info else None,
        "verified": verified,
    }
    return execute_query(connection, UPDATE_USER_PENDING_QUERY, **params)


async def update_user_pending_async(
    connection: AsyncConnection,
    action_by: UUID,
    user_pending_id: UUID,
    email: str | None = None,
    expires: datetime | str | None = None,
    data: dict | None = None,
    roles: list[str] | None = None,
    action_info: dict | None = None,
    verified: bool | None = None,
) -> dict:
    """Update a pending user."""
    params = {
        "action_by": action_by,
        "user_pending_id": user_pending_id,
        "email": email,
        "expires": normalize_timestamp(expires) if expires else None,
        "data": json.dumps(data) if data else None,
        "roles": roles,
        "action_info": json.dumps(action_info) if action_info else None,
        "verified": verified,
    }
    return await execute_query_async(connection, UPDATE_USER_PENDING_QUERY, **params)


def delete_user_pending(
    connection: Connection,
    action_by: UUID,
    user_pending_id: UUID,
    user_id: UUID,
    action_info: dict | None = None,
) -> dict:
    """Delete a pending user."""
    params = {
        "action_by": action_by,
        "user_pending_id": user_pending_id,
        "user_id": user_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, DELETE_USER_PENDING_QUERY, **params)


async def delete_user_pending_async(
    connection: AsyncConnection,
    action_by: UUID,
    user_pending_id: UUID,
    user_id: UUID,
    action_info: dict | None = None,
) -> dict:
    """Delete a pending user."""
    params = {
        "action_by": action_by,
        "user_pending_id": user_pending_id,
        "user_id": user_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, DELETE_USER_PENDING_QUERY, **params)
