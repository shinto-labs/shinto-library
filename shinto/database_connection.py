"""Database connection module to handle the database connection and queries."""

import asyncio
import json
import logging
import os
import sys
from abc import ABC, abstractmethod

try:
    import jsonschema
    import psycopg
    import psycopg_pool
except ImportError as e:
    raise ImportError("Database module requires shinto['database'] or shinto['all'] extras.") from e

from .config import load_config_file


class BaseDatabaseConnection(ABC):
    """BaseDatabaseConnection class to handle the database connection and queries."""

    def __init__(
        self,
        minconn: int = None,
        maxconn: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        host: str = None,
        port: int = None,
        use_env: bool = False,
    ):
        """
        Initialize the database class.

        Args:
            minconn: (defaults to 1) Minimum number of connections in the pool.
            maxconn: (defaults to 3) Maximum number of connections in the pool.
            database: Database name.
            user: Database user.
            password: Database password.
            host: Database host.
            port: (defaults to 6432) Database port.
            use_env: Use environment variables for connection parameters.

        Env variables can be provided as: `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGHOST`, `PGPORT`.
        If arguments are provided, they take precedence over environment variables.

        """
        if use_env:
            database = database or os.environ.get("PGDATABASE")
            user = user or os.environ.get("PGUSER")
            password = password or os.environ.get("PGPASSWORD")
            host = host or os.environ.get("PGHOST")
            port = port or os.environ.get("PGPORT")

        port = port or 6432
        minconn = minconn or 1
        maxconn = maxconn or 3

        missing_params = [param for param, value in locals().items() if value is None]
        if missing_params:
            raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")

        conninfo = f"dbname={database} user={user} password={password} host={host} port={port}"
        self._setup_connection_pool(minconn, maxconn, conninfo)

    @abstractmethod
    def _setup_connection_pool(self, minconn: int, maxconn: int, conninfo: str):
        """Set up the database connection pool."""
        pass

    @abstractmethod
    def connect(self):
        """Open the database connection pool."""
        pass

    @abstractmethod
    def disconnect(self):
        """Close the database connection pool."""
        pass

    @abstractmethod
    def execute_query(self, query: str) -> list[tuple]:
        """Execute a query on the database."""
        pass

    @abstractmethod
    def write_records(self, query: str, records: list[tuple]) -> int:
        """Write data records to the database."""
        pass

    @abstractmethod
    def execute_json_query(
        self,
        query: str,
        schema_filenames: list[str] = None,
    ) -> tuple[object, bool]:
        """Execute a query and validate the result against json schemas if provided."""
        pass

    @abstractmethod
    def validate_json_against_schemas(self, data: object, schema_filenames: list[str]):
        """Validate a json object against schemas."""
        pass


class DatabaseConnection(BaseDatabaseConnection):
    """DatabaseConnection class to handle the database connection and queries."""

    _pool: psycopg_pool.ConnectionPool = None

    def _setup_connection_pool(self, minconn: int, maxconn: int, conninfo: str):
        self._pool = psycopg_pool.ConnectionPool(
            conninfo=conninfo, min_size=minconn, max_size=maxconn, open=False
        )

    def connect(self):  # noqa: D102, inherit doc string
        self._pool.open()

    def disconnect(self):  # noqa: D102, inherit doc string
        self._pool.close()

    def execute_query(self, query: str) -> list[tuple]:  # noqa: D102, inherit doc string
        data = None

        try:
            with self._pool.connection() as conn, conn.cursor() as cur:
                try:
                    cur.execute(query)
                    data = cur.fetchall()
                except psycopg.Error as e:
                    logging.error("Error executing query: %s", str(e))
        except psycopg.OperationalError as e:
            logging.error("Error setting up database connection: %s", str(e))

        return data

    def write_records(self, query: str, records: list[tuple]) -> int:  # noqa: D102, inherit doc string
        try:
            with self._pool.connection() as conn, conn.cursor() as cur:
                try:
                    cur.executemany(query, records)
                    affected_rows = cur.affected_rows
                    conn.commit()
                except psycopg.Error as e:
                    logging.error(
                        "Performing rollback, " + "Error writing records to database: %s",
                        str(e),
                    )
                    conn.rollback()
                    affected_rows = -1
        except psycopg.Error as e:
            logging.error("Error setting up database connection: %s", str(e))
            affected_rows = -2

        return affected_rows

    async def execute_json_query(  # noqa: D102, inherit doc string
        self, query: str, schema_filenames: list[str] = None
    ) -> tuple[object, bool]:
        json_object = None
        schema_filenames = schema_filenames or []

        data = await self.execute_query(query)
        if (
            data is not None
            and isinstance(data, list)
            and len(data) == 1
            and isinstance(data[0], tuple)
            and len(data[0]) == 1
        ):
            json_object = data[0][0]
        else:
            logging.error("Query did not return a single object")
            return (None, False)

        if len(schema_filenames) > 0:
            validate_ok = await self.validate_json_against_schemas(json_object, schema_filenames)
        else:
            validate_ok = True

        return (json_object, validate_ok)

    async def validate_json_against_schemas(self, data: object, schema_filenames: list[str]):  # noqa: D102, inherit doc string
        validate_ok = True
        tasks = []

        loop = asyncio.get_event_loop()

        for schema_filename in schema_filenames:
            schema_filename = os.path.abspath(schema_filename)

            with open(schema_filename, encoding="UTF-8") as file:
                schema = json.load(file)
                task = loop.run_in_executor(None, jsonschema.validate, data, schema)
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result, schema_filename in zip(results, schema_filenames):
            if isinstance(result, Exception):
                if isinstance(result, jsonschema.SchemaError):
                    logging.error("JSON schema error in %s: %s", schema_filename, str(result))
                elif isinstance(result, jsonschema.ValidationError):
                    logging.error("JSON validation error in %s: %s", schema_filename, str(result))
                validate_ok = False

        return validate_ok


