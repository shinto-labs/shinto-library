# integration_tests/database_dump.py

"""Integration tests for the database JSON dump."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import psycopg
from psycopg.errors import ProgramLimitExceeded

from shinto.mimir.base import (
    dump_database_to_json,
    dump_database_to_json_fast,
    dump_database_to_json_slow,
    get_default_user_id,
)

if TYPE_CHECKING:
    from shinto.pg.connection import Connection

# Each project value stays under PostgreSQL's 256MB jsonb limit.
# Together they exceed the 268435455 byte jsonb array limit.
PAYLOAD_BYTES = 140_000_000
SIZE_LIMIT_ROWS = 2
EQUIVALENCE_MARKER = "dump_equivalence"
SIZE_LIMIT_MARKER = "dump_size_limit"

INSERT_PROJECT_QUERY = """
INSERT INTO data.project (timestamp, action, action_by, data)
VALUES (
    clock_timestamp(),
    'created'::base.record_action,
    %(action_by)s,
    %(data)s::jsonb
)
"""
INSERT_LARGE_PROJECT_QUERY = """
INSERT INTO data.project (timestamp, action, action_by, data)
VALUES (
    clock_timestamp(),
    'created'::base.record_action,
    %(action_by)s,
    jsonb_build_object(
        'marker', %(marker)s::text,
        'internal_description', repeat('A', %(payload_bytes)s::integer)
    )
)
"""
DELETE_MARKED_PROJECTS_QUERY = """
DELETE FROM data.project
WHERE data->>'marker' IN (%(equivalence_marker)s, %(size_limit_marker)s)
"""


def _assert(condition: bool, message: str) -> None:
    """Raise AssertionError when a check fails."""
    if not condition:
        raise AssertionError(message)


def _insert_project(conn: Connection, action_by: object, data: dict[str, Any]) -> None:
    """Insert one project row. The insert trigger assigns id and timestamp."""
    conn.execute_command(
        INSERT_PROJECT_QUERY,
        {"action_by": action_by, "data": json.dumps(data)},
    )


def _delete_marked_projects(conn: Connection) -> None:
    """
    Delete projects created by this test.

    Direct deletes are rejected while the project change trigger is enabled.
    """
    conn.rollback()
    conn.execute_command(
        "ALTER TABLE data.project DISABLE TRIGGER project_change_trigger",
        should_commit=False,
    )
    try:
        conn.execute_command(
            DELETE_MARKED_PROJECTS_QUERY,
            {
                "equivalence_marker": EQUIVALENCE_MARKER,
                "size_limit_marker": SIZE_LIMIT_MARKER,
            },
            should_commit=False,
        )
    except psycopg.Error:
        conn.rollback()
        conn.execute_command("ALTER TABLE data.project ENABLE TRIGGER project_change_trigger")
        raise
    else:
        conn.execute_command("ALTER TABLE data.project ENABLE TRIGGER project_change_trigger")


def _assert_dump_shape(dumped: dict[str, Any]) -> None:
    """Check the metadata and table keys shared by both dump implementations."""
    _assert(bool(dumped.get("database_name")), "dump is missing database_name")
    _assert(bool(dumped.get("version")), "dump is missing version")
    _assert("timestamp" in dumped, "dump is missing timestamp")
    _assert(isinstance(dumped.get("sequences"), dict), "sequences should be an object")
    _assert("data.project" in dumped, "dump is missing data.project")


def _describe_dump_difference(fast: dict[str, Any], slow: dict[str, Any]) -> str:
    """Describe the first difference between two dumps."""
    fast_keys = set(fast)
    slow_keys = set(slow)
    if fast_keys != slow_keys:
        return f"dump keys differ: {fast_keys ^ slow_keys}"
    for key in sorted(fast_keys):
        fast_value = fast[key]
        slow_value = slow[key]
        if fast_value == slow_value:
            continue
        if isinstance(fast_value, list) and isinstance(slow_value, list):
            return f"{key} differs (fast {len(fast_value)} rows, slow {len(slow_value)} rows)"
        return f"{key} differs: fast={fast_value!r} slow={slow_value!r}"
    return "dumps differ"


def _assert_fast_and_slow_match(conn: Connection) -> None:
    """Check that the fast and slow dumps are exactly the same."""
    logging.info("Comparing fast and slow database dumps")
    fast = dump_database_to_json_fast(conn)
    slow = dump_database_to_json_slow(conn)
    if fast != slow:
        raise AssertionError(_describe_dump_difference(fast, slow))
    _assert_dump_shape(fast)

    marked = [
        row
        for row in fast["data.project"]
        if isinstance(row.get("data"), dict) and row["data"].get("marker") == EQUIVALENCE_MARKER
    ]
    _assert(len(marked) == 1, f"expected one equivalence project, found {len(marked)}")


def _assert_size_limit_falls_back(conn: Connection, action_by: object) -> None:
    """Check that a dump larger than the jsonb array limit uses the row-by-row path."""
    logging.info(
        "Inserting %s project rows of %s bytes to exceed the jsonb array limit",
        SIZE_LIMIT_ROWS,
        PAYLOAD_BYTES,
    )
    for _ in range(SIZE_LIMIT_ROWS):
        conn.execute_command(
            INSERT_LARGE_PROJECT_QUERY,
            {
                "action_by": action_by,
                "marker": SIZE_LIMIT_MARKER,
                "payload_bytes": PAYLOAD_BYTES,
            },
        )

    logging.info("Expecting the fast dump to hit the jsonb size limit")
    try:
        dump_database_to_json_fast(conn, include_base=False, include_audit=False)
    except ProgramLimitExceeded:
        conn.rollback()
        logging.info("Fast dump raised ProgramLimitExceeded")
    else:
        raise AssertionError("expected the fast dump to exceed the jsonb size limit")

    logging.info("Dumping through the fallback")
    dumped = dump_database_to_json(conn, include_base=False, include_audit=False)
    _assert_dump_shape(dumped)
    marked = [
        row
        for row in dumped["data.project"]
        if isinstance(row.get("data"), dict) and row["data"].get("marker") == SIZE_LIMIT_MARKER
    ]
    _assert(
        len(marked) == SIZE_LIMIT_ROWS,
        f"expected {SIZE_LIMIT_ROWS} large projects, found {len(marked)}",
    )
    for row in marked:
        description = row["data"]["internal_description"]
        _assert(
            len(description) == PAYLOAD_BYTES,
            f"internal_description length {len(description)} != {PAYLOAD_BYTES}",
        )


def run_integration_test(conn: Connection) -> None:
    """Check dump equivalence and the jsonb size-limit fallback."""
    logging.info("Starting database dump integration test")
    action_by = get_default_user_id(conn)
    try:
        _insert_project(conn, action_by, {"marker": EQUIVALENCE_MARKER, "name": "dump-test"})
        _assert_fast_and_slow_match(conn)
        _assert_size_limit_falls_back(conn, action_by)
    finally:
        logging.info("Removing projects created by the database dump test")
        _delete_marked_projects(conn)
    logging.info("Database dump integration test completed")
