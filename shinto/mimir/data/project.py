"""Project management functions for Shinto Mimir."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shinto.general import normalize_timestamp
from shinto.mimir.query_execution_handler import execute_query, execute_query_async

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import AsyncConnection, Connection


GET_PROJECT_BY_ID_QUERY = """
SELECT to_json(data.get_project(
    %(action_by)s::uuid, %(project_id)s::uuid, %(timestamp)s::TIMESTAMPTZ
))
"""
GET_PROJECT_HISTORY_QUERY = """
SELECT COALESCE(json_agg(project), '[]'::json)
FROM data.get_project_history(%(action_by)s::uuid, %(project_id)s::uuid) AS project
"""
GET_PROJECT_LIST_QUERY = """
SELECT COALESCE(json_agg(project), '[]'::json)
FROM data.get_project_list(%(action_by)s::uuid, %(timestamp)s::TIMESTAMPTZ) AS project
"""
CREATE_PROJECT_QUERY = """
SELECT to_json(data.create_project(
    %(action_by)s::uuid, %(data)s::jsonb, null, null, %(action_info)s::jsonb
))
"""
UPDATE_PROJECT_QUERY = """
SELECT to_json(data.update_project(
    %(action_by)s::uuid, %(project_id)s::uuid, %(data)s::jsonb, null, null, %(action_info)s::jsonb
))
"""
DELETE_PROJECT_QUERY = """
SELECT to_json(data.delete_project(
    %(action_by)s::uuid, %(project_id)s::uuid, %(action_info)s::jsonb
))
"""
BULK_UPDATE_PROJECTS_QUERY = """
SELECT COALESCE(json_agg(row), '[]'::json)
FROM data.bulk_update_projects(%(action_by)s::uuid, %(operations)s::jsonb) AS row
"""

# Force update queries
FORCE_PROJECT_INSERT_QUERY = """
INSERT INTO data.project
    (
        "id",
        "timestamp",
        "action",
        "action_by",
        "action_info",
        taxonomy_id,
        taxonomy_timestamp,
        data)
VALUES
    (
        %s::uuid,
        %s::TIMESTAMPTZ,
        %s::base.record_action,
        %s::uuid,
        %s::json,
        %s::uuid,
        %s::TIMESTAMPTZ,
        %s::jsonb
    )
ON CONFLICT ("id", "timestamp") DO UPDATE SET
    action = EXCLUDED.action,
    action_by = EXCLUDED.action_by,
    action_info = EXCLUDED.action_info,
    taxonomy_id = EXCLUDED.taxonomy_id,
    taxonomy_timestamp = EXCLUDED.taxonomy_timestamp,
    data = EXCLUDED.data
RETURNING to_json(data.project.*)
"""
DISABLE_PROJECT_INSERT_TRIGGER = "ALTER TABLE data.project DISABLE TRIGGER project_insert_trigger"
DISABLE_PROJECT_CHANGE_TRIGGER = "ALTER TABLE data.project DISABLE TRIGGER project_change_trigger"
ENABLE_PROJECT_INSERT_TRIGGER = "ALTER TABLE data.project ENABLE TRIGGER project_insert_trigger"
ENABLE_PROJECT_CHANGE_TRIGGER = "ALTER TABLE data.project ENABLE TRIGGER project_change_trigger"


def get_project_by_id(
    connection: Connection,
    action_by: UUID,
    project_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a project by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "project_id": project_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return execute_query(connection, GET_PROJECT_BY_ID_QUERY, **params)


async def get_project_by_id_async(
    connection: AsyncConnection,
    action_by: UUID,
    project_id: UUID,
    timestamp: datetime | str | None = None,
) -> dict:
    """Get a project by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "project_id": project_id,
        "timestamp": normalize_timestamp(timestamp),
    }
    return await execute_query_async(connection, GET_PROJECT_BY_ID_QUERY, **params)


def get_project_history(connection: Connection, action_by: UUID, project_id: UUID) -> list[dict]:
    """Get the history of a project."""
    params = {"action_by": action_by, "project_id": project_id}
    return execute_query(connection, GET_PROJECT_HISTORY_QUERY, **params)


async def get_project_history_async(
    connection: AsyncConnection, action_by: UUID, project_id: UUID
) -> list[dict]:
    """Get the history of a project."""
    params = {"action_by": action_by, "project_id": project_id}
    return await execute_query_async(connection, GET_PROJECT_HISTORY_QUERY, **params)


