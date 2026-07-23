"""File management functions for Shinto Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.query_execution_handler import execute_query, execute_query_async

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import AsyncConnection, Connection


CREATE_FILE_QUERY = """
SELECT to_json(data.create_file(
    %(action_by)s::uuid, %(project_id)s::uuid, %(data)s::jsonb, %(action_info)s::jsonb
))
"""
GET_FILE_QUERY = """
SELECT to_json(data.get_file(
    %(action_by)s::uuid, %(file_id)s::uuid, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_FILE_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_file_history(%(action_by)s::uuid, %(file_id)s::uuid) AS row"""
GET_FILE_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_file_list(%(action_by)s::uuid, %(timestamp)s::TIMESTAMPTZ) AS row"""
DELETE_FILE_QUERY = """
SELECT to_json(data.delete_file(
    %(action_by)s::uuid, %(file_id)s::uuid, %(action_info)s::jsonb
))
"""


def create_file(
    connection: Connection,
    action_by: UUID,
    project_id: UUID,
    data: dict,
    action_info: dict | None = None,
) -> dict:
    """Create a file."""
    params = {
        "action_by": action_by,
        "project_id": project_id,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, CREATE_FILE_QUERY, **params)


async def create_file_async(
    connection: AsyncConnection,
    action_by: UUID,
    project_id: UUID,
    data: dict,
    action_info: dict | None = None,
) -> dict:
    """Create a file."""
    params = {
        "action_by": action_by,
        "project_id": project_id,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, CREATE_FILE_QUERY, **params)


def get_file(
    connection: Connection,
    action_by: UUID,
    file_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a file by ID."""
    params = {
        "action_by": action_by,
        "file_id": file_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_FILE_QUERY, **params)


async def get_file_async(
    connection: AsyncConnection,
    action_by: UUID,
    file_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a file by ID."""
    params = {
        "action_by": action_by,
        "file_id": file_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_FILE_QUERY, **params)


def get_file_history(connection: Connection, action_by: UUID, file_id: UUID) -> list[dict]:
    """Get the history of a file."""
    params = {"action_by": action_by, "file_id": file_id}
    return execute_query(connection, GET_FILE_HISTORY_QUERY, **params)


async def get_file_history_async(
    connection: AsyncConnection, action_by: UUID, file_id: UUID
) -> list[dict]:
    """Get the history of a file."""
    params = {"action_by": action_by, "file_id": file_id}
    return await execute_query_async(connection, GET_FILE_HISTORY_QUERY, **params)


def get_file_list(
    connection: Connection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of files."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return execute_query(connection, GET_FILE_LIST_QUERY, **params)


async def get_file_list_async(
    connection: AsyncConnection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of files."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return await execute_query_async(connection, GET_FILE_LIST_QUERY, **params)


def delete_file(
    connection: Connection, action_by: UUID, file_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a file."""
    params = {
        "action_by": action_by,
        "file_id": file_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, DELETE_FILE_QUERY, **params)


async def delete_file_async(
    connection: AsyncConnection, action_by: UUID, file_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a file."""
    params = {
        "action_by": action_by,
        "file_id": file_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, DELETE_FILE_QUERY, **params)