class AsyncDatabaseConnection(BaseDatabaseConnection):
    """AsyncDatabaseConnection class to handle the database connection and queries."""

    _pool: psycopg_pool.AsyncConnectionPool = None

    def _setup_connection_pool(self, minconn: int, maxconn: int, conninfo: str):
        if sys.platform.startswith("win"):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        self._pool = psycopg_pool.AsyncConnectionPool(
            conninfo=conninfo, min_size=minconn, max_size=maxconn, open=False
        )

    async def connect(self):  # noqa: D102, inherit doc string
        await self._pool.open()

    async def disconnect(self):  # noqa: D102, inherit doc string
        await self._pool.close()

    async def execute_query(self, query: str) -> list[tuple]:  # noqa: D102, inherit doc string
        data = None

        try:
            async with self._pool.connection() as conn, conn.cursor() as cur:
                try:
                    await cur.execute(query)
                    data = await cur.fetchall()
                except psycopg.Error as e:
                    logging.error("Error executing query: %s", str(e))
        except psycopg.OperationalError as e:
            logging.error("Error setting up database connection: %s", str(e))

        return data

    async def write_records(self, query: str, records: list[tuple]) -> int:  # noqa: D102, inherit doc string
        try:
            async with self._pool.connection() as conn, conn.cursor() as cur:
                try:
                    await cur.executemany(query, records)
                    affected_rows = cur.affected_rows
                    await conn.commit()
                except psycopg.Error as e:
                    logging.error(
                        "Performing rollback, " + "Error writing records to database: %s",
                        str(e),
                    )
                    await conn.rollback()
                    affected_rows = -1
        except psycopg.Error as e:
            logging.error("Error setting up database connection: %s", str(e))
            affected_rows = -2

        return affected_rows

    async def execute_json_query(  # noqa: D102, inherit doc string
        self, query: str, schema_filenames: list[str] = None
    ) -> tuple[object, bool]:
        json_object = None
        schema_filenames = schema_filenames or []

        data = await self.execute_query(query)
        if (
            data is not None
            and isinstance(data, list)
            and len(data) == 1
            and isinstance(data[0], tuple)
            and len(data[0]) == 1
        ):
            json_object = data[0][0]
        else:
            logging.error("Query did not return a single object")
            return (None, False)

        if len(schema_filenames) > 0:
            validate_ok = await self.validate_json_against_schemas(json_object, schema_filenames)
        else:
            validate_ok = True

        return (json_object, validate_ok)

    async def validate_json_against_schemas(self, data: object, schema_filenames: list[str]):  # noqa: D102, inherit doc string
        validate_ok = True
        tasks = []

        loop = asyncio.get_event_loop()

        for schema_filename in schema_filenames:
            schema_filename = os.path.abspath(schema_filename)

            with open(schema_filename, encoding="UTF-8") as file:
                schema = json.load(file)
                task = loop.run_in_executor(None, jsonschema.validate, data, schema)
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result, schema_filename in zip(results, schema_filenames):
            if isinstance(result, Exception):
                if isinstance(result, jsonschema.SchemaError):
                    logging.error("JSON schema error in %s: %s", schema_filename, str(result))
                elif isinstance(result, jsonschema.ValidationError):
                    logging.error("JSON validation error in %s: %s", schema_filename, str(result))
                validate_ok = False

        return validate_ok


def database_connection_from_config(
    config_filename: str, start_element: list[str] = None, async_conn: bool = False
) -> DatabaseConnection | AsyncDatabaseConnection:
    """
    Create a database connection from a configuration file.

    Args:
        config_filename: Path to the configuration file.
        start_element: Path to the database connection parameters in the configuration file.
        Should be used if the connection parameters are not at the root level of the config file.
        async_conn: Use async database connection.

    The configuration file should have the following parameters:
        minconn: Minimum number of connections in the pool.
        maxconn: Maximum number of connections in the pool.
        database: Database name.
        user: Username.
        password: Password.
        host: Hostname.
        port: Port number.

    """
    required_params = {
        "minconn": None,
        "maxconn": None,
        "database": None,
        "user": None,
        "password": None,
        "host": None,
        "port": None,
    }

    config = load_config_file(
        config_filename, required_params=required_params, start_element=start_element
    )

    if not async_conn:
        return DatabaseConnection(**config)
    else:
        return AsyncDatabaseConnection(**config)
