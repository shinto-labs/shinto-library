"""Module for managing configs in Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.exception import MimirEntityNotFoundException

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import Connection


GET_CONFIG_BY_ID_QUERY = "SELECT to_json(data.get_config_by_id(%s, %s::uuid, %s::TIMESTAMPTZ))"
GET_CONFIG_BY_NAME_QUERY = (
    "SELECT to_json(data.get_config_by_name(%s::uuid, %s::text, %s::TIMESTAMPTZ))"
)
GET_CONFIG_HISTORY_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_config_history(%s::uuid, %s::uuid) AS row"""
GET_CONFIG_LIST_QUERY = """SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.get_config_list(%s::uuid, %s::TIMESTAMPTZ) AS row"""
CREATE_CONFIG_QUERY = "SELECT to_json(data.create_config(%s::uuid, %s::text, %s::jsonb, %s::jsonb))"
UPDATE_CONFIG_QUERY = (
    "SELECT to_json(data.update_config(%s::uuid, %s::uuid, %s::text, %s::jsonb, %s::jsonb))"
)
DELETE_CONFIG_QUERY = "SELECT to_json(data.delete_config((%s::uuid, %s::uuid, %s::jsonb)))"


def get_config_by_id(
    connection: Connection,
    action_by: UUID,
    config_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a config by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        GET_CONFIG_BY_ID_QUERY,
        (action_by, config_id, timestamp),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Config not found by ID: {config_id}")
    return result[0][0]


def get_config_by_name(
    connection: Connection,
    action_by: UUID,
    config_name: str,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a config by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        GET_CONFIG_BY_NAME_QUERY,
        (action_by, config_name, timestamp),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Config not found by name: {config_name}")
    return result[0][0]


def get_config_history(connection: Connection, action_by: UUID, config_id: UUID) -> list[dict]:
    """Get the history of a config."""
    result = connection.execute_query(
        GET_CONFIG_HISTORY_QUERY,
        (
            action_by,
            config_id,
        ),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Config not found by ID: {config_id}")
    return result[0][0]


def get_config_list(
    connection: Connection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list of taxonomies. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        GET_CONFIG_LIST_QUERY,
        (
            action_by,
            timestamp,
        ),
    )
    return result[0][0] if result else []


def create_config(
    connection: Connection, action_by: UUID, name: str, data: dict, action_info: dict | None = None
) -> dict:
    """Create a config."""
    result = connection.execute_query(
        CREATE_CONFIG_QUERY,
        (
            action_by,
            name,
            json.dumps(data) if data else None,
            json.dumps(action_info) if action_info else None,
        ),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Config not created")
    return result[0][0]


def update_config(
    connection: Connection,
    action_by: UUID,
    config_id: UUID,
    name: str | None = None,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a config. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        UPDATE_CONFIG_QUERY,
        (
            action_by,
            config_id,
            name,
            json.dumps(data) if data else None,
            json.dumps(action_info) if action_info else None,
        ),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Config not updated")
    return result[0][0]


def delete_config(
    connection: Connection, action_by: UUID, config_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a config. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        DELETE_CONFIG_QUERY,
        (action_by, config_id, json.dumps(action_info) if action_info else None),
    )
    if not result or not result[0][0]:
        raise MimirEntityNotFoundException("Config not deleted")
    return result[0][0]
