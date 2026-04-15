"""Internal functions for Mimir."""

import json
from typing import Union, Optional


from shinto.pg.connection import Connection


def get_mimir_version(
        connection: Connection
) -> str:
    """Get the Mimir version."""
    result = connection.execute_query(
        "SELECT base.get_mimir_version()"
    )
    return result[0][0] if result else None

def dump_database_to_json(
        connection: Connection,
        include_base: bool = True,
        include_audit: bool = True
) -> str:
    """Dump the entire database as JSON."""
    result = connection.execute_query(
        "SELECT base.dump_database_to_json(%s, %s)",
        (include_base, include_audit)
    )
    return result[0][0] if result else None

def load_table(
        connection: Connection,
        table_name: str,
        data: list[dict],
        update_action_by: bool = False
) -> None:
    """Load JSON data into a table."""
    connection.execute_query(
        "SELECT base.load_json_to_table(%s, %s::jsonb, %s)",
        (
            table_name,
            json.dumps(data),
            update_action_by
        )
    )
