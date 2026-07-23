"""User management functions for Shinto Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.exception import MimirEntityNotFoundException

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import Connection


GET_USER_BY_ID_QUERY = "SELECT to_json(data.get_user_by_id(%s, %s::uuid, %s::TIMESTAMPTZ))"
GET_USER_BY_NAME_QUERY = (
    "SELECT to_json(data.get_user_by_name(%s::uuid, %s::text, %s::TIMESTAMPTZ))"
)
GET_USER_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_user_history(%s::uuid, %s::uuid) AS row"""
GET_USER_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_user_list(%s::uuid, %s::TIMESTAMPTZ) AS row"""
CREATE_USER_QUERY = "SELECT to_json(data.create_user(%s::uuid, %s::text, %s::jsonb, %s::jsonb))"
UPDATE_USER_QUERY = (
    "SELECT to_json(data.update_user(%s::uuid, %s::uuid, %s::text, %s::jsonb, %s::jsonb))"
)
DELETE_USER_QUERY = "SELECT to_json(data.delete_user((%s::uuid, %s::uuid, %s::jsonb)))"


def get_user_by_id(
    connection: Connection,
    action_by: UUID,
    user_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a user by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        GET_USER_BY_ID_QUERY,
        (action_by, user_id, timestamp),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("User not found: %s", user_id)
    return result[0][0]


def get_user_by_name(
    connection: Connection,
    action_by: UUID,
    user_name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a user by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        GET_USER_BY_NAME_QUERY,
        (action_by, user_name, timestamp),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("User history not found: %s", user_name)
    return result[0][0]


def get_user_history(connection: Connection, action_by: UUID, user_id: UUID) -> list[dict]:
    """Get the history of a user."""
    result = connection.execute_query(
        GET_USER_HISTORY_QUERY,
        (
            action_by,
            user_id,
        ),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("User history not found: %s", user_id)
    return result[0][0]


def get_user_list(
    connection: Connection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        GET_USER_LIST_QUERY,
        (
            action_by,
            timestamp,
        ),
    )
    return result[0][0] if result else []


def create_user(
    connection: Connection, action_by: UUID, name: str, data: dict, action_info: dict | None = None
) -> dict:
    """Create a user."""
    result = connection.execute_query(
        CREATE_USER_QUERY,
        (
            action_by,
            name,
            json.dumps(data) if data else None,
            json.dumps(action_info) if action_info else None,
        ),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("User not created: %s", name)
    return result[0][0]


def update_user(
    connection: Connection,
    action_by: UUID,
    user_id: UUID,
    name: str | None = None,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a user. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        UPDATE_USER_QUERY,
        (
            action_by,
            user_id,
            name,
            json.dumps(data) if data else None,
            json.dumps(action_info) if action_info else None,
        ),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("User not updated: %s", user_id)
    return result[0][0]


def delete_user(
    connection: Connection, action_by: UUID, user_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a user. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        DELETE_USER_QUERY,
        (action_by, user_id, json.dumps(action_info) if action_info else None),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("User not deleted: %s", user_id)
    return result[0][0]
