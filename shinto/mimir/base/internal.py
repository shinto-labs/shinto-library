"""Base internal functions for Mimir."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from psycopg import sql
from psycopg.errors import ProgramLimitExceeded

from shinto.mimir.query_execution_handler import execute_query, execute_query_async

if TYPE_CHECKING:
    from uuid import UUID

    from shinto.pg.connection import AsyncConnection, Connection


GET_DEFAULT_USER_QUERY = "SELECT to_json(base.get_shintolabs_user())"
GET_DEFAULT_USER_ID_QUERY = "SELECT (base.get_shintolabs_user()).id"
GET_MIMIR_VERSION_QUERY = "SELECT base.mimir_version()"
DUMP_DATABASE_TO_JSON_QUERY = """
SELECT base.dump_database_to_json(
    %(include_base)s, %(include_audit)s
)
"""
LOAD_JSON_TO_TABLE_QUERY = """
SELECT base.load_json_to_table(
    %(table_name)s, %(data)s::jsonb, %(update_action_by)s
)
"""
DUMP_METADATA_QUERY = """
SELECT jsonb_build_object(
    'database_name', current_database(),
    'version', base.mimir_version(),
    'timestamp', now()
)
"""
DUMP_TABLES_QUERY = """
SELECT t.table_schema, t.table_name
FROM information_schema.tables t
WHERE t.table_schema = ANY(%(schemas)s)
  AND t.table_type = 'BASE TABLE'
  AND NOT EXISTS (
      SELECT 1
      FROM pg_inherits i
      JOIN pg_class c ON i.inhrelid = c.oid
      JOIN pg_namespace n ON c.relnamespace = n.oid
      WHERE n.nspname = t.table_schema
        AND c.relname = t.table_name
  )
