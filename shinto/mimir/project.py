import uuid
from datetime import datetime
from typing import Union, Optional
from uuid import UUID

from shinto.general import normalize_timestamp

from shinto.pg.connection import Connection

def get_project_by_id(connection: Connection, project_id: uuid.UUID, timestamp: Optional[Union[datetime, str]] = None) -> dict:
    """Get a project by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        "SELECT to_json(data.get_project_by_id((base.get_shintolabs_user()).id, %s::uuid, %s::TIMESTAMPTZ))",
        (project_id, timestamp),
    )
    return result[0][0] if result else {}

def get_project_by_name(connection: Connection, project_name: str, timestamp: Optional[Union[datetime, str]] = None) -> dict:
    """Get a project by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        "SELECT to_json(data.get_project_by_name((base.get_shintolabs_user()).id, %s::text, %s::TIMESTAMPTZ))",
        (project_name, timestamp),
    )
    return result[0][0] if result else {}

def get_project_history(connection: Connection, project_id: uuid.UUID) -> list[dict]:
    """Get the history of a project."""
    result = connection.execute_query(
        """
        SELECT COALESCE(json_agg(project), '[]'::json)
        FROM data.get_project_history(
            (base.get_shintolabs_user()).id, 
            %s::uuid
        ) AS project
        """,
        (project_id,)
    )
    return result[0][0] if result else []

def get_project_list(connection: Connection, timestamp: Optional[Union[datetime, str]] = None, action_by: UUID|None = None ) -> list[dict]:
    """Get a list. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        """
        SELECT COALESCE(json_agg(project), '[]'::json)
        FROM data.get_project_list(
            (base.get_shintolabs_user()).id, 
            %s::TIMESTAMPTZ
        ) AS project
        """,
        (timestamp,)
    )
    return result[0][0] if result else []

def create_project(connection: Connection, data: Optional[dict], action_by: UUID|None = None ) -> dict:
    """Create a project."""
    result = connection.execute_query(
        "SELECT to_json(data.create_project((base.get_shintolabs_user()).id, %s::text, %s::jsonb))",
        (data),
    )
    return result[0][0] if result else {}

def update_project(connection: Connection, project_id: uuid.UUID, data: Optional[dict] = None, action_by: UUID|None = None) -> dict:
    """Update a project. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        "SELECT to_json(data.update_project((base.get_shintolabs_user()).id, %s::uuid, %s::jsonb))",
        (project_id, data),
    )
    return result[0][0] if result else {}

def delete_project(connection: Connection, project_id: uuid.UUID) -> dict:
    """Delete a project. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        "SELECT to_json(data.delete_project(%s::uuid))",
        (project_id,),
    )
    return result[0][0] if result else {}
