"""Tests for the Database Connection module."""

import os
import unittest
from abc import ABC, abstractmethod
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import psycopg

from shinto.database_connection import AsyncDatabaseConnection, DatabaseConnection

test_config = {
    "database": "test_db",
    "user": "test_user",
    "password": "test_password",
    "host": "test_host",
}


class BaseTestDatabaseConnection(ABC):
    """Base class for database connection tests."""

    @abstractmethod
    def test_database_creation(self):
        """Test the creation of a database connection."""

    @abstractmethod
    def test_database_creation_invalid_params(self):
        """Test the creation of a database connection with invalid params."""

    @abstractmethod
    def test_database_creation_from_config(self):
        """Test the creation of a database connection from a config file."""

    @abstractmethod
    def test_database_creation_from_env_vars(self):
        """Test the creation of a database connection from environment variables."""

    @abstractmethod
    def test_open(self):
        """Test open method and state of the datbase connection."""

    @abstractmethod
    def test_close(self):
        """Test close method and state of the database connection."""

    @abstractmethod
    def test_execute_query(self):
        """Test the execution of a query."""

    @abstractmethod
    def test_execute_query_error(self):
        """Test the execution of a query with an error."""

    @abstractmethod
    def test_execute_query_connection_error(self):
        """Test the execution of a query with a connection error."""

    @abstractmethod
    def test_write_records(self):
        """Test the writing of records to the database."""

    @abstractmethod
    def test_write_records_error(self):
        """Test the writing of records to the database with an error."""

    @abstractmethod
    def test_write_records_connection_error(self):
        """Test the writing of records to the database with a connection error."""

    @abstractmethod
    def test_execute_json_query(self):
        """Test the execution of a JSON query."""

    @abstractmethod
    def test_execute_json_query_error(self):
        """Test the execution of a JSON query with multiple returned values."""

    @abstractmethod
    def test_execute_json_query_with_validate_files(self):
        """Test the execution of a JSON query with validation."""

    @abstractmethod
    def test_execute_json_query_with_validate_files_fail(self):
        """Test the execution of a JSON query with validation failure."""


