import uuid
from datetime import datetime
from typing import Union, Optional
from shinto.general import normalize_timestamp

from shinto.pg.connection import Connection

def get_marker_by_id(connection: Connection, marker_id: uuid.UUID, timestamp: Optional[Union[datetime, str]] = None) -> dict:
    """Get a marker by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        "SELECT to_json(data.get_marker_by_id((base.get_shintolabs_user()).id, %s::uuid, %s::TIMESTAMPTZ))",
        (marker_id, timestamp),
    )
    return result[0][0] if result else {}

def get_marker_by_name(connection: Connection, marker_name: str, timestamp: Optional[Union[datetime, str]] = None) -> dict:
    """Get a marker by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        "SELECT to_json(data.get_marker_by_name((base.get_shintolabs_user()).id, %s::text, %s::TIMESTAMPTZ))",
        (marker_name, timestamp),
    )
    return result[0][0] if result else {}

def get_marker_history(connection: Connection, marker_id: uuid.UUID) -> list[dict]:
    """Get the history of a marker."""
    result = connection.execute_query(
        """
            SELECT COALESCE(json_agg(row), '[]'::json)
            FROM data.get_marker_history(
                (base.get_shintolabs_user()).id, 
                %s::uuid
            ) AS row
        """,
        (marker_id,),
        fetch_all=True,
    )
    return result[0][0] if result else []

def get_marker_list(connection: Connection, timestamp: Optional[Union[datetime, str]] = None) -> list[dict]:
    """Get a list of taxonomies. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        """
            SELECT COALESCE(json_agg(row), '[]'::json)
            FROM data.get_marker_list(
                (base.get_shintolabs_user()).id, 
                %s::TIMESTAMPTZ
            ) AS row
        """,
        (timestamp,),
        fetch_all=True,
    )
    return result[0][0] if result else []

def create_marker(connection: Connection, name: str, marked_timestamp: Optional[Union[datetime, str]] = None) -> dict:
    """Create a marker."""
    marked_timestamp = normalize_timestamp(marked_timestamp)

    result = connection.execute_query(
        "SELECT to_json(data.create_marker((base.get_shintolabs_user()).id, %s::text, %s::jsonb))",
        (name, marked_timestamp),
    )
    return result[0][0] if result else {}

def update_marker(connection: Connection, marker_id: uuid.UUID, name: Optional[str] = None, marked_timestamp: Optional[Union[datetime, str]] = None ) -> dict:
    """Update a marker. Accepts timestamp as datetime, ISO 8601 string, or None."""
    marked_timestamp=normalize_timestamp(marked_timestamp)

    result = connection.execute_query(
        "SELECT to_json(data.update_marker((base.get_shintolabs_user()).id, %s::uuid, %s::text, %s::jsonb))",
        (marker_id, name, marked_timestamp),
    )
    return result[0][0] if result else {}

def delete_marker(connection: Connection, marker_id: uuid.UUID) -> dict:
    """Delete a marker. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        "SELECT to_json(data.delete_marker((base.get_shintolabs_user()).id, %s::uuid))",
        (marker_id),
    )
    return result[0][0] if result else {}
