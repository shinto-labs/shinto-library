import uuid
from datetime import datetime
from typing import Union, Optional
from shinto.general import normalize_timestamp

from shinto.pg.connection import Connection

def get_transformation_by_id(connection: Connection, transformation_id: uuid.UUID, timestamp: Optional[Union[datetime, str]] = None) -> dict:
    """Get a transformation by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        "SELECT to_json(data.get_transformation_by_id((base.get_shintolabs_user()).id, %s::uuid, %s::TIMESTAMPTZ))",
        (transformation_id, timestamp),
    )
    return result[0][0] if result else {}

def get_transformation_by_name(connection: Connection, transformation_name: str, timestamp: Optional[Union[datetime, str]] = None) -> dict:
    """Get a transformation by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        "SELECT to_json(data.get_transformation_by_name((base.get_shintolabs_user()).id, %s::text, %s::TIMESTAMPTZ))",
        (transformation_name, timestamp),
    )
    return result[0][0] if result else {}

def get_transformation_history(connection: Connection, transformation_id: uuid.UUID) -> list[dict]:
    """Get the history of a transformation."""
    result = connection.execute_query(
        """
            SELECT COALESCE(json_agg(row), '[]'::json)
            FROM data.get_transformation_history(
                (base.get_shintolabs_user()).id, 
                %s::uuid
            ) AS row
        """,
        (transformation_id,),
        fetch_all=True,
    )
    return result[0][0] if result else []

def get_transformation_list(connection: Connection, timestamp: Optional[Union[datetime, str]] = None) -> list[dict]:
    """Get a list. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        """
            SELECT COALESCE(json_agg(row), '[]'::json)
            FROM data.get_transformation_list(
                (base.get_shintolabs_user()).id, 
                %s::TIMESTAMPTZ
            ) AS row
        """,
        (timestamp,)
    )
    return result[0][0] if result else []

def create_transformation(connection: Connection, name: str, data: list) -> dict:
    """Create a transformation."""
    result = connection.execute_query(
        "SELECT to_json(data.create_transformation((base.get_shintolabs_user()).id, %s::text, %s::jsonb))",
        (name, data),
    )
    return result[0][0] if result else {}

def update_transformation(connection: Connection, transformation_id: uuid.UUID, name: Optional[str] = None, data: list = None) -> dict:
    """Update a transformation. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        "SELECT to_json(data.update_transformation((base.get_shintolabs_user()).id, %s::uuid, %s::text, %s::jsonb))",
        (transformation_id, name, data),
    )
    return result[0][0] if result else {}

def delete_transformation(connection: Connection, transformation_id: uuid.UUID) -> dict:
    """Delete a transformation. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        "SELECT to_json(data.delete_transformation((base.get_shintolabs_user()).id, %s::uuid))",
        (transformation_id),
    )
    return result[0][0] if result else {}