class TestDatabaseConnection(BaseTestDatabaseConnection, unittest.TestCase):
    """Tests for the DatabaseConnection module."""

    db: DatabaseConnection = None
    mock_pool: MagicMock = None

    @classmethod
    @patch("shinto.database_connection.ConnectionPool")
    def setUpClass(cls, mock_pool: MagicMock):
        cls.mock_pool = MagicMock()
        mock_pool.return_value = cls.mock_pool
        cls.db = DatabaseConnection(**test_config)

    def test_database_creation(self):
        self.assertIsInstance(self.db, DatabaseConnection)

    def test_database_creation_invalid_params(self):
        with self.assertRaises(TypeError):
            DatabaseConnection()

        with self.assertRaises(TypeError):
            DatabaseConnection(None, None, None, None)

    @patch("shinto.database_connection.load_config_file")
    def test_database_creation_from_config(self, mock_load_config: MagicMock):
        mock_load_config.return_value = test_config
        db = DatabaseConnection.from_config_file("test_config.yaml")
        self.assertIsInstance(db, DatabaseConnection)

    @patch.dict(
        os.environ,
        {
            "PGDATABASE": test_config["database"],
            "PGUSER": test_config["user"],
            "PGPASSWORD": test_config["password"],
            "PGHOST": test_config["host"],
            "PGPORT": "6432",
        },
    )
    def test_database_creation_from_env_vars(self):
        db = DatabaseConnection.from_environment_variables()
        self.assertIsInstance(db, DatabaseConnection)

    def test_open(self):
        type(self.mock_pool).closed = PropertyMock(return_value=False)
        self.mock_pool.open = AsyncMock()

        self.db.open()

        self.mock_pool.open.assert_called_once()
        self.assertTrue(self.db.is_open)

    def test_close(self):
        type(self.mock_pool).closed = PropertyMock(return_value=True)
        self.mock_pool.close = AsyncMock()

        self.db.close()

        self.mock_pool.close.assert_called_once()
        self.assertFalse(self.db.is_open)

    def test_execute_query(self):
        test_query = "SELECT * FROM test_table"
        expected_data = [("row1",), ("row2",)]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = expected_data
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        self.mock_pool.connection.return_value = mock_conn

        result = self.db.execute_query(test_query)

        mock_cursor.execute.assert_called_once_with(test_query)
        mock_cursor.fetchall.assert_called_once()
        self.assertEqual(result, expected_data)

    def test_execute_query_error(self):
        test_query = "SELECT * FROM test_table"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg.Error("Test execution error")
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        self.mock_pool.connection.return_value = mock_conn

        result = self.db.execute_query(test_query)

        mock_cursor.execute.assert_called_once_with(test_query)
        mock_cursor.fetchall.assert_not_called()
        self.assertIsNone(result)

    def test_execute_query_connection_error(self):
        test_query = "SELECT * FROM test_table"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.side_effect = psycopg.OperationalError("Test server error")
        self.mock_pool.connection.return_value = mock_conn

        result = self.db.execute_query(test_query)

        mock_cursor.execute.assert_not_called()
        mock_cursor.fetchall.assert_not_called()
        self.assertIsNone(result)

    def test_write_records(self):
        test_query = "INSERT INTO test_table VALUES (%s, %s)"
        test_data = [("row1", "value1"), ("row2", "value2")]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        self.mock_pool.connection.return_value = mock_conn
        mock_cursor.rowcount = 2

        result = self.db.write_records(test_query, test_data)

        mock_cursor.executemany.assert_called_once_with(test_query, test_data, returning=False)
        mock_conn.commit.assert_called_once()
        self.assertIsInstance(result, int)
        self.assertEqual(result, 2)

    def test_write_records_error(self):
        test_query = "INSERT INTO test_table VALUES (%s, %s)"
        test_data = [("row1", "value1"), ("row2", "value2")]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        self.mock_pool.connection.return_value = mock_conn
        mock_cursor.executemany.side_effect = psycopg.Error("Test execution error")

        result = self.db.write_records(test_query, test_data)

        mock_cursor.executemany.assert_called_once_with(test_query, test_data, returning=False)
        mock_conn.rollback.assert_called_once()
        self.assertEqual(result, -1)

    def test_write_records_connection_error(self):
        test_query = "INSERT INTO test_table VALUES (%s, %s)"
        test_data = [("row1", "value1"), ("row2", "value2")]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        self.mock_pool.connection.return_value = mock_conn
        mock_conn.__enter__.side_effect = psycopg.OperationalError("Test server error")

        result = self.db.write_records(test_query, test_data)

        self.assertEqual(result, -2)

    @patch("shinto.database_connection.DatabaseConnection.execute_query")
    def test_execute_json_query(self, mock_execute_query: MagicMock):
        test_query = "SELECT * FROM test_table"
        expected_data = [({"key": "value1"},)]

        mock_execute_query.return_value = expected_data

        result, validate_ok = self.db.execute_json_query(test_query)

        self.assertEqual(result, expected_data[0][0])
        self.assertTrue(validate_ok)

    @patch("shinto.database_connection.DatabaseConnection.execute_query")
    def test_execute_json_query_error(self, mock_execute_query: MagicMock):
        test_query = "SELECT * FROM test_table"
        expected_data = [({"key": "value1"},), ({"key": "value2"},)]

        mock_execute_query.return_value = expected_data

        result, validate_ok = self.db.execute_json_query(test_query)

        self.assertIsNone(result)
        self.assertFalse(validate_ok)

    @patch("shinto.database_connection.validate_json_against_schemas")
    @patch("shinto.database_connection.DatabaseConnection.execute_query")
    def test_execute_json_query_with_validate_files(
        self,
        mock_execute_query: MagicMock,
        mock_validate: MagicMock,
    ):
        test_query = "SELECT * FROM test_table"
        expected_data = [({"key": "value1"},)]

        mock_execute_query.return_value = expected_data
        mock_validate.return_value = True

        result, validate_ok = self.db.execute_json_query(test_query, ["test_schema.json"])

        self.assertEqual(result, expected_data[0][0])
        self.assertTrue(validate_ok)

    @patch("shinto.database_connection.validate_json_against_schemas")
    @patch("shinto.database_connection.DatabaseConnection.execute_query")
    def test_execute_json_query_with_validate_files_fail(
        self,
        mock_execute_query: MagicMock,
        mock_validate: MagicMock,
    ):
        test_query = "SELECT * FROM test_table"
        expected_data = [({"key": "value1"},)]

        mock_execute_query.return_value = expected_data
        mock_validate.return_value = False

        result, validate_ok = self.db.execute_json_query(test_query, ["test_schema.json"])

        self.assertEqual(result, expected_data[0][0])
        self.assertFalse(validate_ok)


