"""Marker management functions for Shinto Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.exception import MimirEntityNotFoundException

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import Connection


GET_MARKER_BY_ID_QUERY = """
SELECT to_json(data.get_marker_by_id(%s::uuid, %s::uuid, %s::TIMESTAMPTZ))
"""
GET_MARKER_BY_NAME_QUERY = """
SELECT to_json(data.get_marker_by_name(%s::uuid, %s::text, %s::TIMESTAMPTZ))
"""
GET_MARKER_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_marker_history(%s::uuid, %s::uuid) AS row"""
GET_MARKER_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_marker_list(%s::uuid, %s::TIMESTAMPTZ) AS row"""
CREATE_MARKER_QUERY = """
SELECT to_json(data.create_marker(%s::uuid, %s::text, %s::timestamptz, %s::jsonb))
"""
UPDATE_MARKER_QUERY = """SELECT to_json(data.update_marker(
%s::uuid,
%s::uuid,
%s::text,
%s::timestamptz,
%s::jsonb
))"""
DELETE_MARKER_QUERY = "SELECT to_json(data.delete_marker(%s::uuid, %s::uuid, %s::jsonb))"


def get_marker_by_id(
    connection: Connection,
    action_by: UUID,
    marker_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a marker by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        GET_MARKER_BY_ID_QUERY,
        (action_by, marker_id, timestamp),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Marker not found by ID: {marker_id}")
    return result[0][0]


def get_marker_by_name(
    connection: Connection,
    action_by: UUID,
    marker_name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a marker by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        GET_MARKER_BY_NAME_QUERY,
        (action_by, marker_name, timestamp),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Marker not found by name: {marker_name}")
    return result[0][0]


def get_marker_history(connection: Connection, action_by: UUID, marker_id: UUID) -> list[dict]:
    """Get the history of a marker."""
    result = connection.execute_query(
        GET_MARKER_HISTORY_QUERY,
        (
            action_by,
            marker_id,
        ),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Marker not found: %s", marker_id)
    return result[0][0]


def get_marker_list(
    connection: Connection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of taxonomies. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        GET_MARKER_LIST_QUERY,
        (
            action_by,
            timestamp,
        ),
    )
    return result[0][0] if result else []


def create_marker(
    connection: Connection,
    action_by: UUID,
    name: str,
    marked_timestamp: datetime | str | None = None,
    action_info: dict | None = None,
) -> dict:
    """Create a marker."""
    marked_timestamp = normalize_timestamp(marked_timestamp)

    result = connection.execute_query(
        CREATE_MARKER_QUERY,
        (action_by, name, marked_timestamp, json.dumps(action_info) if action_info else None),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Unable to create marker: %s", name)
    return result[0][0]


def update_marker(
    connection: Connection,
    action_by: UUID,
    marker_id: UUID,
    name: str | None = None,
    marked_timestamp: datetime | str | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a marker. Accepts timestamp as datetime, ISO 8601 string, or None."""
    marked_timestamp = normalize_timestamp(marked_timestamp)

    result = connection.execute_query(
        UPDATE_MARKER_QUERY,
        (
            action_by,
            marker_id,
            name,
            marked_timestamp,
            json.dumps(action_info) if action_info else None,
        ),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Marker not updated: %s", marker_id)
    return result[0][0]


def delete_marker(
    connection: Connection, action_by: UUID, marker_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a marker. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        DELETE_MARKER_QUERY,
        (action_by, marker_id, json.dumps(action_info) if action_info else None),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Marker not deleted: %s", marker_id)
    return result[0][0]
