"""Project management functions for Shinto Mimir."""

import json
from datetime import datetime
from typing import Union, Optional
from uuid import UUID

from shinto.general import normalize_timestamp
from shinto.pg.connection import Connection


def get_project_by_id(
        connection: Connection,
        action_by: UUID,
        project_id: UUID,
        timestamp: Optional[Union[datetime, str]] = None
) -> dict:
    """Get a project by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        "SELECT to_json(data.get_project(%s::uuid, %s::uuid, %s::TIMESTAMPTZ))",
        (action_by, project_id, timestamp),
    )
    return result[0][0] if result else {}

def get_project_history(
        connection: Connection,
        action_by: UUID,
        project_id: UUID
) -> list[dict]:
    """Get the history of a project."""
    result = connection.execute_query(
        """
        SELECT COALESCE(json_agg(project), '[]'::json)
        FROM data.get_project_history(%s::uuid, %s::uuid
        ) AS project
        """,
        (action_by, project_id,)
    )
    return result[0][0] if result else []

def get_project_list(
        connection: Connection,
        action_by: UUID,
        timestamp: Optional[Union[datetime, str]] = None
) -> list[dict]:
    """Get a list. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        """
        SELECT COALESCE(json_agg(project), '[]'::json)
        FROM data.get_project_list(
            %s::uuid, 
            %s::TIMESTAMPTZ
        ) AS project
        """,
        (action_by, timestamp)
    )
    return result[0][0] if result else []

def create_project(
        connection: Connection,
        action_by: UUID,
        data: Optional[dict],
        action_info: Optional[dict] = None
) -> dict:
    """Create a project."""
    result = connection.execute_query(
        "SELECT to_json(data.create_project(%s::uuid, %s::jsonb, %s::jsonb))",
        (
            action_by,
            json.dumps(data) if data else None,
            json.dumps(action_info) if action_info else None),
    )
    return result[0][0] if result else {}

def force_project_record(
        connection: Connection,
        action_by: UUID,
        action: str,
        project_id: UUID,
        timestamp: Union[datetime, str],
        data: dict,
        action_info: Optional[dict],
        taxonomy_id: Optional[UUID] = None,
        taxonomy_timestamp: Optional[Union[datetime, str]] = None ) -> dict:
    """Force create a project with a specific ID and timestamp."""
    timestamp = normalize_timestamp(timestamp)
    if taxonomy_id and taxonomy_timestamp:
        taxonomy_timestamp = normalize_timestamp(taxonomy_timestamp)
    else:
        taxonomy_timestamp = None

    if action not in ['created', 'updated', 'deleted']:
        raise ValueError("Action must be one of 'created', 'updated', or 'deleted'.")

    if not action_info:
        action_info = {"forced": True}
    else:
        action_info["forced"] = True

    # First disable the trigger that prevents creating a project with a specific ID and timestamp
    connection.execute_command(
        "ALTER TABLE data.project DISABLE TRIGGER project_insert_trigger"
    )
    # then insert the project with the specified ID and timestamp
    connection.execute_command(
        """
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
                    %s::text, 
                    %s::uuid, 
                    %s::json, 
                    %s::uuid, 
                    %s::TIMESTAMPTZ, 
                    %s::jsonb
                )
            """,
        (
            project_id,
            timestamp,
            action,
            action_by,
            taxonomy_id,
            taxonomy_timestamp,
            json.dumps(data) if data else None,
            json.dumps(action_info)
        )
    )

    # Turn the trigger back on
    connection.execute_command(
        "ALTER TABLE data.project ENABLE TRIGGER project_insert_trigger"
    )

    return get_project_by_id(connection, action_by, project_id)


def update_project(
        connection: Connection,
        action_by: UUID,
        project_id: UUID,
        data: Optional[dict] = None,
        action_info: Optional[dict] = None
) -> dict:
    """Update a project. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        "SELECT to_json(data.update_project(%s::uuid, %s::uuid, %s::jsonb, %s::jsonb))",
        (
            action_by,
            project_id,
            json.dumps(data) if data else None,
            json.dumps(action_info) if action_info else None
        ),
    )
    return result[0][0] if result else {}

def delete_project(
        connection: Connection,
        action_by: UUID,
        project_id: UUID,
        action_info: Optional[dict] = None
) -> dict:
    """Delete a project. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        "SELECT to_json(data.delete_project(%s::uuid, %s::uuid, %s::jsonb))",
        (
            action_by,
            project_id,
            json.dumps(action_info) if action_info else None
        ),
    )
    return result[0][0] if result else {}
