"""Marker management functions for Shinto Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.query_execution_handler import execute_query, execute_query_async

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import AsyncConnection, Connection


GET_MARKER_BY_ID_QUERY = """SELECT to_json(data.get_marker(
    %(action_by)s::uuid,
    %(marker_id)s::uuid,
    %(timestamp)s::TIMESTAMPTZ
))"""
GET_MARKER_BY_NAME_QUERY = """SELECT to_json(data.get_marker_by_name(
    %(action_by)s::uuid,
    %(marker_name)s::text,
    %(timestamp)s::TIMESTAMPTZ
))"""
GET_MARKER_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_marker_history(%(action_by)s::uuid, %(marker_id)s::uuid) AS row"""
GET_MARKER_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_marker_list(%(action_by)s::uuid, %(timestamp)s::TIMESTAMPTZ) AS row"""
CREATE_MARKER_QUERY = """SELECT to_json(data.create_marker(
    %(action_by)s::uuid,
    %(name)s::text,
    %(marked_timestamp)s::timestamptz,
    %(action_info)s::jsonb
))"""
UPDATE_MARKER_QUERY = """SELECT to_json(data.update_marker(
    %(action_by)s::uuid,
    %(marker_id)s::uuid,
    %(name)s::text,
    %(marked_timestamp)s::timestamptz,
    %(action_info)s::jsonb
))"""
DELETE_MARKER_QUERY = """SELECT to_json(data.delete_marker(
    %(action_by)s::uuid,
    %(marker_id)s::uuid,
    %(action_info)s::jsonb
))"""


def get_marker_by_id(
    connection: Connection,
    action_by: UUID,
    marker_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a marker by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "marker_id": marker_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_MARKER_BY_ID_QUERY, **params)


async def get_marker_by_id_async(
    connection: AsyncConnection,
    action_by: UUID,
    marker_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a marker by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "marker_id": marker_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_MARKER_BY_ID_QUERY, **params)


def get_marker_by_name(
    connection: Connection,
    action_by: UUID,
    marker_name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a marker by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "marker_name": marker_name,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_MARKER_BY_NAME_QUERY, **params)


async def get_marker_by_name_async(
    connection: AsyncConnection,
    action_by: UUID,
    marker_name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a marker by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "marker_name": marker_name,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_MARKER_BY_NAME_QUERY, **params)


def get_marker_history(connection: Connection, action_by: UUID, marker_id: UUID) -> list[dict]:
    """Get the history of a marker."""
    params = {
        "action_by": action_by,
        "marker_id": marker_id,
    }
    return execute_query(connection, GET_MARKER_HISTORY_QUERY, **params)


async def get_marker_history_async(
    connection: AsyncConnection, action_by: UUID, marker_id: UUID
) -> list[dict]:
    """Get the history of a marker."""
    params = {
        "action_by": action_by,
        "marker_id": marker_id,
    }
    return await execute_query_async(connection, GET_MARKER_HISTORY_QUERY, **params)


def get_marker_list(
    connection: Connection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of markers. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_MARKER_LIST_QUERY, **params)


async def get_marker_list_async(
    connection: AsyncConnection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of markers. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_MARKER_LIST_QUERY, **params)


def create_marker(
    connection: Connection,
    action_by: UUID,
    name: str,
    marked_timestamp: datetime | str | None = None,
    action_info: dict | None = None,
) -> dict:
    """Create a marker."""
    params = {
        "action_by": action_by,
        "name": name,
        "marked_timestamp": normalize_timestamp(marked_timestamp),
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, CREATE_MARKER_QUERY, **params)


async def create_marker_async(
    connection: AsyncConnection,
    action_by: UUID,
    name: str,
    marked_timestamp: datetime | str | None = None,
    action_info: dict | None = None,
) -> dict:
    """Create a marker."""
    params = {
        "action_by": action_by,
        "name": name,
        "marked_timestamp": normalize_timestamp(marked_timestamp),
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, CREATE_MARKER_QUERY, **params)


def update_marker(
    connection: Connection,
    action_by: UUID,
    marker_id: UUID,
    name: str | None = None,
    marked_timestamp: datetime | str | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a marker. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "marker_id": marker_id,
        "name": name,
        "marked_timestamp": normalize_timestamp(marked_timestamp),
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, UPDATE_MARKER_QUERY, **params)


async def update_marker_async(
    connection: AsyncConnection,
    action_by: UUID,
    marker_id: UUID,
    name: str | None = None,
    marked_timestamp: datetime | str | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a marker. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "marker_id": marker_id,
        "name": name,
        "marked_timestamp": normalize_timestamp(marked_timestamp),
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, UPDATE_MARKER_QUERY, **params)


def delete_marker(
    connection: Connection, action_by: UUID, marker_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a marker. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "marker_id": marker_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, DELETE_MARKER_QUERY, **params)


async def delete_marker_async(
    connection: AsyncConnection, action_by: UUID, marker_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a marker. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "marker_id": marker_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, DELETE_MARKER_QUERY, **params)
