"""Test the ConnectionPool and AsyncConnectionPool classes."""

import os
import unittest
from unittest.mock import MagicMock, patch

from shinto.pg import AsyncConnectionPool, ConnectionPool

test_config = {
    "database": "test_db",
    "user": "test_user",
    "password": "test_password",
    "host": "test_host",
    "port": 6432,
}


class TestConnectionPool(unittest.TestCase):
    """Test the ConnectionPool class."""

    def test_pool_creation(self):
        """Test the creation of a connection pool."""
        pool = ConnectionPool(**test_config)
        self.assertIsInstance(pool, ConnectionPool)
        self.assertTrue(pool.closed)

    def test_creation_without_args_failure(self):
        """Test the creation of a connection pool without arguments."""
        with self.assertRaises(TypeError):
            ConnectionPool()

    @patch("shinto.pg.pool.load_config_file")
    def test_pool_creation_from_config(self, mock_load_config: MagicMock):
        """Test the creation of a connection pool from a config file."""
        mock_load_config.return_value = test_config
        pool = ConnectionPool.from_config_file("test_config.yaml")
        self.assertIsInstance(pool, ConnectionPool)
        self.assertTrue(pool.closed)

    @patch.dict(
        os.environ,
        {
            "PGDATABASE": test_config["database"],
            "PGUSER": test_config["user"],
            "PGPASSWORD": test_config["password"],
            "PGHOST": test_config["host"],
            "PGPORT": str(test_config["port"]),
        },
        clear=True,
    )
    def test_pool_creation_from_env_vars(self):
        """Test the creation of a database connection from environment variables."""
        pool = ConnectionPool()
        self.assertIsInstance(pool, ConnectionPool)
        self.assertTrue(pool.closed)

    @patch.dict(
        os.environ,
        {
            "PGDATABASE": test_config["database"] + "_2",
            "PGUSER": test_config["user"] + "_2",
            "PGPASSWORD": test_config["password"] + "_2",
            "PGHOST": test_config["host"] + "_2",
            "PGPORT": str(test_config["port"]),
        },
        clear=True,
    )
    @patch("shinto.pg.pool.load_config_file")
    @patch("shinto.pg.pool.ConnectionPool.__init__", return_value=None)
    def test_pool_creation_from_config_overloaded_with_env_vars(
        self, mock_init: MagicMock, mock_load_config: MagicMock
    ):
        """Test the creation of a connection pool from a config file and environment variables."""
        mock_load_config.return_value = test_config
        ConnectionPool.from_config_file("test_config.yaml")

        mock_init.assert_called_once_with(
            database=os.environ["PGDATABASE"],
            user=os.environ["PGUSER"],
            password=os.environ["PGPASSWORD"],
            host=os.environ["PGHOST"],
            port=os.environ["PGPORT"],
            minconn=1,
            maxconn=3,
        )


class TestAsyncConnectionPool(unittest.IsolatedAsyncioTestCase):
    """Test the AsyncConnectionPool class."""

    def test_pool_creation(self):
        """Test the creation of a connection pool."""
        pool = AsyncConnectionPool(**test_config)
        self.assertIsInstance(pool, AsyncConnectionPool)
        self.assertTrue(pool.closed)

    def test_creation_without_args_failure(self):
        """Test the creation of a connection pool without arguments."""
        with self.assertRaises(TypeError):
            AsyncConnectionPool()

    @patch("shinto.pg.pool.load_config_file")
    def test_pool_creation_from_config(self, mock_load_config: MagicMock):
        """Test the creation of a connection pool from a config file."""
        mock_load_config.return_value = test_config
        pool = AsyncConnectionPool.from_config_file("test_config.yaml")
        self.assertIsInstance(pool, AsyncConnectionPool)
        self.assertTrue(pool.closed)

    @patch.dict(
        os.environ,
        {
            "PGDATABASE": test_config["database"],
            "PGUSER": test_config["user"],
            "PGPASSWORD": test_config["password"],
            "PGHOST": test_config["host"],
            "PGPORT": str(test_config["port"]),
        },
        clear=True,
    )
    def test_pool_creation_from_env_vars(self):
        """Test the creation of a connection pool from environment variables."""
        pool = AsyncConnectionPool()
        self.assertIsInstance(pool, AsyncConnectionPool)
        self.assertTrue(pool.closed)

    @patch.dict(
        os.environ,
        {
            "PGDATABASE": test_config["database"] + "_2",
            "PGUSER": test_config["user"] + "_2",
            "PGPASSWORD": test_config["password"] + "_2",
            "PGHOST": test_config["host"] + "_2",
            "PGPORT": str(test_config["port"]),
        },
        clear=True,
    )
    @patch("shinto.pg.pool.load_config_file")
    @patch("shinto.pg.pool.AsyncConnectionPool.__init__", return_value=None)
    def test_pool_creation_from_config_overloaded_with_env_vars(
        self, mock_init: MagicMock, mock_load_config: MagicMock
    ):
        """Test the creation of a connection pool from a config file and environment variables."""
        mock_load_config.return_value = test_config
        AsyncConnectionPool.from_config_file("test_config.yaml")

        mock_init.assert_called_once_with(
            database=os.environ["PGDATABASE"],
            user=os.environ["PGUSER"],
            password=os.environ["PGPASSWORD"],
            host=os.environ["PGHOST"],
            port=os.environ["PGPORT"],
            minconn=1,
            maxconn=3,
        )


if __name__ == "__main__":
    unittest.main()
