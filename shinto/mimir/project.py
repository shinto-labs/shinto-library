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
        "SELECT to_json(data.create_project(%s::uuid, %s::text, %s::jsonb))",
        (action_by, json.dumps(data)),
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
