"""Taxonomy management functions for Shinto Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.query_execution_handler import execute_query, execute_query_async

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import AsyncConnection, Connection

GET_TAXONOMY_QUERY = """
SELECT to_json(data.get_taxonomy(
    %(action_by)s::uuid, %(taxonomy_id)s::uuid, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_TAXONOMY_BY_NAME_QUERY = """
SELECT to_json(data.get_taxonomy_by_name(
    %(action_by)s::uuid, %(taxonomy_name)s::text, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_TAXONOMY_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_taxonomy_history(%(action_by)s::uuid, %(taxonomy_id)s::uuid) AS row"""
GET_TAXONOMY_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_taxonomy_list(%(action_by)s::uuid, %(timestamp)s::TIMESTAMPTZ) AS row"""
CREATE_TAXONOMY_QUERY = """
SELECT to_json(data.create_taxonomy(
    %(action_by)s::uuid, %(name)s::text, %(data)s::jsonb, %(action_info)s::jsonb
))
"""
UPDATE_TAXONOMY_QUERY = """
SELECT to_json(data.update_taxonomy(
    %(action_by)s::uuid,
    %(taxonomy_id)s::uuid,
    %(name)s::text,
    %(data)s::jsonb,
    %(action_info)s::jsonb
))
"""
DELETE_TAXONOMY_QUERY = """
SELECT to_json(data.delete_taxonomy(
    %(action_by)s::uuid, %(taxonomy_id)s::uuid, %(action_info)s::jsonb
))
"""


def get_taxonomy_by_id(
    connection: Connection,
    action_by: UUID,
    taxonomy_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a taxonomy by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "taxonomy_id": taxonomy_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_TAXONOMY_QUERY, **params)


async def get_taxonomy_by_id_async(
    connection: AsyncConnection,
    action_by: UUID,
    taxonomy_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a taxonomy by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "taxonomy_id": taxonomy_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_TAXONOMY_QUERY, **params)


def get_taxonomy_by_name(
    connection: Connection,
    action_by: UUID,
    taxonomy_name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a taxonomy by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "taxonomy_name": taxonomy_name,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_TAXONOMY_BY_NAME_QUERY, **params)


async def get_taxonomy_by_name_async(
    connection: AsyncConnection,
    action_by: UUID,
    taxonomy_name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a taxonomy by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "taxonomy_name": taxonomy_name,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_TAXONOMY_BY_NAME_QUERY, **params)


def get_taxonomy_history(connection: Connection, action_by: UUID, taxonomy_id: UUID) -> list[dict]:
    """Get the history of a taxonomy."""
    params = {"action_by": action_by, "taxonomy_id": taxonomy_id}
    return execute_query(connection, GET_TAXONOMY_HISTORY_QUERY, **params)


async def get_taxonomy_history_async(
    connection: AsyncConnection, action_by: UUID, taxonomy_id: UUID
) -> list[dict]:
    """Get the history of a taxonomy."""
    params = {"action_by": action_by, "taxonomy_id": taxonomy_id}
    return await execute_query_async(connection, GET_TAXONOMY_HISTORY_QUERY, **params)


def get_taxonomy_list(
    connection: Connection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of taxonomies. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return execute_query(connection, GET_TAXONOMY_LIST_QUERY, **params)


async def get_taxonomy_list_async(
    connection: AsyncConnection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of taxonomies. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return await execute_query_async(connection, GET_TAXONOMY_LIST_QUERY, **params)


def create_taxonomy(
    connection: Connection,
    action_by: UUID,
    name: str,
    data: dict | None,
    action_info: dict | None = None,
) -> dict:
    """Create a taxonomy."""
    params = {
        "action_by": action_by,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, CREATE_TAXONOMY_QUERY, **params)


async def create_taxonomy_async(
    connection: AsyncConnection,
    action_by: UUID,
    name: str,
    data: dict | None,
    action_info: dict | None = None,
) -> dict:
    """Create a taxonomy."""
    params = {
        "action_by": action_by,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, CREATE_TAXONOMY_QUERY, **params)


def update_taxonomy(
    connection: Connection,
    action_by: UUID,
    taxonomy_id: UUID,
    name: str | None = None,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a taxonomy. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "taxonomy_id": taxonomy_id,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, UPDATE_TAXONOMY_QUERY, **params)


async def update_taxonomy_async(
    connection: AsyncConnection,
    action_by: UUID,
    taxonomy_id: UUID,
    name: str | None = None,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a taxonomy. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "taxonomy_id": taxonomy_id,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, UPDATE_TAXONOMY_QUERY, **params)


def delete_taxonomy(
    connection: Connection, action_by: UUID, taxonomy_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a taxonomy. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "taxonomy_id": taxonomy_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, DELETE_TAXONOMY_QUERY, **params)


async def delete_taxonomy_async(
    connection: AsyncConnection, action_by: UUID, taxonomy_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a taxonomy. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "taxonomy_id": taxonomy_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, DELETE_TAXONOMY_QUERY, **params)
