"""Database connection module to handle the database connection and queries."""

import asyncio
import logging
import os
import sys
from abc import ABC, abstractmethod

import psycopg
from psycopg_pool import AsyncConnectionPool, ConnectionPool

from .config import load_config_file
from .jsonschema import async_validate_json_against_schemas, validate_json_against_schemas


class BaseDatabaseConnection(ABC):
    """BaseDatabaseConnection class to handle the database connection and queries."""

    _pool: ConnectionPool | AsyncConnectionPool = None

    def __init__(
        self,
        database: str,
        user: str,
        password: str,
        host: str,
        port: int = 6432,
        minconn: int = 1,
        maxconn: int = 3,
    ):
        """
        Initialize the database connection class.

        Args:
            database (str): Database name.
            user (str): Database user.
            password (str): Database password.
            host (str): Database host.
            port (int): Database port.
            minconn (int): Minimum number of connections in the connnection pool.
            maxconn (int): Maximum number of connections in the connnection pool.

        Raises:
            ValueError: If any of the required parameters are missing.

        """
        missing_params = [k for k, v in locals().items() if v is None]
        if len(missing_params) > 0:
            raise TypeError(f"Missing required parameters: {missing_params}")

        conninfo = f"dbname={database} user={user} password={password} host={host} port={port}"
        self._setup_connection_pool(minconn, maxconn, conninfo)

    @abstractmethod
    def _setup_connection_pool(self, minconn: int, maxconn: int, conninfo: str):
        """Set up the database connection pool and open the pool."""

    @abstractmethod
    def open(self):
        """Open the database connection pool."""

    @abstractmethod
    def close(self):
        """Close the database connection pool."""

    @property
    def is_open(self) -> bool:
        """Check if the database connection pool is open."""
        return not self._pool.closed

    @abstractmethod
    def execute_query(self, query: str) -> list[tuple]:
        """Execute a query on the database."""

    @abstractmethod
    def write_records(self, query: str, records: list[tuple]) -> int:
        """Write data records to the database."""

    @abstractmethod
    def execute_json_query(
        self,
        query: str,
        schema_filenames: list[str] | None = None,
    ) -> tuple[object, bool]:
        """Execute a query and validate the result against json schemas if provided."""

    @classmethod
    def from_config_file(cls, config_filename: str, start_element: list[str] | None = None):  # noqa: ANN206
        """
        Create a database connection from a configuration file.

        Args:
            config_filename (str): Path to the configuration file.
            start_element (list):
                Path to the database connection parameters in the configuration file.
                Should be used when the parameters are nested in the configuration file.

        Required parameters in the configuration file:
        ---------------------------------------------
        - database
        - user
        - password
        - host

        Optional paramers in the configuration file:
        -------------------------------------------
        - port: default 6432
        - minconn: default 1
        - maxconn: default 3

        """
        optional_params = ["port", "minconn", "maxconn"]
        required_params = {
            "database": None,
            "user": None,
            "password": None,
            "host": None,
        }

        config = load_config_file(
            config_filename,
            required_params=required_params,
            start_element=start_element,
        )

        params = {
            k: v
            for k, v in config.items()
            if v is not None and k in [*optional_params, *required_params.keys()]
        }

        return cls(**params)

    @classmethod
    def from_environment_variables(  # noqa: ANN206
        cls,
        database: str | None = None,
        user: str | None = None,
        password: str | None = None,
        host: str | None = None,
        port: int | None = None,
        minconn: int = 1,
        maxconn: int = 3,
    ):
        """
        Create a database connection from environment variables.

        Env variables should be provided as:
        `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGHOST`, `PGPORT`.

        If arguments are provided, they take precedence over environment variables.
        """
        database = database or os.environ.get("PGDATABASE")
        user = user or os.environ.get("PGUSER")
        password = password or os.environ.get("PGPASSWORD")
        host = host or os.environ.get("PGHOST")
        port = port or os.environ.get("PGPORT")

        return cls(
            database=database,
            user=user,
            password=password,
            host=host,
            port=port,
            minconn=minconn,
            maxconn=maxconn,
        )


