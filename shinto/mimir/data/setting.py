"""Setting management functions for Shinto Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.query_execution_handler import execute_query, execute_query_async

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import AsyncConnection, Connection


CREATE_SETTING_QUERY = """SELECT to_json(data.create_setting(
    %(action_by)s::uuid,
    %(setting_type)s::base.setting_type,
    %(name)s::text,
    %(project_id)s::uuid,
    %(data)s::jsonb,
    %(action_info)s::jsonb
))"""
GET_SETTING_QUERY = """
SELECT to_json(data.get_setting(
    %(action_by)s::uuid, %(setting_id)s::uuid, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_SETTING_BY_NAME_QUERY = """
SELECT to_json(data.get_setting_by_name(
    %(action_by)s::uuid, %(name)s::text, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_SETTING_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_setting_history(%(action_by)s::uuid, %(setting_id)s::uuid) AS row"""
GET_SETTING_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_setting_list(%(action_by)s::uuid, %(timestamp)s::TIMESTAMPTZ) AS row"""
UPDATE_SETTING_QUERY = """
SELECT to_json(data.update_setting(
    %(action_by)s::uuid, %(setting_id)s::uuid, %(data)s::jsonb, %(action_info)s::jsonb
))
"""
DELETE_SETTING_QUERY = """
SELECT to_json(data.delete_setting(
    %(action_by)s::uuid, %(setting_id)s::uuid, %(action_info)s::jsonb
))
"""


def create_setting(
    connection: Connection,
    action_by: UUID,
    setting_type: str,
    name: str,
    project_id: UUID,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Create a setting."""
    params = {
        "action_by": action_by,
        "setting_type": setting_type,
        "name": name,
        "project_id": project_id,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, CREATE_SETTING_QUERY, **params)


async def create_setting_async(
    connection: AsyncConnection,
    action_by: UUID,
    setting_type: str,
    name: str,
    project_id: UUID,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Create a setting."""
    params = {
        "action_by": action_by,
        "setting_type": setting_type,
        "name": name,
        "project_id": project_id,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, CREATE_SETTING_QUERY, **params)


def get_setting(
    connection: Connection,
    action_by: UUID,
    setting_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a setting by ID."""
    params = {
        "action_by": action_by,
        "setting_id": setting_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_SETTING_QUERY, **params)


async def get_setting_async(
    connection: AsyncConnection,
    action_by: UUID,
    setting_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a setting by ID."""
    params = {
        "action_by": action_by,
        "setting_id": setting_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_SETTING_QUERY, **params)


def get_setting_by_name(
    connection: Connection,
    action_by: UUID,
    name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a setting by name."""
    params = {
        "action_by": action_by,
        "name": name,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_SETTING_BY_NAME_QUERY, **params)


async def get_setting_by_name_async(
    connection: AsyncConnection,
    action_by: UUID,
    name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a setting by name."""
    params = {
        "action_by": action_by,
        "name": name,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_SETTING_BY_NAME_QUERY, **params)


def get_setting_history(connection: Connection, action_by: UUID, setting_id: UUID) -> list[dict]:
    """Get the history of a setting."""
    params = {"action_by": action_by, "setting_id": setting_id}
    return execute_query(connection, GET_SETTING_HISTORY_QUERY, **params)


async def get_setting_history_async(
    connection: AsyncConnection, action_by: UUID, setting_id: UUID
) -> list[dict]:
    """Get the history of a setting."""
    params = {"action_by": action_by, "setting_id": setting_id}
    return await execute_query_async(connection, GET_SETTING_HISTORY_QUERY, **params)


def get_setting_list(
    connection: Connection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of settings."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return execute_query(connection, GET_SETTING_LIST_QUERY, **params)


async def get_setting_list_async(
    connection: AsyncConnection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of settings."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return await execute_query_async(connection, GET_SETTING_LIST_QUERY, **params)


def update_setting(
    connection: Connection,
    action_by: UUID,
    setting_id: UUID,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a setting."""
    params = {
        "action_by": action_by,
        "setting_id": setting_id,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, UPDATE_SETTING_QUERY, **params)


async def update_setting_async(
    connection: AsyncConnection,
    action_by: UUID,
    setting_id: UUID,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a setting."""
    params = {
        "action_by": action_by,
        "setting_id": setting_id,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, UPDATE_SETTING_QUERY, **params)


def delete_setting(
    connection: Connection, action_by: UUID, setting_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a setting."""
    params = {
        "action_by": action_by,
        "setting_id": setting_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, DELETE_SETTING_QUERY, **params)


async def delete_setting_async(
    connection: AsyncConnection, action_by: UUID, setting_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a setting."""
    params = {
        "action_by": action_by,
        "setting_id": setting_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, DELETE_SETTING_QUERY, **params)
