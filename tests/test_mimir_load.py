"""Tests for choosing a table load from the JSON size."""

import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from shinto.mimir.base.internal import (
    JSONB_MAX_BYTES,
    _json_payload_size,
    _row_batches,
    load_table,
    load_table_async,
)


class TestJsonPayloadSize(unittest.TestCase):
    """Test the size used to choose the load path."""

    def test_matches_json_dumps(self):
        """The measured size is the UTF-8 size of one JSON array."""
        rows = [{"id": "a", "note": "café"}, {"id": "b"}]
        self.assertEqual(_json_payload_size(rows), len(json.dumps(rows).encode()))

    def test_empty_array(self):
        """An empty row list is a two-byte JSON array."""
        self.assertEqual(_json_payload_size([]), len(b"[]"))


class TestRowBatches(unittest.TestCase):
    """Test splitting rows into jsonb-sized batches."""

    def test_splits_before_the_batch_limit(self):
        """Rows that do not fit together are loaded separately."""
        rows = [{"value": "a" * 30}, {"value": "b" * 30}]
        batches = _row_batches(rows, max_bytes=80)
        self.assertEqual(len(batches), 2)
        self.assertEqual(batches[0], [rows[0]])
        self.assertEqual(batches[1], [rows[1]])

    def test_rejects_a_row_above_the_jsonb_limit(self):
        """A single row larger than PostgreSQL accepts cannot be loaded."""
        with patch("shinto.mimir.base.internal.JSONB_MAX_BYTES", 10), self.assertRaises(ValueError):
            _row_batches([{"value": "too-long"}])


class TestLoadTableDispatch(unittest.TestCase):
    """Test that load_table does not try the fast path for a large payload."""

    def test_small_payload_uses_fast_load(self):
        """A payload under the jsonb limit uses one PostgreSQL call."""
        connection = MagicMock()
        rows = [{"id": "a"}]
        size = patch("shinto.mimir.base.internal._json_payload_size", return_value=10)
        fast_load = patch("shinto.mimir.base.internal.load_table_fast")
        slow_load = patch("shinto.mimir.base.internal.load_table_slow")
        with size, fast_load as fast, slow_load as slow:
            load_table(connection, "data.project", rows, update_action_by=True)

        fast.assert_called_once_with(connection, "data.project", rows, True)
        slow.assert_not_called()

    def test_large_payload_uses_slow_load(self):
        """A payload at the jsonb limit is loaded in batches."""
        connection = MagicMock()
        rows = [{"id": "a"}]
        size = patch(
            "shinto.mimir.base.internal._json_payload_size",
            return_value=JSONB_MAX_BYTES,
        )
        fast_load = patch("shinto.mimir.base.internal.load_table_fast")
        slow_load = patch("shinto.mimir.base.internal.load_table_slow")
        with size, fast_load as fast, slow_load as slow:
            load_table(connection, "data.project", rows)

        slow.assert_called_once_with(connection, "data.project", rows, False)
        fast.assert_not_called()


class TestLoadTableDispatchAsync(unittest.IsolatedAsyncioTestCase):
    """Test the async size decision."""

    async def test_large_payload_uses_slow_load(self):
        """A payload at the jsonb limit is loaded in batches."""
        connection = MagicMock()
        rows = [{"id": "a"}]
        size = patch(
            "shinto.mimir.base.internal._json_payload_size",
            return_value=JSONB_MAX_BYTES,
        )
        fast_load = patch(
            "shinto.mimir.base.internal.load_table_fast_async", new_callable=AsyncMock
        )
        slow_load = patch(
            "shinto.mimir.base.internal.load_table_slow_async", new_callable=AsyncMock
        )
        with size, fast_load as fast, slow_load as slow:
            await load_table_async(connection, "data.project", rows)

        slow.assert_awaited_once_with(connection, "data.project", rows, False)
        fast.assert_not_awaited()
