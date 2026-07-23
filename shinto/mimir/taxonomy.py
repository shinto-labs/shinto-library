"""Taxonomy management functions for Shinto Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.exception import MimirEntityNotFoundException

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import Connection

GET_TAXONOMY_BY_ID_QUERY = (
    "SELECT to_json(data.get_taxonomy_by_id(%s::uuid, %s::uuid, %s::TIMESTAMPTZ))"
)
GET_TAXONOMY_BY_NAME_QUERY = (
    "SELECT to_json(data.get_taxonomy_by_name(%s::uuid, %s::text, %s::TIMESTAMPTZ))"
)
GET_TAXONOMY_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_taxonomy_history(%s::uuid, %s::uuid) AS row"""
GET_TAXONOMY_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_taxonomy_list(%s::uuid, %s::TIMESTAMPTZ) AS row"""
CREATE_TAXONOMY_QUERY = (
    "SELECT to_json(data.create_taxonomy(%s::uuid, %s::text, %s::jsonb, %s::jsonb))"
)
UPDATE_TAXONOMY_QUERY = (
    "SELECT to_json(data.update_taxonomy(%s::uuid, %s::uuid, %s::text, %s::jsonb, %s::jsonb))"
)
DELETE_TAXONOMY_QUERY = "SELECT to_json(data.delete_taxonomy(%s::uuid, %s::uuid, %s::jsonb))"


def get_taxonomy_by_id(
    connection: Connection,
    action_by: UUID,
    taxonomy_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a taxonomy by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        GET_TAXONOMY_BY_ID_QUERY,
        (action_by, taxonomy_id, timestamp),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Taxonomy not found: %s", taxonomy_id)
    return result[0][0] if result else {}


def get_taxonomy_by_name(
    connection: Connection,
    action_by: UUID,
    taxonomy_name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a taxonomy by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        GET_TAXONOMY_BY_NAME_QUERY,
        (action_by, taxonomy_name, timestamp),
    )
    return result[0][0] if result else {}


def get_taxonomy_history(connection: Connection, action_by: UUID, taxonomy_id: UUID) -> list[dict]:
    """Get the history of a taxonomy."""
    result = connection.execute_query(
        GET_TAXONOMY_HISTORY_QUERY,
        (
            action_by,
            taxonomy_id,
        ),
    )
    return result[0][0] if result else []


def get_taxonomy_list(
    connection: Connection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of taxonomies. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        GET_TAXONOMY_LIST_QUERY,
        (
            action_by,
            timestamp,
        ),
    )
    return result[0][0] if result else []


def create_taxonomy(
    connection: Connection,
    action_by: UUID,
    name: str,
    data: dict | None,
    action_info: dict | None = None,
) -> dict:
    """Create a taxonomy."""
    result = connection.execute_query(
        CREATE_TAXONOMY_QUERY,
        (
            action_by,
            name,
            json.dumps(data) if data else None,
            json.dumps(action_info) if action_info else None,
        ),
    )
    return result[0][0] if result else {}


def update_taxonomy(
    connection: Connection,
    action_by: UUID,
    taxonomy_id: UUID,
    name: str | None = None,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a taxonomy. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        UPDATE_TAXONOMY_QUERY,
        (
            action_by,
            taxonomy_id,
            name,
            json.dumps(data) if data else None,
            json.dumps(action_info) if action_info else None,
        ),
    )
    return result[0][0] if result else {}


def delete_taxonomy(
    connection: Connection, action_by: UUID, taxonomy_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a taxonomy. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        DELETE_TAXONOMY_QUERY,
        (action_by, taxonomy_id, json.dumps(action_info) if action_info else None),
    )
    return result[0][0] if result else {}
