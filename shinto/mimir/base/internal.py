"""Base internal functions for Mimir."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import psycopg
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
# PostgreSQL refuses a jsonb value at or above this size.
JSONB_MAX_BYTES = 268_435_455
# Keep each slow-load batch under the limit. One larger row is still sent alone.
JSONB_BATCH_BYTES = 200_000_000
LOAD_TABLE_COLUMNS_QUERY = """
SELECT column_name,
       CASE
           WHEN data_type = 'ARRAY' THEN udt_name
           WHEN data_type = 'USER-DEFINED' THEN udt_schema || '.' || udt_name
           ELSE data_type
       END AS column_type
FROM information_schema.columns
WHERE table_schema = %(schema)s
  AND table_name = %(table)s
ORDER BY ordinal_position
"""
LOAD_TABLE_PARTITION_QUERY = """
SELECT c.relkind = 'p'
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = %(schema)s
  AND c.relname = %(table)s
"""
CREATE_LOG_PARTITION_QUERY = "SELECT audit.create_log_partition(%(timestamp)s::timestamptz)"


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


def _split_table_name(table_name: str) -> tuple[str, str]:
    """Split ``schema.table`` the way base.load_json_to_table does."""
    if "." in table_name:
        schema, name = table_name.split(".", 1)
        return schema, name
    return "base", table_name


def _json_payload_size(data: list[dict]) -> int:
    """Return the UTF-8 size of data as one JSON array."""
    if not data:
        return len(b"[]")
    separators = 2 * (len(data) - 1)
    row_sizes = sum(len(json.dumps(row).encode()) for row in data)
    return len(b"[]") + separators + row_sizes


def _with_action_by(data: list[dict], columns: list[tuple[str, str]], user_id: UUID) -> list[dict]:
    """Copy rows with action_by set to the shintolabs user, matching the SQL load."""
    if not any(name == "action_by" for name, _column_type in columns):
        columns.append(("action_by", "uuid"))
    user = str(user_id)
    return [{**row, "action_by": user} for row in data]


def _row_batches(rows: list[dict], max_bytes: int = JSONB_BATCH_BYTES) -> list[list[dict]]:
    """Split rows so each batch stays under PostgreSQL's jsonb limit."""
    batches: list[list[dict]] = []
    current: list[dict] = []
    current_size = 0
    for row in rows:
        row_size = len(json.dumps(row).encode())
        if row_size >= JSONB_MAX_BYTES:
            message = (
                f"A single row is {row_size} bytes, above PostgreSQL's jsonb limit "
                f"of {JSONB_MAX_BYTES}"
            )
            raise ValueError(message)
        if current and current_size + row_size >= max_bytes:
            batches.append(current)
            current = []
            current_size = 0
        current.append(row)
        current_size += row_size
    if current:
        batches.append(current)
    return batches


def _qualified_table(schema: str, table: str) -> sql.Composed:
    """Return a quoted schema.table name."""
    return sql.SQL("{}.{}").format(sql.Identifier(schema), sql.Identifier(table))


def _insert_batch_query(schema: str, table: str, columns: list[tuple[str, str]]) -> sql.Composed:
    """Build the batched jsonb_to_recordset insert used by the SQL loader."""
    names = sql.SQL(", ").join(sql.Identifier(name) for name, _column_type in columns)
    column_types = sql.SQL(", ").join(
        sql.SQL("{} {}").format(sql.Identifier(name), sql.SQL(column_type))
        for name, column_type in columns
    )
    return sql.SQL(
        "INSERT INTO {} ({}) SELECT {} FROM jsonb_to_recordset(%(data)s::jsonb) AS t({})"
    ).format(_qualified_table(schema, table), names, names, column_types)


def load_table_fast(
    connection: Connection, table_name: str, data: list[dict], update_action_by: bool = False
) -> None:
    """Load a table by passing all rows to base.load_json_to_table in one call."""
    params = {
        "table_name": table_name,
        "data": json.dumps(data),
        "update_action_by": update_action_by,
    }
    execute_query(connection, LOAD_JSON_TO_TABLE_QUERY, **params, return_result=False)


async def load_table_fast_async(
    connection: AsyncConnection,
    table_name: str,
    data: list[dict],
    update_action_by: bool = False,
) -> None:
    """Load a table asynchronously in one base.load_json_to_table call."""
    params = {
        "table_name": table_name,
        "data": json.dumps(data),
        "update_action_by": update_action_by,
    }
    await execute_query_async(connection, LOAD_JSON_TO_TABLE_QUERY, **params, return_result=False)


def _prepare_rows(
    data: list[dict],
    columns: list[tuple[str, str]],
    user_id: UUID | None,
    update_action_by: bool,
) -> list[dict]:
    """Return the rows to insert, applying action_by when requested."""
    if update_action_by:
        return _with_action_by(data, columns, user_id)
    return data


def _load_table_slow_statements(
    schema: str, table: str, columns: list[tuple[str, str]], is_partitioned: bool
) -> tuple[sql.Composed, sql.Composed, sql.Composed, sql.Composed]:
    """Return clear, disable-triggers, insert, and enable-triggers statements."""
    table_sql = _qualified_table(schema, table)
    if is_partitioned:
        clear = sql.SQL("DELETE FROM {}").format(table_sql)
    else:
        clear = sql.SQL("TRUNCATE TABLE {} CASCADE").format(table_sql)
    disable = sql.SQL("ALTER TABLE {} DISABLE TRIGGER ALL").format(table_sql)
    enable = sql.SQL("ALTER TABLE {} ENABLE TRIGGER ALL").format(table_sql)
    return clear, disable, _insert_batch_query(schema, table, columns), enable


