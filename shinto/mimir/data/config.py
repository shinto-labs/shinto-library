"""Module for managing configs in Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.query_execution_handler import execute_query, execute_query_async

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import AsyncConnection, Connection


GET_CONFIG_QUERY = """
SELECT to_json(data.get_config(
    %(action_by)s, %(config_id)s::uuid, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_CONFIG_BY_NAME_QUERY = """
SELECT to_json(data.get_config_by_name(
    %(action_by)s::uuid, %(config_name)s::text, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_CONFIG_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_config_history(%(action_by)s::uuid, %(config_id)s::uuid) AS row"""
GET_CONFIG_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_config_list(%(action_by)s::uuid, %(timestamp)s::TIMESTAMPTZ) AS row"""
CREATE_CONFIG_QUERY = """
SELECT to_json(data.create_config(
    %(action_by)s::uuid, %(name)s::text, %(data)s::jsonb, %(action_info)s::jsonb
))
"""
UPDATE_CONFIG_QUERY = """
SELECT to_json(data.update_config(
    %(action_by)s::uuid,
    %(config_id)s::uuid,
    %(name)s::text,
    %(data)s::jsonb,
    %(action_info)s::jsonb
))
"""
DELETE_CONFIG_QUERY = """
SELECT to_json(data.delete_config(
    (%(action_by)s::uuid, %(config_id)s::uuid, %(action_info)s::jsonb)
))
"""
CONFIG_EXISTS_QUERY = "SELECT data.config_exists(%(config_id)s::uuid, %(timestamp)s::TIMESTAMPTZ)"


def get_config_by_id(
    connection: Connection,
    action_by: UUID,
    config_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a config by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "config_id": config_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_CONFIG_QUERY, **params)


async def get_config_by_id_async(
    connection: AsyncConnection,
    action_by: UUID,
    config_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a config by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "config_id": config_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_CONFIG_QUERY, **params)


def get_config_by_name(
    connection: Connection,
    action_by: UUID,
    config_name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a config by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "config_name": config_name,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_CONFIG_BY_NAME_QUERY, **params)


async def get_config_by_name_async(
    connection: AsyncConnection,
    action_by: UUID,
    config_name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a config by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "config_name": config_name,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_CONFIG_BY_NAME_QUERY, **params)


def get_config_history(connection: Connection, action_by: UUID, config_id: UUID) -> list[dict]:
    """Get the history of a config."""
    params = {"action_by": action_by, "config_id": config_id}
    return execute_query(connection, GET_CONFIG_HISTORY_QUERY, **params)


async def get_config_history_async(
    connection: AsyncConnection, action_by: UUID, config_id: UUID
) -> list[dict]:
    """Get the history of a config."""
    params = {"action_by": action_by, "config_id": config_id}
    return await execute_query_async(connection, GET_CONFIG_HISTORY_QUERY, **params)


def get_config_list(
    connection: Connection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of configs. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return execute_query(connection, GET_CONFIG_LIST_QUERY, **params)


async def get_config_list_async(
    connection: AsyncConnection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of configs. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return await execute_query_async(connection, GET_CONFIG_LIST_QUERY, **params)


def create_config(
    connection: Connection, action_by: UUID, name: str, data: dict, action_info: dict | None = None
) -> dict:
    """Create a config."""
    params = {
        "action_by": action_by,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, CREATE_CONFIG_QUERY, **params)


async def create_config_async(
    connection: AsyncConnection,
    action_by: UUID,
    name: str,
    data: dict,
    action_info: dict | None = None,
) -> dict:
    """Create a config."""
    params = {
        "action_by": action_by,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, CREATE_CONFIG_QUERY, **params)


def update_config(
    connection: Connection,
    action_by: UUID,
    config_id: UUID,
    name: str | None = None,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a config. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "config_id": config_id,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, UPDATE_CONFIG_QUERY, **params)


async def update_config_async(
    connection: AsyncConnection,
    action_by: UUID,
    config_id: UUID,
    name: str | None = None,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a config. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "config_id": config_id,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, UPDATE_CONFIG_QUERY, **params)


def delete_config(
    connection: Connection, action_by: UUID, config_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a config. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "config_id": config_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, DELETE_CONFIG_QUERY, **params)


async def delete_config_async(
    connection: AsyncConnection, action_by: UUID, config_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a config. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "config_id": config_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, DELETE_CONFIG_QUERY, **params)


def config_exists(
    connection: Connection, config_id: UUID, timestamp: datetime | str | None = None
) -> bool:
    """Check if a config exists at a given timestamp."""
    params = {"config_id": config_id, "timestamp": normalize_timestamp(timestamp)}
    return execute_query(connection, CONFIG_EXISTS_QUERY, **params)


async def config_exists_async(
    connection: AsyncConnection, config_id: UUID, timestamp: datetime | str | None = None
) -> bool:
    """Check if a config exists at a given timestamp."""
    params = {"config_id": config_id, "timestamp": normalize_timestamp(timestamp)}
    return await execute_query_async(connection, CONFIG_EXISTS_QUERY, **params)
