"""Internal functions for Mimir."""

from uuid import UUID

from shinto.pg.connection import Connection


def get_default_user(
        connection: Connection
) -> dict:
    """Get the default user."""
    result = connection.execute_query(
        "SELECT to_json(base.get_shintolabs_user())"
    )
    return result[0][0] if result else {}

def get_default_user_id(
        connection: Connection
) -> UUID:
    """Get the default user ID."""
    result = connection.execute_query(
        "SELECT (base.get_shintolabs_user()).id"
    )
    return result[0][0] if result else None
