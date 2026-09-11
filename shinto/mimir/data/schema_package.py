"""Schema package management functions for Shinto Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.query_execution_handler import execute_query, execute_query_async

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import AsyncConnection, Connection

GET_SCHEMA_PACKAGE_QUERY = """
SELECT to_json(data.get_schema_package(
    %(action_by)s::uuid, %(schema_package_id)s::uuid, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_SCHEMA_PACKAGE_BY_NAME_QUERY = """
SELECT to_json(data.get_schema_package_by_name(
    %(action_by)s::uuid, %(schema_package_name)s::text, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_SCHEMA_PACKAGE_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_schema_package_history(%(action_by)s::uuid, %(schema_package_id)s::uuid) AS row"""
GET_SCHEMA_PACKAGE_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_schema_package_list(%(action_by)s::uuid, %(timestamp)s::TIMESTAMPTZ) AS row"""
CREATE_SCHEMA_PACKAGE_QUERY = """
SELECT to_json(data.create_schema_package(
    %(action_by)s::uuid, %(name)s::text, %(data)s::jsonb, %(action_info)s::jsonb
))
"""
UPDATE_SCHEMA_PACKAGE_QUERY = """
SELECT to_json(data.update_schema_package(
    %(action_by)s::uuid,
    %(schema_package_id)s::uuid,
    %(name)s::text,
    %(data)s::jsonb,
    %(action_info)s::jsonb
))
"""
DELETE_SCHEMA_PACKAGE_QUERY = """
SELECT to_json(data.delete_schema_package(
    %(action_by)s::uuid, %(schema_package_id)s::uuid, %(action_info)s::jsonb
))
"""


def get_schema_package_by_id(
    connection: Connection,
    action_by: UUID,
    schema_package_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a schema package by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "schema_package_id": schema_package_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_SCHEMA_PACKAGE_QUERY, **params)


async def get_schema_package_by_id_async(
    connection: AsyncConnection,
    action_by: UUID,
    schema_package_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a schema package by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "schema_package_id": schema_package_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_SCHEMA_PACKAGE_QUERY, **params)


def get_schema_package_by_name(
    connection: Connection,
    action_by: UUID,
    schema_package_name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a schema package by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "schema_package_name": schema_package_name,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_SCHEMA_PACKAGE_BY_NAME_QUERY, **params)


async def get_schema_package_by_name_async(
    connection: AsyncConnection,
    action_by: UUID,
    schema_package_name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a schema package by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "schema_package_name": schema_package_name,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_SCHEMA_PACKAGE_BY_NAME_QUERY, **params)


def get_schema_package_history(
    connection: Connection, action_by: UUID, schema_package_id: UUID
) -> list[dict]:
    """Get the history of a schema package."""
    params = {"action_by": action_by, "schema_package_id": schema_package_id}
    return execute_query(connection, GET_SCHEMA_PACKAGE_HISTORY_QUERY, **params)


async def get_schema_package_history_async(
    connection: AsyncConnection, action_by: UUID, schema_package_id: UUID
) -> list[dict]:
    """Get the history of a schema package."""
    params = {"action_by": action_by, "schema_package_id": schema_package_id}
    return await execute_query_async(connection, GET_SCHEMA_PACKAGE_HISTORY_QUERY, **params)


def get_schema_package_list(
    connection: Connection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of schema packages. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return execute_query(connection, GET_SCHEMA_PACKAGE_LIST_QUERY, **params)


async def get_schema_package_list_async(
    connection: AsyncConnection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of schema packages. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return await execute_query_async(connection, GET_SCHEMA_PACKAGE_LIST_QUERY, **params)


def create_schema_package(
    connection: Connection,
    action_by: UUID,
    name: str,
    data: dict | None,
    action_info: dict | None = None,
) -> dict:
    """Create a schema package."""
    params = {
        "action_by": action_by,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, CREATE_SCHEMA_PACKAGE_QUERY, **params)


async def create_schema_package_async(
    connection: AsyncConnection,
    action_by: UUID,
    name: str,
    data: dict | None,
    action_info: dict | None = None,
) -> dict:
    """Create a schema package."""
    params = {
        "action_by": action_by,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, CREATE_SCHEMA_PACKAGE_QUERY, **params)


def update_schema_package(
    connection: Connection,
    action_by: UUID,
    schema_package_id: UUID,
    name: str | None = None,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a schema package. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "schema_package_id": schema_package_id,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, UPDATE_SCHEMA_PACKAGE_QUERY, **params)


async def update_schema_package_async(
    connection: AsyncConnection,
    action_by: UUID,
    schema_package_id: UUID,
    name: str | None = None,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a schema package. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "schema_package_id": schema_package_id,
        "name": name,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, UPDATE_SCHEMA_PACKAGE_QUERY, **params)


def delete_schema_package(
    connection: Connection,
    action_by: UUID,
    schema_package_id: UUID,
    action_info: dict | None = None,
) -> dict:
    """Delete a schema package. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "schema_package_id": schema_package_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, DELETE_SCHEMA_PACKAGE_QUERY, **params)


async def delete_schema_package_async(
    connection: AsyncConnection,
    action_by: UUID,
    schema_package_id: UUID,
    action_info: dict | None = None,
) -> dict:
    """Delete a schema package. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "schema_package_id": schema_package_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, DELETE_SCHEMA_PACKAGE_QUERY, **params)