def load_table_slow(
    connection: Connection, table_name: str, data: list[dict], update_action_by: bool = False
) -> None:
    """
    Load a table in batches so no single jsonb value exceeds PostgreSQL's size limit.

    Matches ``base.load_json_to_table``: it clears the table, disables triggers,
    creates audit.log partitions, and optionally rewrites action_by.

    Args:
        connection: Database connection.
        table_name: Target table, as ``schema.table``.
        data: Rows from a database dump.
        update_action_by: Set action_by to the shintolabs user on every row.

    """
    schema, table = _split_table_name(table_name)
    with connection.cursor() as cur:
        cur.execute(LOAD_TABLE_COLUMNS_QUERY, {"schema": schema, "table": table})
        columns = [(name, column_type) for name, column_type in cur.fetchall()]
        if not columns:
            message = f"Table {table_name} has no columns"
            raise ValueError(message)

        user_id = None
        if update_action_by:
            cur.execute(GET_DEFAULT_USER_ID_QUERY)
            user_id = cur.fetchone()[0]
        rows = _prepare_rows(data, columns, user_id, update_action_by)

        if schema == "audit" and table == "log":
            timestamps = {row.get("timestamp") for row in rows if row.get("timestamp")}
            for timestamp in timestamps:
                cur.execute(CREATE_LOG_PARTITION_QUERY, {"timestamp": timestamp})
                cur.fetchone()

        cur.execute(LOAD_TABLE_PARTITION_QUERY, {"schema": schema, "table": table})
        partition_row = cur.fetchone()
        is_partitioned = bool(partition_row and partition_row[0])
        clear, disable, insert, enable = _load_table_slow_statements(
            schema, table, columns, is_partitioned
        )
        cur.execute(clear)
        cur.execute(disable)
        try:
            for batch in _row_batches(rows):
                logging.info("Loading %s rows into %s", len(batch), table_name)
                cur.execute(insert, {"data": json.dumps(batch)})
        finally:
            try:
                cur.execute(enable)
            except psycopg.Error:
                connection.rollback()


async def load_table_slow_async(
    connection: AsyncConnection,
    table_name: str,
    data: list[dict],
    update_action_by: bool = False,
) -> None:
    """
    Load a table asynchronously in batches.

    See ``load_table_slow``.

    Args:
        connection: Database connection.
        table_name: Target table, as ``schema.table``.
        data: Rows from a database dump.
        update_action_by: Set action_by to the shintolabs user on every row.

    """
    schema, table = _split_table_name(table_name)
    async with connection.cursor() as cur:
        await cur.execute(LOAD_TABLE_COLUMNS_QUERY, {"schema": schema, "table": table})
        columns = [(name, column_type) for name, column_type in await cur.fetchall()]
        if not columns:
            message = f"Table {table_name} has no columns"
            raise ValueError(message)

        user_id = None
        if update_action_by:
            await cur.execute(GET_DEFAULT_USER_ID_QUERY)
            user_id = (await cur.fetchone())[0]
        rows = _prepare_rows(data, columns, user_id, update_action_by)

        if schema == "audit" and table == "log":
            timestamps = {row.get("timestamp") for row in rows if row.get("timestamp")}
            for timestamp in timestamps:
                await cur.execute(CREATE_LOG_PARTITION_QUERY, {"timestamp": timestamp})
                await cur.fetchone()

        await cur.execute(LOAD_TABLE_PARTITION_QUERY, {"schema": schema, "table": table})
        partition_row = await cur.fetchone()
        is_partitioned = bool(partition_row and partition_row[0])
        clear, disable, insert, enable = _load_table_slow_statements(
            schema, table, columns, is_partitioned
        )
        await cur.execute(clear)
        await cur.execute(disable)
        try:
            for batch in _row_batches(rows):
                logging.info("Loading %s rows into %s", len(batch), table_name)
                await cur.execute(insert, {"data": json.dumps(batch)})
        finally:
            try:
                await cur.execute(enable)
            except psycopg.Error:
                await connection.rollback()


def load_table(
    connection: Connection, table_name: str, data: list[dict], update_action_by: bool = False
) -> None:
    """
    Load JSON rows into a table.

    Uses one PostgreSQL call when the serialized rows fit in a jsonb value.
    Larger dumps are loaded in batches, chosen from that size without trying
    the single-call load first.

    Args:
        connection: Database connection.
        table_name: Target table, as ``schema.table``.
        data: Rows from a database dump.
        update_action_by: Set action_by to the shintolabs user on every row.

    """
    payload_size = _json_payload_size(data)
    if payload_size >= JSONB_MAX_BYTES:
        logging.info("Table %s JSON is %s bytes; loading in batches", table_name, payload_size)
        load_table_slow(connection, table_name, data, update_action_by)
        return
    load_table_fast(connection, table_name, data, update_action_by)


async def load_table_async(
    connection: AsyncConnection, table_name: str, data: list[dict], update_action_by: bool = False
) -> None:
    """
    Load JSON rows into a table asynchronously.

    See ``load_table``.

    Args:
        connection: Database connection.
        table_name: Target table, as ``schema.table``.
        data: Rows from a database dump.
        update_action_by: Set action_by to the shintolabs user on every row.

    """
    payload_size = _json_payload_size(data)
    if payload_size >= JSONB_MAX_BYTES:
        logging.info("Table %s JSON is %s bytes; loading in batches", table_name, payload_size)
        await load_table_slow_async(connection, table_name, data, update_action_by)
        return
    await load_table_fast_async(connection, table_name, data, update_action_by)