"""
GET_SEQUENCES_QUERY = "SELECT data.get_sequences()"


def get_default_user(connection: Connection) -> dict:
    """Get the default user."""
    return execute_query(connection, GET_DEFAULT_USER_QUERY)


async def get_default_user_async(connection: AsyncConnection) -> dict:
    """Get the default user asynchronously."""
    return await execute_query_async(connection, GET_DEFAULT_USER_QUERY)


def get_default_user_id(connection: Connection) -> UUID:
    """Get the default user ID."""
    return execute_query(connection, GET_DEFAULT_USER_ID_QUERY)


async def get_default_user_id_async(connection: AsyncConnection) -> UUID:
    """Get the default user ID asynchronously."""
    return await execute_query_async(connection, GET_DEFAULT_USER_ID_QUERY)


def get_mimir_version(connection: Connection) -> str:
    """Get the Mimir version."""
    return execute_query(connection, GET_MIMIR_VERSION_QUERY)


async def get_mimir_version_async(connection: AsyncConnection) -> str:
    """Get the Mimir version asynchronously."""
    return await execute_query_async(connection, GET_MIMIR_VERSION_QUERY)


def dump_database_to_json_fast(
    connection: Connection, include_base: bool = True, include_audit: bool = True
) -> dict[str, Any]:
    """Dump the entire database as JSON in one PostgreSQL call."""
    params = {"include_base": include_base, "include_audit": include_audit}
    return execute_query(connection, DUMP_DATABASE_TO_JSON_QUERY, **params)


async def dump_database_to_json_fast_async(
    connection: AsyncConnection, include_base: bool = True, include_audit: bool = True
) -> dict[str, Any]:
    """Dump the entire database as JSON in one PostgreSQL call, asynchronously."""
    params = {"include_base": include_base, "include_audit": include_audit}
    return await execute_query_async(connection, DUMP_DATABASE_TO_JSON_QUERY, **params)


def _schemas_to_include(include_base: bool, include_audit: bool) -> list[str]:
    """Return the schemas to dump. The data schema is always included."""
    schemas = ["data"]
    if include_base:
        schemas.append("base")
    if include_audit:
        schemas.append("audit")
    return schemas


def _table_rows_query(schema: str, table: str) -> sql.Composed:
    """Build a query that returns one jsonb object per row."""
    return sql.SQL("SELECT to_jsonb(t) FROM {}.{} AS t").format(
        sql.Identifier(schema), sql.Identifier(table)
    )


def dump_database_to_json_slow(
    connection: Connection, include_base: bool = True, include_audit: bool = True
) -> dict[str, Any]:
    """
    Dump the database as JSON, one table at a time.

    Matches ``base.dump_database_to_json``, but loads each row separately so
    PostgreSQL never builds one jsonb array for a whole table. Used when the
    fast dump hits PostgreSQL's jsonb size limit, for example project rows
    that store base64 images.

    Args:
        connection: Database connection.
        include_base: Include tables from the base schema.
        include_audit: Include tables from the audit schema.

    Returns:
        Dump object with database_name, version, timestamp, one key per
        schema.table, and sequences.

    """
    return _assemble_dump(
        _fetch_dump_parts(connection, include_base=include_base, include_audit=include_audit)
    )


async def dump_database_to_json_slow_async(
    connection: AsyncConnection, include_base: bool = True, include_audit: bool = True
) -> dict[str, Any]:
    """
    Dump the database as JSON asynchronously, one table at a time.

    See ``dump_database_to_json_slow``.

    Args:
        connection: Database connection.
        include_base: Include tables from the base schema.
        include_audit: Include tables from the audit schema.

    Returns:
        Dump object with database_name, version, timestamp, one key per
        schema.table, and sequences.

    """
    return _assemble_dump(
        await _fetch_dump_parts_async(
            connection, include_base=include_base, include_audit=include_audit
        )
    )


def _fetch_dump_parts(
    connection: Connection, include_base: bool, include_audit: bool
) -> tuple[dict[str, Any], list[tuple[str, list[Any]]], Any]:
    """Read dump metadata, table rows, and sequences."""
    schemas = _schemas_to_include(include_base, include_audit)
    with connection.cursor() as cur:
        cur.execute(DUMP_METADATA_QUERY)
        metadata = cur.fetchone()[0]

        cur.execute(DUMP_TABLES_QUERY, {"schemas": schemas})
        tables = cur.fetchall()

        table_rows: list[tuple[str, list[Any]]] = []
        for schema, table in tables:
            key = f"{schema}.{table}"
            logging.info("Dumping table %s", key)
            cur.execute(_table_rows_query(schema, table))
            table_rows.append((key, [row[0] for row in cur.fetchall()]))

        cur.execute(GET_SEQUENCES_QUERY)
        sequences = cur.fetchone()[0]

    return metadata, table_rows, sequences


async def _fetch_dump_parts_async(
    connection: AsyncConnection, include_base: bool, include_audit: bool
) -> tuple[dict[str, Any], list[tuple[str, list[Any]]], Any]:
    """Read dump metadata, table rows, and sequences asynchronously."""
    schemas = _schemas_to_include(include_base, include_audit)
    async with connection.cursor() as cur:
        await cur.execute(DUMP_METADATA_QUERY)
        metadata = (await cur.fetchone())[0]

        await cur.execute(DUMP_TABLES_QUERY, {"schemas": schemas})
        tables = await cur.fetchall()

        table_rows: list[tuple[str, list[Any]]] = []
        for schema, table in tables:
            key = f"{schema}.{table}"
            logging.info("Dumping table %s", key)
            await cur.execute(_table_rows_query(schema, table))
            table_rows.append((key, [row[0] for row in await cur.fetchall()]))

        await cur.execute(GET_SEQUENCES_QUERY)
        sequences = (await cur.fetchone())[0]

    return metadata, table_rows, sequences


def _assemble_dump(
    parts: tuple[dict[str, Any], list[tuple[str, list[Any]]], Any],
) -> dict[str, Any]:
    """Combine metadata, per-table rows, and sequences into one dump object."""
    metadata, table_rows, sequences = parts
    return {**metadata, **dict(table_rows), "sequences": sequences}


def dump_database_to_json(
    connection: Connection, include_base: bool = True, include_audit: bool = True
) -> dict[str, Any]:
    """
    Dump the entire database as JSON.

    Tries the PostgreSQL dump function first. When that hits PostgreSQL's jsonb
    size limit, rolls back the failed statement and dumps each row separately.

    Args:
        connection: Database connection.
        include_base: Include tables from the base schema.
        include_audit: Include tables from the audit schema.

    Returns:
        Dump object with database_name, version, timestamp, one key per
        schema.table, and sequences.

    """
    try:
        return dump_database_to_json_fast(connection, include_base, include_audit)
    except ProgramLimitExceeded:
        logging.warning("Database dump exceeded the jsonb size limit; dumping row by row")
        connection.rollback()
        return dump_database_to_json_slow(connection, include_base, include_audit)


async def dump_database_to_json_async(
    connection: AsyncConnection, include_base: bool = True, include_audit: bool = True
) -> dict[str, Any]:
    """
    Dump the entire database as JSON asynchronously.

    See ``dump_database_to_json``.

    Args:
        connection: Database connection.
        include_base: Include tables from the base schema.
        include_audit: Include tables from the audit schema.

    Returns:
        Dump object with database_name, version, timestamp, one key per
        schema.table, and sequences.

    """
    try:
        return await dump_database_to_json_fast_async(connection, include_base, include_audit)
    except ProgramLimitExceeded:
        logging.warning("Database dump exceeded the jsonb size limit; dumping row by row")
        await connection.rollback()
        return await dump_database_to_json_slow_async(connection, include_base, include_audit)


def load_table(
    connection: Connection, table_name: str, data: list[dict], update_action_by: bool = False
) -> None:
    """Load JSON data into a table."""
    params = {
        "table_name": table_name,
        "data": json.dumps(data),
        "update_action_by": update_action_by,
    }
    execute_query(connection, LOAD_JSON_TO_TABLE_QUERY, **params, return_result=False)


async def load_table_async(
    connection: AsyncConnection, table_name: str, data: list[dict], update_action_by: bool = False
) -> None:
    """Load JSON data into a table asynchronously."""
    params = {
        "table_name": table_name,
        "data": json.dumps(data),
        "update_action_by": update_action_by,
    }
    await execute_query_async(connection, LOAD_JSON_TO_TABLE_QUERY, **params, return_result=False)
