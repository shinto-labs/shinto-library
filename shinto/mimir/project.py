import uuid
import json
from datetime import datetime
from typing import Union, Optional
from uuid import UUID

from shinto.general import normalize_timestamp

from shinto.pg.connection import Connection

def get_project_by_id(connection: Connection, action_by: UUID, project_id: uuid.UUID, timestamp: Optional[Union[datetime, str]] = None) -> dict:
    """Get a project by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        "SELECT to_json(data.get_project_by_id(%s::uuid, %s::uuid, %s::TIMESTAMPTZ))",
        (action_by, project_id, timestamp),
    )
    return result[0][0] if result else {}

def get_project_by_name(connection: Connection, action_by: UUID, project_name: str, timestamp: Optional[Union[datetime, str]] = None) -> dict:
    """Get a project by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        "SELECT to_json(data.get_project_by_name(%s::uuid, %s::text, %s::TIMESTAMPTZ))",
        (action_by, project_name, timestamp),
    )
    return result[0][0] if result else {}

def get_project_history(connection: Connection, action_by: UUID, project_id: uuid.UUID) -> list[dict]:
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

def get_project_list(connection: Connection, action_by: UUID, timestamp: Optional[Union[datetime, str]] = None) -> list[dict]:
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

def create_project(connection: Connection, action_by: UUID, data: Optional[dict] ) -> dict:
    """Create a project."""
    result = connection.execute_query(
        "SELECT to_json(data.create_project(%s::uuid, %s::jsonb))",
        (action_by, json.dumps(data)),
    )
    return result[0][0] if result else {}

def force_create_project(
        connection: Connection,
        action_by: UUID,
        project_id: UUID,
        timestamp: Union[datetime, str],
        data: dict,
        taxonomy_id: Optional[UUID] = None,
        taxonomy_timestamp: Optional[Union[datetime, str]] = None ) -> dict:
    """Force create a project with a specific ID and timestamp."""
    timestamp = normalize_timestamp(timestamp)
    if taxonomy_id and taxonomy_timestamp:
        taxonomy_timestamp = normalize_timestamp(taxonomy_timestamp)
    else:
        taxonomy_timestamp = None

    # First disable the trigger that prevents creating a project with a specific ID and timestamp
    connection.execute_command(
        "ALTER TABLE data.project DISABLE TRIGGER project_insert_trigger"
    )
    # then insert the project with the specified ID and timestamp
    result = connection.execute_query(
        """
            INSERT INTO data.project 
                ("id", "timestamp", "action", "action_by", "action_info", taxonomy_id, taxonomy_timestamp, data)
            VALUES 
                (%s::uuid, %s::TIMESTAMPTZ, 'created', %s::uuid, '{"force_create": true}', %s::uuid, %s::TIMESTAMPTZ, %s::jsonb)
            RETURNING to_json(*)
            """,
        (project_id, timestamp, action_by, taxonomy_id, taxonomy_timestamp, json.dumps(data))
    )
    # Turn the trigger back on
    connection.execute_command(
        "ALTER TABLE data.project ENABLE TRIGGER project_insert_trigger"
    )

    return result[0][0] if result else {}



def update_project(connection: Connection, action_by: UUID, project_id: uuid.UUID, data: Optional[dict] = None) -> dict:
    """Update a project. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        "SELECT to_json(data.update_project(%s::uuid, %s::uuid, %s::jsonb))",
        (action_by, project_id, json.dumps(data)),
    )
    return result[0][0] if result else {}

def delete_project(connection: Connection, action_by: UUID, project_id: uuid.UUID) -> dict:
    """Delete a project. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        "SELECT to_json(data.delete_project(%s::uuid, %s::uuid))",
        (action_by,project_id,),
    )
    return result[0][0] if result else {}
