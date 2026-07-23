"""Module for managing transformations in the Mimir data catalog."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.exception import MimirEntityNotFoundException

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import Connection


GET_TRANSFORMATION_BY_ID_QUERY = """SELECT to_json(data.get_transformation_by_id(
%s::uuid, %s::uuid, %s::TIMESTAMPTZ))"""
GET_TRANSFORMATION_BY_NAME_QUERY = """SELECT to_json(data.get_transformation_by_name(
%s::uuid, %s::text, %s::TIMESTAMPTZ))"""
GET_TRANSFORMATION_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_transformation_history(%s::uuid, %s::uuid) AS row"""
GET_TRANSFORMATION_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_transformation_list(%s::uuid, %s::TIMESTAMPTZ) AS row"""
CREATE_TRANSFORMATION_QUERY = (
    "SELECT to_json(data.create_transformation(%s::uuid, %s::text, %s::jsonb, %s::jsonb))"
)
UPDATE_TRANSFORMATION_QUERY = (
    "SELECT to_json(data.update_transformation(%s::uuid, %s::uuid, %s::text, %s::jsonb, %s::jsonb))"
)
DELETE_TRANSFORMATION_QUERY = (
    "SELECT to_json(data.delete_transformation(%s::uuid, %s::uuid, %s::jsonb))"
)


def get_transformation_by_id(
    connection: Connection,
    action_by: UUID,
    transformation_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a transformation by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        GET_TRANSFORMATION_BY_ID_QUERY,
        (action_by, transformation_id, timestamp),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Transformation not found: %s", transformation_id)
    return result[0][0]


def get_transformation_by_name(
    connection: Connection,
    action_by: UUID,
    transformation_name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a transformation by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        GET_TRANSFORMATION_BY_NAME_QUERY,
        (action_by, transformation_name, timestamp),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Transformation not found: %s", transformation_name)
    return result[0][0]


def get_transformation_history(
    connection: Connection, action_by: UUID, transformation_id: UUID
) -> list[dict]:
    """Get the history of a transformation."""
    result = connection.execute_query(
        GET_TRANSFORMATION_HISTORY_QUERY,
        (
            action_by,
            transformation_id,
        ),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException(
            "Transformation history not found: %s", transformation_id
        )
    return result[0][0]


def get_transformation_list(
    connection: Connection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        GET_TRANSFORMATION_LIST_QUERY,
        (
            action_by,
            timestamp,
        ),
    )
    return result[0][0] if result else []


def create_transformation(
    connection: Connection, action_by: UUID, name: str, data: dict, action_info: dict | None = None
) -> dict:
    """Create a transformation."""
    result = connection.execute_query(
        CREATE_TRANSFORMATION_QUERY,
        (
            action_by,
            name,
            json.dumps(data) if data else None,
            json.dumps(action_info) if action_info else None,
        ),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Transformation not created: %s", name)
    return result[0][0]


def update_transformation(
    connection: Connection,
    action_by: UUID,
    transformation_id: UUID,
    name: str | None = None,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a transformation. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        UPDATE_TRANSFORMATION_QUERY,
        (
            action_by,
            transformation_id,
            name,
            json.dumps(data) if data else None,
            json.dumps(action_info) if action_info else None,
        ),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Transformation not updated: %s", transformation_id)
    return result[0][0]


def delete_transformation(
    connection: Connection,
    action_by: UUID,
    transformation_id: UUID,
    action_info: dict | None = None,
) -> dict:
    """Delete a transformation. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        DELETE_TRANSFORMATION_QUERY,
        (action_by, transformation_id, json.dumps(action_info) if action_info else None),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Transformation not deleted: %s", transformation_id)
    return result[0][0]
