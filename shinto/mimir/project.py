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
        "SELECT to_json(data.get_project(%s::uuid, %s::uuid, %s::TIMESTAMPTZ))",
        (action_by, project_id, timestamp),
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
    connection.execute_command(
        """
            INSERT INTO data.project 
                ("id", "timestamp", "action", "action_by", "action_info", taxonomy_id, taxonomy_timestamp, data)
            VALUES 
                (%s::uuid, %s::TIMESTAMPTZ, 'created', %s::uuid, '{"force_create": true}'::json, %s::uuid, %s::TIMESTAMPTZ, %s::jsonb)
            """,
        (project_id, timestamp, action_by, taxonomy_id, taxonomy_timestamp, json.dumps(data))
    )

    # Turn the trigger back on
    connection.execute_command(
        "ALTER TABLE data.project ENABLE TRIGGER project_insert_trigger"
    )

    return get_project_by_id(connection, action_by, project_id)



def update_project(connection: Connection, action_by: UUID, project_id: uuid.UUID, data: Optional[dict] = None) -> dict:
    """Update a project. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        "SELECT to_json(data.update_project(%s::uuid, %s::uuid, %s::jsonb))",
        (action_by, project_id, json.dumps(data)),
    )
    return result[0][0] if result else {}

def force_update_project(
        connection: Connection,
        action_by: UUID,
        project_id: UUID,
        timestamp: Union[datetime, str],
        data: dict,
        taxonomy_id: Optional[UUID] = None,
        taxonomy_timestamp: Optional[Union[datetime, str]] = None ) -> dict:
    """Force update a project with a specific timestamp."""
    timestamp = normalize_timestamp(timestamp)
    if taxonomy_id and taxonomy_timestamp:
        taxonomy_timestamp = normalize_timestamp(taxonomy_timestamp)
    else:
        taxonomy_timestamp = None

    # First disable the trigger that prevents updating a project with a specific timestamp
    connection.execute_command(
        "ALTER TABLE data.project DISABLE TRIGGER project_update_trigger"
    )
    # then update the project with the specified timestamp
    connection.execute_command(
        """
            UPDATE data.project 
            SET 
                "action_by" = %s::uuid, 
                "action_info" = '{"force_update": true}'::json, 
                taxonomy_id = %s::uuid, 
                taxonomy_timestamp = %s::TIMESTAMPTZ, 
                data = %s::jsonb
            WHERE id = %s::uuid, timestamp = %s::TIMESTAMPTZ
            """,
        (timestamp, action_by, taxonomy_id, taxonomy_timestamp, json.dumps(data), project_id)
    )

    # Turn the trigger back on
    connection.execute_command(
        "ALTER TABLE data.project ENABLE TRIGGER project_update_trigger"
    )

    return get_project_by_id(connection, action_by, project_id)


def delete_project(connection: Connection, action_by: UUID, project_id: uuid.UUID) -> dict:
    """Delete a project. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        "SELECT to_json(data.delete_project(%s::uuid, %s::uuid))",
        (action_by,project_id,),
    )
    return result[0][0] if result else {}
