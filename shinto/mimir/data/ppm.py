"""PPM management functions for Shinto Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.query_execution_handler import execute_query, execute_query_async

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import AsyncConnection, Connection


CREATE_PPM_QUERY = """
SELECT to_json(data.create_ppm(
    %(action_by)s::uuid, %(data)s::jsonb, %(project_id)s::uuid, %(action_info)s::jsonb
))
"""
GET_PPM_QUERY = """
SELECT to_json(data.get_ppm(
    %(action_by)s::uuid, %(ppm_id)s::uuid, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_PPM_BY_PROJECT_ID_QUERY = """
SELECT to_json(data.get_ppm_by_project_id(
    %(action_by)s::uuid, %(project_id)s::uuid, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_PPM_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_ppm_history(%(action_by)s::uuid, %(ppm_id)s::uuid) AS row"""
GET_PPM_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_ppm_list(%(action_by)s::uuid, %(timestamp)s::TIMESTAMPTZ) AS row"""
UPDATE_PPM_QUERY = """
SELECT to_json(data.update_ppm(
    %(action_by)s::uuid, %(ppm_id)s::uuid, %(data)s::jsonb, %(action_info)s::jsonb
))
"""
DELETE_PPM_QUERY = """
SELECT to_json(data.delete_ppm(
    %(action_by)s::uuid, %(ppm_id)s::uuid, %(action_info)s::jsonb
))
"""


def create_ppm(
    connection: Connection,
    action_by: UUID,
    data: dict,
    project_id: UUID,
    action_info: dict | None = None,
) -> dict:
    """Create a PPM."""
    params = {
        "action_by": action_by,
        "data": json.dumps(data) if data else None,
        "project_id": project_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, CREATE_PPM_QUERY, **params)


async def create_ppm_async(
    connection: AsyncConnection,
    action_by: UUID,
    data: dict,
    project_id: UUID,
    action_info: dict | None = None,
) -> dict:
    """Create a PPM."""
    params = {
        "action_by": action_by,
        "data": json.dumps(data) if data else None,
        "project_id": project_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, CREATE_PPM_QUERY, **params)


def get_ppm(
    connection: Connection,
    action_by: UUID,
    ppm_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a PPM by ID."""
    params = {
        "action_by": action_by,
        "ppm_id": ppm_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_PPM_QUERY, **params)


async def get_ppm_async(
    connection: AsyncConnection,
    action_by: UUID,
    ppm_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a PPM by ID."""
    params = {
        "action_by": action_by,
        "ppm_id": ppm_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_PPM_QUERY, **params)


def get_ppm_by_project_id(
    connection: Connection,
    action_by: UUID,
    project_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a PPM by project ID."""
    params = {
        "action_by": action_by,
        "project_id": project_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_PPM_BY_PROJECT_ID_QUERY, **params)


async def get_ppm_by_project_id_async(
    connection: AsyncConnection,
    action_by: UUID,
    project_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a PPM by project ID."""
    params = {
        "action_by": action_by,
        "project_id": project_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_PPM_BY_PROJECT_ID_QUERY, **params)


def get_ppm_history(connection: Connection, action_by: UUID, ppm_id: UUID) -> list[dict]:
    """Get the history of a PPM."""
    params = {"action_by": action_by, "ppm_id": ppm_id}
    return execute_query(connection, GET_PPM_HISTORY_QUERY, **params)


async def get_ppm_history_async(
    connection: AsyncConnection, action_by: UUID, ppm_id: UUID
) -> list[dict]:
    """Get the history of a PPM."""
    params = {"action_by": action_by, "ppm_id": ppm_id}
    return await execute_query_async(connection, GET_PPM_HISTORY_QUERY, **params)


def get_ppm_list(
    connection: Connection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of PPMs."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return execute_query(connection, GET_PPM_LIST_QUERY, **params)


async def get_ppm_list_async(
    connection: AsyncConnection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of PPMs."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return await execute_query_async(connection, GET_PPM_LIST_QUERY, **params)


def update_ppm(
    connection: Connection,
    action_by: UUID,
    ppm_id: UUID,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a PPM."""
    params = {
        "action_by": action_by,
        "ppm_id": ppm_id,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, UPDATE_PPM_QUERY, **params)


async def update_ppm_async(
    connection: AsyncConnection,
    action_by: UUID,
    ppm_id: UUID,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a PPM."""
    params = {
        "action_by": action_by,
        "ppm_id": ppm_id,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, UPDATE_PPM_QUERY, **params)


def delete_ppm(
    connection: Connection, action_by: UUID, ppm_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a PPM."""
    params = {
        "action_by": action_by,
        "ppm_id": ppm_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, DELETE_PPM_QUERY, **params)


async def delete_ppm_async(
    connection: AsyncConnection, action_by: UUID, ppm_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a PPM."""
    params = {
        "action_by": action_by,
        "ppm_id": ppm_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, DELETE_PPM_QUERY, **params)