class TestAsyncDatabaseConnection(unittest.IsolatedAsyncioTestCase):
    """Tests for the AsyncDatabaseConnection class."""

    db: AsyncDatabaseConnection = None
    mock_pool: MagicMock = None

    @classmethod
    @patch("shinto.database_connection.AsyncConnectionPool")
    def setUpClass(cls, mock_async_pool: MagicMock):
        cls.mock_pool = MagicMock()
        mock_async_pool.return_value = cls.mock_pool
        cls.db = AsyncDatabaseConnection(**test_config)

    def tearDown(self):
        self.mock_pool.reset_mock()
        self.mock_pool.connection.return_value.__aenter__.side_effect = None

    def test_database_creation(self):
        self.assertIsInstance(self.db, AsyncDatabaseConnection)

    def test_database_creation_invalid_params(self):
        with self.assertRaises(TypeError):
            AsyncDatabaseConnection()

        with self.assertRaises(TypeError):
            AsyncDatabaseConnection(None, None, None, None)

    @patch("shinto.database_connection.load_config_file")
    def test_database_creation_from_config(self, mock_load_config: MagicMock):
        mock_load_config.return_value = test_config
        db = AsyncDatabaseConnection.from_config_file("test_config.yaml")
        self.assertIsInstance(db, AsyncDatabaseConnection)

    @patch.dict(
        os.environ,
        {
            "PGDATABASE": test_config["database"],
            "PGUSER": test_config["user"],
            "PGPASSWORD": test_config["password"],
            "PGHOST": test_config["host"],
            "PGPORT": "6432",
        },
    )
    def test_database_creation_from_env_vars(self):
        db = AsyncDatabaseConnection.from_environment_variables()
        self.assertIsInstance(db, AsyncDatabaseConnection)

    async def test_open(self):
        type(self.mock_pool).closed = PropertyMock(return_value=False)
        self.mock_pool.open = AsyncMock()

        await self.db.open()

        self.mock_pool.open.assert_awaited_once()
        self.assertTrue(self.db.is_open)

    async def test_close(self):
        type(self.mock_pool).closed = PropertyMock(return_value=True)
        self.mock_pool.close = AsyncMock()

        await self.db.close()

        self.mock_pool.close.assert_awaited_once()
        self.assertFalse(self.db.is_open)

    async def test_execute_query(self):
        test_query = "SELECT * FROM test_table"
        expected_data = [("row1",), ("row2",)]

        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.execute = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=expected_data)
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__aexit__.return_value = None
        self.mock_pool.connection.return_value.__aenter__.return_value = mock_conn
        self.mock_pool.connection.return_value.__aexit__.return_value = None

        result = await self.db.execute_query(test_query)

        mock_cursor.execute.assert_awaited_once_with(test_query)
        mock_cursor.fetchall.assert_awaited_once()
        self.assertEqual(result, expected_data)

    async def test_execute_query_error(self):
        test_query = "SELECT * FROM test_table"

        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.execute = AsyncMock(side_effect=psycopg.Error("Test execution error"))
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__aexit__.return_value = None
        self.mock_pool.connection.return_value.__aenter__.return_value = mock_conn
        self.mock_pool.connection.return_value.__aexit__.return_value = None

        result = await self.db.execute_query(test_query)

        mock_cursor.execute.assert_called_once_with(test_query)
        mock_cursor.fetchall.assert_not_awaited()
        self.assertIsNone(result)

    async def test_execute_query_connection_error(self):
        test_query = "SELECT * FROM test_table"

        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__aexit__.return_value = None
        self.mock_pool.connection.return_value.__aenter__.return_value = mock_conn
        self.mock_pool.connection.return_value.__aexit__.return_value = None
        self.mock_pool.connection.return_value.__aenter__.side_effect = psycopg.OperationalError(
            "Test server error",
        )

        result = await self.db.execute_query(test_query)

        mock_cursor.execute.assert_not_awaited()
        mock_cursor.fetchall.assert_not_awaited()
        self.assertIsNone(result)

    async def test_write_records(self):
        test_query = "INSERT INTO test_table VALUES (%s, %s)"
        test_data = [("row1", "value1"), ("row2", "value2")]

        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.executemany.return_value = test_data
        mock_cursor.rowcount = 2
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__aexit__.return_value = None
        mock_conn.commit = AsyncMock()
        self.mock_pool.connection.return_value.__aenter__.return_value = mock_conn
        self.mock_pool.connection.return_value.__aexit__.return_value = None

        result = await self.db.write_records(test_query, test_data)

        mock_cursor.executemany.assert_awaited_once_with(test_query, test_data, returning=False)
        mock_conn.commit.assert_awaited_once()
        self.assertIsInstance(result, int)
        self.assertEqual(result, 2)

    async def test_write_records_error(self):
        test_query = "INSERT INTO test_table VALUES (%s, %s)"
        test_data = [("row1", "value1"), ("row2", "value2")]

        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.executemany.side_effect = psycopg.Error("Test execution error")
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__aexit__.return_value = None
        mock_conn.rollback = AsyncMock()
        self.mock_pool.connection.return_value.__aenter__.return_value = mock_conn
        self.mock_pool.connection.return_value.__aexit__.return_value = None

        result = await self.db.write_records(test_query, test_data)

        mock_cursor.executemany.assert_awaited_once_with(test_query, test_data, returning=False)
        mock_conn.rollback.assert_awaited_once()
        self.assertEqual(result, -1)

    async def test_write_records_connection_error(self):
        test_query = "INSERT INTO test_table VALUES (%s, %s)"
        test_data = [("row1", "value1"), ("row2", "value2")]

        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__aexit__.return_value = None
        self.mock_pool.connection.return_value.__aenter__.return_value = mock_conn
        self.mock_pool.connection.return_value.__aexit__.return_value = None
        self.mock_pool.connection.return_value.__aenter__.side_effect = psycopg.OperationalError(
            "Test server error",
        )

        result = await self.db.write_records(test_query, test_data)

        self.assertEqual(result, -2)

    @patch("shinto.database_connection.AsyncDatabaseConnection.execute_query")
    async def test_execute_json_query(self, mock_execute_query: AsyncMock):
        test_query = "SELECT * FROM test_table"
        expected_data = [({"key": "value1"},)]

        mock_execute_query.return_value = expected_data

        result, validate_ok = await self.db.execute_json_query(test_query)

        self.assertEqual(result, expected_data[0][0])
        self.assertTrue(validate_ok)

    @patch("shinto.database_connection.AsyncDatabaseConnection.execute_query")
    async def test_execute_json_query_error(self, mock_execute_query: AsyncMock):
        test_query = "SELECT * FROM test_table"
        expected_data = [({"key": "value1"},), ({"key": "value2"},)]

        mock_execute_query.return_value = expected_data

        result, validate_ok = await self.db.execute_json_query(test_query)

        self.assertIsNone(result)
        self.assertFalse(validate_ok)

    @patch("shinto.database_connection.async_validate_json_against_schemas")
    @patch("shinto.database_connection.AsyncDatabaseConnection.execute_query")
    async def test_execute_json_query_with_validate_files(
        self,
        mock_execute_query: AsyncMock,
        mock_validate: AsyncMock,
    ):
        test_query = "SELECT * FROM test_table"
        expected_data = [({"key": "value1"},)]

        mock_execute_query.return_value = expected_data
        mock_validate.return_value = True

        result, validate_ok = await self.db.execute_json_query(test_query, ["test_schema.json"])

        self.assertEqual(result, expected_data[0][0])
        self.assertTrue(validate_ok)

    @patch("shinto.database_connection.async_validate_json_against_schemas")
    @patch("shinto.database_connection.AsyncDatabaseConnection.execute_query")
    async def test_execute_json_query_with_validate_files_fail(
        self,
        mock_execute_query: AsyncMock,
        mock_validate: AsyncMock,
    ):
        test_query = "SELECT * FROM test_table"
        expected_data = [({"key": "value1"},)]

        mock_execute_query.return_value = expected_data
        mock_validate.return_value = False

        result, validate_ok = await self.db.execute_json_query(test_query, ["test_schema.json"])

        self.assertEqual(result, expected_data[0][0])
        self.assertFalse(validate_ok)


if __name__ == "__main__":
    unittest.main()
