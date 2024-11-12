"""Test the ConnectionPool and AsyncConnectionPool classes."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from shinto.pg import AsyncConnectionPool, ConnectionPool


class TestConnectionPool(unittest.TestCase):
    """Test the ConnectionPool class."""

    @patch("shinto.pg.pool.psycopg_pool.ConnectionPool.__init__", return_value=None)
    @patch("shinto.pg.pool.psycopg_pool.ConnectionPool.connection")
    @patch("shinto.pg.pool.Connection")
    def test_connection_context_manager(
        self,
        mock_connection: MagicMock,
        mock_super_connection: MagicMock,
        mock_connection_pool: MagicMock,
    ):
        """Test the connection context manager."""
        mock_psycopg_conn = MagicMock()
        mock_super_connection.return_value.__enter__.return_value = mock_psycopg_conn
        mock_shinto_conn = MagicMock()
        mock_connection.return_value = mock_shinto_conn

        pool = ConnectionPool()

        with pool.connection() as conn:
            self.assertEqual(conn, mock_shinto_conn)

        mock_connection_pool.assert_called_once()
        mock_super_connection.assert_called_once()
        mock_super_connection.return_value.__enter__.assert_called_once()
        mock_connection.assert_called_once_with(
            mock_psycopg_conn.pgconn, mock_psycopg_conn.row_factory
        )


class TestAsyncConnectionPool(unittest.IsolatedAsyncioTestCase):
    """Test the AsyncConnectionPool class."""

    @patch("shinto.pg.pool.psycopg_pool.AsyncConnectionPool.__init__", return_value=None)
    @patch("shinto.pg.pool.psycopg_pool.AsyncConnectionPool.connection")
    @patch("shinto.pg.pool.AsyncConnection")
    async def test_connection_context_manager(
        self,
        mock_connection: AsyncMock,
        mock_super_connection: AsyncMock,
        mock_connection_pool: MagicMock,
    ):
        """Test the connection context manager."""
        mock_psycopg_conn = AsyncMock()
        mock_super_connection.return_value.__aenter__.return_value = mock_psycopg_conn
        mock_shinto_conn = AsyncMock()
        mock_connection.return_value = mock_shinto_conn

        pool = AsyncConnectionPool()

        async with pool.connection() as conn:
            self.assertEqual(conn, mock_shinto_conn)

        mock_connection_pool.assert_called_once()
        mock_super_connection.assert_called_once()
        mock_super_connection.return_value.__aenter__.assert_called_once()
        mock_connection.assert_called_once_with(
            mock_psycopg_conn.pgconn, mock_psycopg_conn.row_factory
        )


if __name__ == "__main__":
    unittest.main()