def get_project_list(
    connection: Connection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return execute_query(connection, GET_PROJECT_LIST_QUERY, **params)


async def get_project_list_async(
    connection: AsyncConnection, action_by: UUID, timestamp: datetime | str | None = None
) -> list[dict]:
    """Get a list. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {"action_by": action_by, "timestamp": normalize_timestamp(timestamp)}
    return await execute_query_async(connection, GET_PROJECT_LIST_QUERY, **params)


def create_project(
    connection: Connection,
    action_by: UUID,
    data: dict | None,
    action_info: dict | None = None,
) -> dict:
    """Create a project."""
    params = {
        "action_by": action_by,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, CREATE_PROJECT_QUERY, **params)


async def create_project_async(
    connection: AsyncConnection,
    action_by: UUID,
    data: dict | None,
    action_info: dict | None = None,
) -> dict:
    """Create a project."""
    params = {
        "action_by": action_by,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, CREATE_PROJECT_QUERY, **params)


def update_project(
    connection: Connection,
    action_by: UUID,
    project_id: UUID,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a project. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "project_id": project_id,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, UPDATE_PROJECT_QUERY, **params)


async def update_project_async(
    connection: AsyncConnection,
    action_by: UUID,
    project_id: UUID,
    data: dict | None = None,
    action_info: dict | None = None,
) -> dict:
    """Update a project. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "project_id": project_id,
        "data": json.dumps(data) if data else None,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, UPDATE_PROJECT_QUERY, **params)


def delete_project(
    connection: Connection, action_by: UUID, project_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a project. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "project_id": project_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return execute_query(connection, DELETE_PROJECT_QUERY, **params)


async def delete_project_async(
    connection: AsyncConnection, action_by: UUID, project_id: UUID, action_info: dict | None = None
) -> dict:
    """Delete a project. Accepts timestamp as datetime, ISO 8601 string, or None."""
    params = {
        "action_by": action_by,
        "project_id": project_id,
        "action_info": json.dumps(action_info) if action_info else None,
    }
    return await execute_query_async(connection, DELETE_PROJECT_QUERY, **params)


def bulk_update_projects(
    connection: Connection, action_by: UUID, operations: list[dict]
) -> list[dict]:
    """Bulk update projects."""
    params = {
        "action_by": action_by,
        "operations": json.dumps(operations),
    }
    return execute_query(connection, BULK_UPDATE_PROJECTS_QUERY, **params)


async def bulk_update_projects_async(
    connection: AsyncConnection, action_by: UUID, operations: list[dict]
) -> list[dict]:
    """Bulk update projects."""
    params = {
        "action_by": action_by,
        "operations": json.dumps(operations),
    }
    return await execute_query_async(connection, BULK_UPDATE_PROJECTS_QUERY, **params)


def force_project_record(
    connection: Connection,
    action_by: UUID,
    action: str,
    project_id: UUID,
    timestamp: datetime | str,
    data: dict,
    action_info: dict | None = None,
    taxonomy_id: UUID | None = None,
    taxonomy_timestamp: datetime | str | None = None,
) -> dict:
    """Force create a project with a specific ID and timestamp."""
    timestamp = normalize_timestamp(timestamp)
    if taxonomy_id and taxonomy_timestamp:
        taxonomy_timestamp = normalize_timestamp(taxonomy_timestamp)
    else:
        taxonomy_timestamp = None

    if action not in ["created", "updated", "deleted"]:
        raise ValueError("Action must be one of 'created', 'updated', or 'deleted'.")

    if not action_info:
        action_info = {"forced": True}
    else:
        action_info["forced"] = True

    # First disable the trigger that prevents creating a project with a specific ID and timestamp
    connection.execute_command(DISABLE_PROJECT_INSERT_TRIGGER)

    # Second, disable the trigger that prevents updating a project with a specific ID and timestamp
    connection.execute_command(DISABLE_PROJECT_CHANGE_TRIGGER)

    # then insert the project with the specified ID and timestamp
    result = connection.execute_query(
        FORCE_PROJECT_INSERT_QUERY,
        (
            project_id,
            timestamp,
            action,
            action_by,
            json.dumps(action_info),
            taxonomy_id,
            taxonomy_timestamp,
            json.dumps(data) if data else None,
        ),
    )

    # Finally, turn the triggers back on
    connection.execute_command(ENABLE_PROJECT_CHANGE_TRIGGER)

    # Turn the trigger back on
    connection.execute_command(ENABLE_PROJECT_INSERT_TRIGGER)

    return result[0][0] if result else {}
