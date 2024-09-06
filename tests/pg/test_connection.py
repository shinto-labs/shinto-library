"""Test the connection module."""

import unittest
from unittest.mock import AsyncMock, MagicMock

import psycopg

from shinto.pg import AsyncConnection, Connection


class TestConnection(unittest.TestCase):
    """Test the Connection class."""

    def test_execute_query_success(self):
        """Test execute_query method with a successful query."""
        test_query = "SELECT * FROM test_table"
        expected_data = [("row1",), ("row2",)]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = expected_data
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        result = Connection.execute_query(mock_conn, test_query)

        self.assertEqual(result, expected_data)
        mock_cursor.execute.assert_called_once_with(test_query, None)
        mock_cursor.fetchall.assert_called_once()

    def test_execute_query_failure(self):
        """Test execute_query method with a failed query."""
        test_query = "SELECT * FROM test_table"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg.Error
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with self.assertRaises(psycopg.Error):
            Connection.execute_query(mock_conn, test_query)

        mock_cursor.execute.assert_called_once_with(test_query, None)
        mock_cursor.fetchall.assert_not_called()

    def test_write_records_success(self):
        """Test write_records method with successful record insertion."""
        test_query = "INSERT INTO test_table (col1, col2) VALUES (%s, %s)"
        test_records = [("value1", "value2"), ("value3", "value4")]
        expected_rowcount = len(test_records)

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = expected_rowcount
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        result = Connection.write_records(mock_conn, test_query, test_records)

        self.assertEqual(result, expected_rowcount)
        mock_cursor.executemany.assert_called_once_with(test_query, test_records, returning=False)

    def test_write_records_failure(self):
        """Test write_records method with a failed record insertion."""
        test_query = "INSERT INTO test_table (col1, col2) VALUES (%s, %s)"
        test_records = [("value1", "value2"), ("value3", "value4")]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.executemany.side_effect = psycopg.Error
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with self.assertRaises(psycopg.Error):
            Connection.write_records(mock_conn, test_query, test_records)

        mock_cursor.executemany.assert_called_once_with(test_query, test_records, returning=False)


class TestAsyncConnection(unittest.IsolatedAsyncioTestCase):
    """Test the AsyncConnection class."""

    async def test_execute_query_success(self):
        """Test execute_query method with a successful query."""
        test_query = "SELECT * FROM test_table"
        expected_data = [("row1",), ("row2",)]

        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.execute = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=expected_data)
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__aexit__.return_value = None

        result = await AsyncConnection.execute_query(mock_conn, test_query)

        self.assertEqual(result, expected_data)
        mock_cursor.execute.assert_called_once_with(test_query, None)
        mock_cursor.fetchall.assert_called_once()

    async def test_execute_query_failure(self):
        """Test execute_query method with a failed query."""
        test_query = "SELECT * FROM test_table"

        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.execute = AsyncMock(side_effect=psycopg.Error)
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__aexit__.return_value = None

        with self.assertRaises(psycopg.Error):
            await AsyncConnection.execute_query(mock_conn, test_query)

        mock_cursor.execute.assert_called_once_with(test_query, None)
        mock_cursor.fetchall.assert_not_called()

    async def test_write_records_success(self):
        """Test write_records method with successful record insertion."""
        test_query = "INSERT INTO test_table (col1, col2) VALUES (%s, %s)"
        test_records = [("value1", "value2"), ("value3", "value4")]
        expected_rowcount = len(test_records)

        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.executemany.return_value = test_records
        mock_cursor.rowcount = 2
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__aexit__.return_value = None

        result = await AsyncConnection.write_records(mock_conn, test_query, test_records)

        self.assertEqual(result, expected_rowcount)
        mock_cursor.executemany.assert_called_once_with(test_query, test_records, returning=False)

    async def test_write_records_failure(self):
        """Test write_records method with a failed record insertion."""
        test_query = "INSERT INTO test_table (col1, col2) VALUES (%s, %s)"
        test_records = [("value1", "value2"), ("value3", "value4")]

        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.executemany.side_effect = psycopg.Error
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__aexit__.return_value = None

        with self.assertRaises(psycopg.Error):
            await AsyncConnection.write_records(mock_conn, test_query, test_records)

        mock_cursor.executemany.assert_called_once_with(test_query, test_records, returning=False)


if __name__ == "__main__":
    unittest.main()
