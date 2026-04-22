import json
from datetime import datetime
from typing import Union, Optional
from uuid import UUID

from shinto.general import normalize_timestamp
from shinto.pg.connection import Connection

def get_taxonomy_by_id(
        connection: Connection,
        action_by: UUID,
        taxonomy_id: UUID,
        timestamp: Optional[Union[datetime, str]] = None
) -> dict:
    """Get a taxonomy by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        "SELECT to_json(data.get_taxonomy_by_id(%s::uuid, %s::uuid, %s::TIMESTAMPTZ))",
        (action_by, taxonomy_id, timestamp),
    )
    return result[0][0] if result else {}

def get_taxonomy_by_name(
        connection: Connection,
        action_by: UUID,
        taxonomy_name: str,
        timestamp: Optional[Union[datetime, str]] = None
) -> dict:
    """Get a taxonomy by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        "SELECT to_json(data.get_taxonomy_by_name(%s::uuid, %s::text, %s::TIMESTAMPTZ))",
        (action_by, taxonomy_name, timestamp),
    )
    return result[0][0] if result else {}

def get_taxonomy_history(
        connection: Connection,
        action_by: UUID,
        taxonomy_id: UUID
) -> list[dict]:
    """Get the history of a taxonomy."""
    result = connection.execute_query(
        """
            SELECT COALESCE(json_agg(row), '[]'::json)
            FROM data.get_taxonomy_history(
                %s::uuid, 
                %s::uuid
            ) AS row
        """,
        (action_by, taxonomy_id,)
    )
    return result[0][0] if result else []

def get_taxonomy_list(
        connection: Connection,
        action_by: UUID,
        timestamp: Optional[Union[datetime, str]] = None
) -> list[dict]:
    """Get a list of taxonomies. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        """
            SELECT COALESCE(json_agg(row), '[]'::json)
            FROM data.get_taxonomy_list(
                %s::uuid, 
                %s::TIMESTAMPTZ
            ) AS row
        """,
        (action_by, timestamp,)
    )
    return result[0][0] if result else []

def create_taxonomy(
        connection: Connection,
        action_by: UUID,
        name: str, data: Optional[dict],
        action_info: Optional[dict] = None
) -> dict:
    """Create a taxonomy."""
    result = connection.execute_query(
        "SELECT to_json(data.create_taxonomy(%s::uuid, %s::text, %s::jsonb, %s::jsonb))",
        (
            action_by,
            name,
            json.dumps(data) if data else None,
            json.dumps(action_info) if action_info else None
        )
    )
    return result[0][0] if result else {}

def update_taxonomy(
        connection: Connection,
        action_by: UUID,
        taxonomy_id: UUID,
        name: Optional[str] = None,
        data: Optional[dict] = None,
        action_info: Optional[dict] = None
) -> dict:
    """Update a taxonomy. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        "SELECT to_json(data.update_taxonomy(%s::uuid, %s::uuid, %s::text, %s::jsonb, %s::jsonb))",
        (
            action_by,
            taxonomy_id,
            name,
            json.dumps(data) if data else None,
            json.dumps(action_info) if action_info else None
        )
    )
    return result[0][0] if result else {}

def delete_taxonomy(
        connection: Connection,
        action_by: UUID,
        taxonomy_id: UUID,
        action_info: Optional[dict] = None
) -> dict:
    """Delete a taxonomy. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        "SELECT to_json(data.delete_taxonomy(%s::uuid, %s::uuid, %s::jsonb))",
        (
            action_by,
            taxonomy_id,
            json.dumps(action_info) if action_info else None
        )
    )
    return result[0][0] if result else {}
