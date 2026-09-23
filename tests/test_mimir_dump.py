"""Tests for the row-by-row database dump."""

import unittest
from unittest.mock import AsyncMock, MagicMock

from psycopg import sql
from psycopg.errors import ProgramLimitExceeded

from shinto.mimir.base.internal import (
    dump_database_to_json,
    dump_database_to_json_async,
    dump_database_to_json_fast,
    dump_database_to_json_slow,
    dump_database_to_json_slow_async,
)


def _table_query(schema: str, table: str) -> sql.Composed:
    return sql.SQL("SELECT to_jsonb(t) FROM {}.{} AS t").format(
        sql.Identifier(schema), sql.Identifier(table)
    )


class TestDumpDatabaseToJsonSlow(unittest.TestCase):
    """Test dump_database_to_json_slow."""

    def test_assembles_dump_without_aggregating_tables(self):
        """Rows are collected per table and empty tables become an empty list."""
        metadata = {
            "database_name": "mimir",
            "version": "1.5.1",
            "timestamp": "2026-09-23T12:00:00+00:00",
        }
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            (metadata,),
            ({"test_sequence": 3},),
        ]
        mock_cursor.fetchall.side_effect = [
            [("data", "project"), ("data", "empty")],
            [({"id": "a", "description": "image"},)],
            [],
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        result = dump_database_to_json_slow(mock_conn, include_base=False, include_audit=True)

        self.assertEqual(
            result,
            {
                **metadata,
                "data.project": [{"id": "a", "description": "image"}],
                "data.empty": [],
                "sequences": {"test_sequence": 3},
            },
        )
        schemas = mock_cursor.execute.call_args_list[1].args[1]["schemas"]
        self.assertEqual(schemas, ["data", "audit"])
        executed = mock_cursor.execute.call_args_list
        self.assertEqual(executed[2].args[0], _table_query("data", "project"))
        self.assertEqual(executed[3].args[0], _table_query("data", "empty"))

    def test_includes_base_schema_by_default(self):
        """The data and base schemas are included when audit is left out."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [({"database_name": "mimir"},), ({},)]
        mock_cursor.fetchall.side_effect = [[]]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        dump_database_to_json_slow(mock_conn, include_audit=False)

        schemas = mock_cursor.execute.call_args_list[1].args[1]["schemas"]
        self.assertEqual(schemas, ["data", "base"])


class TestDumpDatabaseToJsonSlowAsync(unittest.IsolatedAsyncioTestCase):
    """Test dump_database_to_json_slow_async."""

    async def test_assembles_dump(self):
        """The async dump returns the same document shape."""
        metadata = {"database_name": "mimir", "version": "1.5.1", "timestamp": "ts"}
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.side_effect = [(metadata,), ({"seq": 1},)]
        mock_cursor.fetchall.side_effect = [
            [("base", "user")],
            [({"id": "u"},)],
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

        result = await dump_database_to_json_slow_async(
            mock_conn, include_base=True, include_audit=False
        )

        self.assertEqual(result["base.user"], [{"id": "u"}])
        self.assertEqual(result["sequences"], {"seq": 1})
        schemas = mock_cursor.execute.await_args_list[1].args[1]["schemas"]
        self.assertEqual(schemas, ["data", "base"])


def _cursor_that_blocks_aggregated_dump(metadata: dict) -> MagicMock:
    """Cursor whose aggregated dump raises, and whose row queries succeed."""
    mock_cursor = MagicMock()

    def execute(query: object, *_args: object) -> None:
        if "base.dump_database_to_json" in str(query):
            message = "total size of jsonb array elements exceeds the maximum"
            raise ProgramLimitExceeded(message)

    mock_cursor.execute.side_effect = execute
    mock_cursor.fetchone.side_effect = [(metadata,), ({"seq": 1},)]
    mock_cursor.fetchall.side_effect = [[("data", "project")], [({"id": "a"},)]]
    return mock_cursor


class TestDumpDatabaseToJson(unittest.TestCase):
    """Test dump_database_to_json fallback."""

    def test_returns_fast_dump_when_it_succeeds(self):
        """The aggregated dump is returned when PostgreSQL accepts it."""
        dumped = {"database_name": "mimir", "data.project": [{"id": "a"}]}
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(dumped,)]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = False

        result = dump_database_to_json_fast(mock_conn)

        self.assertEqual(result, dumped)
        self.assertEqual(dump_database_to_json(mock_conn), dumped)
        mock_conn.rollback.assert_not_called()

    def test_falls_back_when_jsonb_size_limit_is_hit(self):
        """A jsonb size-limit error is rolled back and dumped row by row."""
        metadata = {"database_name": "mimir", "version": "1.5.1", "timestamp": "ts"}
        mock_cursor = _cursor_that_blocks_aggregated_dump(metadata)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = False

        result = dump_database_to_json(mock_conn, include_base=False, include_audit=False)

        self.assertEqual(result["data.project"], [{"id": "a"}])
        self.assertEqual(result["sequences"], {"seq": 1})
        mock_conn.rollback.assert_called_once()


class TestDumpDatabaseToJsonAsync(unittest.IsolatedAsyncioTestCase):
    """Test dump_database_to_json_async fallback."""

    async def test_falls_back_when_jsonb_size_limit_is_hit(self):
        """A jsonb size-limit error is rolled back and dumped row by row."""
        metadata = {"database_name": "mimir", "version": "1.5.1", "timestamp": "ts"}
        mock_cursor = AsyncMock()

        def execute(query: object, *_args: object) -> None:
            if "base.dump_database_to_json" in str(query):
                message = "total size of jsonb array elements exceeds the maximum"
                raise ProgramLimitExceeded(message)

        mock_cursor.execute.side_effect = execute
        mock_cursor.fetchone.side_effect = [(metadata,), ({"seq": 1},)]
        mock_cursor.fetchall.side_effect = [[("data", "project")], [({"id": "a"},)]]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__aexit__.return_value = False
        mock_conn.rollback = AsyncMock()

        result = await dump_database_to_json_async(
            mock_conn, include_base=False, include_audit=False
        )

        self.assertEqual(result["data.project"], [{"id": "a"}])
        mock_conn.rollback.assert_awaited_once()
