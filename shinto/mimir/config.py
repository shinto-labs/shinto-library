import uuid
from datetime import datetime
from typing import Union, Optional

from shinto.general import normalize_timestamp
from shinto.pg.connection import Connection

def get_config_by_id(
        connection: Connection,
        action_by: uuid.UUID,
        config_id: uuid.UUID,
        timestamp: Optional[Union[datetime, str]] = None
) -> dict:
    """Get a config by ID. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        "SELECT to_json(data.get_config_by_id(%s, %s::uuid, %s::TIMESTAMPTZ))",
        (action_by, config_id, timestamp),
    )
    return result[0][0] if result else {}

def get_config_by_name(
        connection: Connection,
        action_by: uuid.UUID,
        config_name: str,
        timestamp: Optional[Union[datetime, str]] = None
) -> dict:
    """Get a config by name. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        "SELECT to_json(data.get_config_by_name(%s::uuid, %s::text, %s::TIMESTAMPTZ))",
        (action_by, config_name, timestamp),
    )
    return result[0][0] if result else {}

def get_config_history(
        connection: Connection,
        action_by: uuid.UUID,
        config_id: uuid.UUID
) -> list[dict]:
    """Get the history of a config."""
    result = connection.execute_query(
        """
            SELECT COALESCE(json_agg(row), '[]'::json)
            FROM data.get_config_history(
                %s::uuid, 
                %s::uuid
            ) AS row
        """,
        (action_by, config_id,)
    )
    return result[0][0] if result else []

def get_config_list(
        connection: Connection,
        action_by: uuid.UUID,
        timestamp: Optional[Union[datetime, str]] = None
) -> list[dict]:
    """Get a list of taxonomies. Accepts timestamp as datetime, ISO 8601 string, or None."""
    timestamp = normalize_timestamp(timestamp)

    result = connection.execute_query(
        """
            SELECT COALESCE(json_agg(row), '[]'::json)
            FROM data.get_config_list(
                %s::uuid, 
                %s::TIMESTAMPTZ
            ) AS row
        """,
        (action_by, timestamp,)
    )
    return result[0][0] if result else []

def create_config(
        connection: Connection,
        action_by: uuid.UUID,
        name: str,
        data: Optional[dict]
) -> dict:
    """Create a config."""
    result = connection.execute_query(
        "SELECT to_json(data.create_config(%s::uuid, %s::text, %s::jsonb))",
        (action_by, name, data),
    )
    return result[0][0] if result else {}

def update_config(
        connection: Connection,
        action_by: uuid.UUID,
        config_id: uuid.UUID,
        name: Optional[str] = None,
        data: Optional[dict] = None
) -> dict:
    """Update a config. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        "SELECT to_json(data.update_config(%s::uuid, %s::uuid, %s::text, %s::jsonb))",
        (action_by, config_id, name, data),
    )
    return result[0][0] if result else {}

def delete_config(
        connection: Connection,
        action_by: uuid.UUID,
        config_id: uuid.UUID
) -> dict:
    """Delete a config. Accepts timestamp as datetime, ISO 8601 string, or None."""
    result = connection.execute_query(
        "SELECT to_json(data.delete_config((%s::uuid, %s::uuid))",
        (action_by, config_id),
    )
    return result[0][0] if result else {}
