import uuid
from datetime import datetime
from typing import Union, Optional
from shinto.general import normalize_timestamp

from shinto.pg.connection import Connection

def get_taxonomy_by_id(connection: Connection, taxonomy_id: uuid.UUID, timestamp: Optional[Union[datetime, str]] = None) -> dict:
    """Get a taxonomy by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        "SELECT to_json(data.get_taxonomy_by_id((base.get_shintolabs_user()).id, %s::uuid, %s::TIMESTAMPTZ))",
        (taxonomy_id, timestamp),
    )
    return result[0][0] if result else {}

def get_taxonomy_by_name(connection: Connection, taxonomy_name: str, timestamp: Optional[Union[datetime, str]] = None) -> dict:
    """Get a taxonomy by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        "SELECT to_json(data.get_taxonomy_by_name((base.get_shintolabs_user()).id, %s::text, %s::TIMESTAMPTZ))",
        (taxonomy_name, timestamp),
    )
    return result[0][0] if result else {}

def get_taxonomy_history(connection: Connection, taxonomy_id: uuid.UUID) -> list[dict]:
    """Get the history of a taxonomy."""
    result = connection.execute_query(
        """
            SELECT COALESCE(json_agg(row), '[]'::json)
            FROM data.get_taxonomy_history(
                (base.get_shintolabs_user()).id, 
                %s::uuid
            ) AS row
        """,
        (taxonomy_id,),
        fetch_all=True,
    )
    return result[0][0] if result else []

def get_taxonomy_list(connection: Connection, timestamp: Optional[Union[datetime, str]] = None) -> list[dict]:
    """Get a list of taxonomies. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        """
            SELECT COALESCE(json_agg(row), '[]'::json)
            FROM data.get_taxonomy_list(
                (base.get_shintolabs_user()).id, 
                %s::TIMESTAMPTZ
            ) AS row
        """,
        (timestamp,),
        fetch_all=True,
    )
    return result[0][0] if result else []

def create_taxonomy(connection: Connection, name: str, data: Optional[dict]) -> dict:
    """Create a taxonomy."""
    result = connection.execute_query(
        "SELECT to_json(data.create_taxonomy((base.get_shintolabs_user()).id, %s::text, %s::jsonb))",
        (name, data),
    )
    return result[0][0] if result else {}

def update_taxonomy(connection: Connection, taxonomy_id: uuid.UUID, name: Optional[str] = None, data: Optional[dict] = None ) -> dict:
    """Update a taxonomy. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        "SELECT to_json(data.update_taxonomy((base.get_shintolabs_user()).id, %s::uuid, %s::text, %s::jsonb))",
        (taxonomy_id, name, data),
    )
    return result[0][0] if result else {}

def delete_taxonomy(connection: Connection, taxonomy_id: uuid.UUID) -> dict:
    """Delete a taxonomy. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)
    result = connection.execute_query(
        "SELECT to_json(data.delete_taxonomy((base.get_shintolabs_user()).id, %s::uuid))",
        (taxonomy_id),
    )
    return result[0][0] if result else {}
