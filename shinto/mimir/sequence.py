"""Sequence management for Shinto library."""

from shinto.mimir.exception import MimirException
from shinto.pg.connection import AsyncConnection, Connection

GET_NEXT_SEQUENCE_VALUE_QUERY = "SELECT data.get_next_sequence_value(%s)"
SEQUENCE_EXISTS_QUERY = "SELECT data.sequence_exists(%s)"


def get_next_sequence_value(connection: Connection, sequence_name: str) -> int:
    """Get the next value of a sequence."""
    result = connection.execute_query(GET_NEXT_SEQUENCE_VALUE_QUERY, (sequence_name,))
    if not result or not result[0][0]:
        raise MimirException(f"Failed to get next sequence value for sequence '{sequence_name}'")
    return result[0][0]


async def get_next_sequence_value_async(connection: AsyncConnection, sequence_name: str) -> int:
    """Get the next value of a sequence asynchronously."""
    result = await connection.execute_query(GET_NEXT_SEQUENCE_VALUE_QUERY, (sequence_name,))
    if not result or not result[0][0]:
        raise MimirException(f"Failed to get next sequence value for sequence '{sequence_name}'")
    return result[0][0]


def sequence_exists(connection: Connection, sequence_name: str) -> bool:
    """Check if a sequence exists."""
    result = connection.execute_query(SEQUENCE_EXISTS_QUERY, (sequence_name,))
    if not result or result[0][0] is None:
        raise MimirException(f"Failed to check if sequence exists for sequence '{sequence_name}'")
    return result[0][0]


async def sequence_exists_async(connection: AsyncConnection, sequence_name: str) -> bool:
    """Check if a sequence exists asynchronously."""
    result = await connection.execute_query(SEQUENCE_EXISTS_QUERY, (sequence_name,))
    if not result or result[0][0] is None:
        raise MimirException(f"Failed to check if sequence exists for sequence '{sequence_name}'")
    return result[0][0]
