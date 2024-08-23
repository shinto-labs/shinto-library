"""Test the ConnectionPool and AsyncConnectionPool classes."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import psycopg

from shinto.pg import AsyncConnectionPool, ConnectionPool


class TestConnectionPool(unittest.TestCase):
    """Test the ConnectionPool class."""

    @patch("shinto.pg.pool.psycopg_pool.ConnectionPool.__init__", return_value=None)
    @patch("shinto.pg.pool.psycopg_pool.ConnectionPool.connection")
    def test_connection_context_manager(
        self,
        mock_super_connection: MagicMock,
        mock_connection_pool: MagicMock,
    ):
        """Test the connection context manager."""
        mock_connection = MagicMock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_connection
        mock_super_connection.return_value = mock_context_manager

        pool = ConnectionPool()

        with pool.connection() as conn:
            self.assertEqual(conn, mock_connection)

        mock_super_connection.assert_called_once()
        mock_context_manager.__enter__.assert_called_once()
        mock_connection_pool.assert_called_once()

    @patch("shinto.pg.pool.psycopg_pool.ConnectionPool.__init__", return_value=None)
    @patch("shinto.pg.pool.psycopg_pool.ConnectionPool.connection")
    def test_connection_context_manager_exception(
        self,
        mock_super_connection: MagicMock,
        mock_connection_pool: MagicMock,
    ):
        """Test the connection context manager exception handling."""
        mock_super_connection.side_effect = psycopg.Error

        pool = ConnectionPool()

        with self.assertRaises(psycopg.Error), pool.connection():
            pass

        mock_super_connection.assert_called_once()
        mock_connection_pool.assert_called_once()


class TestAsyncConnectionPool(unittest.IsolatedAsyncioTestCase):
    """Test the AsyncConnectionPool class."""

    @patch("shinto.pg.pool.psycopg_pool.AsyncConnectionPool.__init__", return_value=None)
    @patch("shinto.pg.pool.psycopg_pool.AsyncConnectionPool.connection")
    async def test_connection_context_manager(
        self,
        mock_super_connection: AsyncMock,
        mock_connection_pool: MagicMock,
    ):
        """Test the connection context manager."""
        mock_connection = AsyncMock()
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_connection
        mock_super_connection.return_value = mock_context_manager

        pool = AsyncConnectionPool()

        async with pool.connection() as conn:
            self.assertEqual(conn, mock_connection)

        mock_super_connection.assert_called_once()
        mock_context_manager.__aenter__.assert_called_once()
        mock_connection_pool.assert_called_once()

    @patch("shinto.pg.pool.psycopg_pool.AsyncConnectionPool.__init__", return_value=None)
    @patch("shinto.pg.pool.psycopg_pool.AsyncConnectionPool.connection")
    async def test_connection_context_manager_exception(
        self,
        mock_super_connection: AsyncMock,
        mock_connection_pool: MagicMock,
    ):
        """Test the connection context manager exception handling."""
        mock_super_connection.side_effect = psycopg.Error

        pool = AsyncConnectionPool()

        with self.assertRaises(psycopg.Error):
            async with pool.connection():
                pass

        mock_super_connection.assert_called_once()
        mock_connection_pool.assert_called_once()


if __name__ == "__main__":
    unittest.main()
