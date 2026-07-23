"""Sequence management for Shinto library."""

from shinto.mimir.query_execution_handler import execute_query, execute_query_async
from shinto.pg.connection import AsyncConnection, Connection

GET_NEXT_SEQUENCE_VALUE_QUERY = "SELECT data.get_next_sequence_value(%(sequence_name)s)"
SEQUENCE_EXISTS_QUERY = "SELECT data.sequence_exists(%(sequence_name)s)"


def get_next_sequence_value(connection: Connection, sequence_name: str) -> int:
    """Get the next value of a sequence."""
    params = {"sequence_name": sequence_name}
    return execute_query(connection, GET_NEXT_SEQUENCE_VALUE_QUERY, params)


async def get_next_sequence_value_async(connection: AsyncConnection, sequence_name: str) -> int:
    """Get the next value of a sequence asynchronously."""
    params = {"sequence_name": sequence_name}
    return await execute_query_async(connection, GET_NEXT_SEQUENCE_VALUE_QUERY, params)


def sequence_exists(connection: Connection, sequence_name: str) -> bool:
    """Check if a sequence exists."""
    params = {"sequence_name": sequence_name}
    return execute_query(connection, SEQUENCE_EXISTS_QUERY, params)


async def sequence_exists_async(connection: AsyncConnection, sequence_name: str) -> bool:
    """Check if a sequence exists asynchronously."""
    params = {"sequence_name": sequence_name}
    return await execute_query_async(connection, SEQUENCE_EXISTS_QUERY, params)