class DatabaseConnection(BaseDatabaseConnection):
    """DatabaseConnection class to handle the database connection and queries."""

    _pool: ConnectionPool = None

    def _setup_connection_pool(self, minconn: int, maxconn: int, conninfo: str):
        self._pool = ConnectionPool(
            conninfo=conninfo,
            min_size=minconn,
            max_size=maxconn,
            open=False,
        )

    def open(self):  # noqa: D102, inherit doc string
        self._pool.open()

    def close(self):  # noqa: D102, inherit doc string
        self._pool.close()

    def execute_query(self, query: str) -> list[tuple] | None:  # noqa: D102, inherit doc string
        try:
            with self._pool.connection() as conn, conn.cursor() as cur:
                try:
                    cur.execute(query)
                    return cur.fetchall()
                except psycopg.Error:
                    logging.exception("Error executing query.")
        except psycopg.OperationalError:
            logging.exception("Error setting up database connection.")

        return None

    def write_records(self, query: str, records: list[tuple]) -> int:  # noqa: D102, inherit doc string
        try:
            with self._pool.connection() as conn, conn.cursor() as cur:
                try:
                    # TODO: look at copy instead of executemany
                    # https://shintolabs.atlassian.net/browse/DOT-422
                    cur.executemany(query, records, returning=False)
                    affected_rows = cur.rowcount
                    conn.commit()
                except psycopg.Error:
                    logging.exception("Error writing records to database, performing rollback.")
                    conn.rollback()
                    affected_rows = -1
        except psycopg.OperationalError:
            logging.exception("Error setting up database connection.")
            affected_rows = -2

        return affected_rows

    def execute_json_query(  # noqa: D102, inherit doc string
        self,
        query: str,
        schema_filenames: list[str] | None = None,
    ) -> tuple[object, bool]:
        schema_filenames = schema_filenames or []

        data = self.execute_query(query)
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
            validate_ok = validate_json_against_schemas(json_object, schema_filenames)
        else:
            validate_ok = True

        return (json_object, validate_ok)


class AsyncDatabaseConnection(BaseDatabaseConnection):
    """AsyncDatabaseConnection class to handle the database connection and queries."""

    _pool: AsyncConnectionPool = None

    def _setup_connection_pool(self, minconn: int, maxconn: int, conninfo: str):
        if sys.platform.startswith("win"):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        self._pool = AsyncConnectionPool(
            conninfo=conninfo,
            min_size=minconn,
            max_size=maxconn,
            open=False,
        )

    async def open(self):  # noqa: D102, inherit doc string
        await self._pool.open()

    async def close(self):  # noqa: D102, inherit doc string
        await self._pool.close()

    async def execute_query(self, query: str) -> list[tuple]:  # noqa: D102, inherit doc string
        try:
            async with self._pool.connection() as conn, conn.cursor() as cur:
                try:
                    await cur.execute(query)
                    return await cur.fetchall()
                except psycopg.Error:
                    logging.exception("Error executing query.")
        except psycopg.OperationalError:
            logging.exception("Error setting up database connection.")

        return None

    async def write_records(self, query: str, records: list[tuple]) -> int:  # noqa: D102, inherit doc string
        try:
            async with self._pool.connection() as conn, conn.cursor() as cur:
                try:
                    # TODO: look at copy instead of executemany
                    # https://shintolabs.atlassian.net/browse/DOT-422
                    await cur.executemany(query, records, returning=False)
                    affected_rows = cur.rowcount
                    await conn.commit()
                except psycopg.Error:
                    logging.exception("Error writing records to database, performing rollback.")
                    await conn.rollback()
                    affected_rows = -1
        except psycopg.OperationalError:
            logging.exception("Error setting up database connection.")
            affected_rows = -2

        return affected_rows

    async def execute_json_query(  # noqa: D102, inherit doc string
        self,
        query: str,
        schema_filenames: list[str] | None = None,
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
            validate_ok = await async_validate_json_against_schemas(json_object, schema_filenames)
        else:
            validate_ok = True

        return (json_object, validate_ok)
