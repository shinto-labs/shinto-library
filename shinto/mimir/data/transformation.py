"""Module for managing transformations in the Mimir data catalog."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.query_execution_handler import execute_query, execute_query_async

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import AsyncConnection, Connection


GET_TRANSFORMATION_QUERY = """
SELECT to_json(data.get_transformation(
    %(action_by)s::uuid, %(transformation_id)s::uuid, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_TRANSFORMATION_BY_NAME_QUERY = """
SELECT to_json(data.get_transformation_by_name(
    %(action_by)s::uuid, %(transformation_name)s::text, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_TRANSFORMATION_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_transformation_history(%(action_by)s::uuid, %(transformation_id)s::uuid) AS row"""
GET_TRANSFORMATION_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_transformation_list(%(action_by)s::uuid, %(timestamp)s::TIMESTAMPTZ) AS row"""
CREATE_TRANSFORMATION_QUERY = """
SELECT to_json(data.create_transformation(
    %(action_by)s::uuid, %(name)s::text, %(data)s::jsonb, %(action_info)s::jsonb
))
"""
UPDATE_TRANSFORMATION_QUERY = """
SELECT to_json(data.update_transformation(
    %(action_by)s::uuid,
    %(transformation_id)s::uuid,
    %(name)s::text,
    %(data)s::jsonb,
    %(action_info)s::jsonb
))
"""
DELETE_TRANSFORMATION_QUERY = """
SELECT to_json(data.delete_transformation(
    %(action_by)s::uuid, %(transformation_id)s::uuid, %(action_info)s::jsonb
))
"""


def get_transformation_by_id(
    connection: Connection,
    action_by: UUID,
    transformation_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a transformation by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "transformation_id": transformation_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_TRANSFORMATION_QUERY, **params)


async def get_transformation_by_id_async(
    connection: AsyncConnection,
    action_by: UUID,
    transformation_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a transformation by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "transformation_id": transformation_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_TRANSFORMATION_QUERY, **params)


def get_transformation_by_name(
    connection: Connection,
    action_by: UUID,
    transformation_name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a transformation by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "transformation_name": transformation_name,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_TRANSFORMATION_BY_NAME_QUERY, **params)


async def get_transformation_by_name_async(
    connection: AsyncConnection,
    action_by: UUID,
    transformation_name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a transformation by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "transformation_name": transformation_name,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_TRANSFORMATION_BY_NAME_QUERY, **params)


def get_transformation_history(
    connection: Connection, action_by: UUID, transformation_id: UUID
) -> list[dict]:
    """Get the history of a transformation."""
    params = {"action_by": action_by, "transformation_id": transformation_id}
    return execute_query(connection, GET_TRANSFORMATION_HISTORY_QUERY, **params)


async def get_transformation_history_async(
    connection: AsyncConnection, action_by: UUID, transformation_id: UUID
) -> list[dict]:
    """Get the history of a transformation."""
    params = {"action_by": action_by, "transformation_id": transformation_id}
    return await execute_query_async(connection, GET_TRANSFORMATION_HISTORY_QUERY, **params)


def get_transformation_list(
    connection: Connection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return execute_query(connection, GET_TRANSFORMATION_LIST_QUERY, **params)


async def get_transformation_list_async(
    connection: AsyncConnection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return await execute_query_async(connection, GET_TRANSFORMATION_LIST_QUERY, **params)


def create_transformation(
    connection: Connection, action_by: UUID, name: str, data: dict, action_info: dict | None = None
) -> dict:
    """Create a transformation."""
    params = {
        "action_by": action_by,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, CREATE_TRANSFORMATION_QUERY, **params)


async def create_transformation_async(
    connection: AsyncConnection,
    action_by: UUID,
    name: str,
    data: dict,
    action_info: dict | None = None,
) -> dict:
    """Create a transformation."""
    params = {
        "action_by": action_by,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, CREATE_TRANSFORMATION_QUERY, **params)


def update_transformation(
    connection: Connection,
    action_by: UUID,
    transformation_id: UUID,
    name: str | None = None,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a transformation. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "transformation_id": transformation_id,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, UPDATE_TRANSFORMATION_QUERY, **params)


async def update_transformation_async(
    connection: AsyncConnection,
    action_by: UUID,
    transformation_id: UUID,
    name: str | None = None,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a transformation. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "transformation_id": transformation_id,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, UPDATE_TRANSFORMATION_QUERY, **params)


def delete_transformation(
    connection: Connection,
    action_by: UUID,
    transformation_id: UUID,
    action_info: dict | None = None,
) -> dict:
    """Delete a transformation. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "transformation_id": transformation_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, DELETE_TRANSFORMATION_QUERY, **params)


async def delete_transformation_async(
    connection: AsyncConnection,
    action_by: UUID,
    transformation_id: UUID,
    action_info: dict | None = None,
) -> dict:
    """Delete a transformation. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "transformation_id": transformation_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, DELETE_TRANSFORMATION_QUERY, **params)
