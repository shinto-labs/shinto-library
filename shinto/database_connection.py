"""Database connection module to handle the database connection and queries."""

import asyncio
import logging
import os
import sys
from abc import ABC, abstractmethod

import psycopg
from psycopg_pool import AsyncConnectionPool, ConnectionPool

from .config import load_config_file


class BaseDatabaseConnection(ABC):
    """BaseDatabaseConnection class to handle the database connection and queries."""

    _pool: ConnectionPool | AsyncConnectionPool = None

    @property
    def is_open(self) -> bool:
        """Check if the database connection pool is open."""
        return not self._pool.closed

    def __init__(
        self,
        database: str | None = None,
        user: str | None = None,
        password: str | None = None,
        host: str | None = None,
        port: int | None = None,
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
            port (int): Database port. Defaults to 6432.
            minconn (int): Minimum number of connections in the connnection pool.
            maxconn (int): Maximum number of connections in the connnection pool.

        Raises:
            ValueError: If any of the required parameters are missing.

        Args can also be provided as environment variables:
        `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGHOST`, `PGPORT`.

        If arguments are provided they will take precedence over the environment variables.

        """
        database = database or os.getenv("PGDATABASE")
        user = user or os.getenv("PGUSER")
        password = password or os.getenv("PGPASSWORD")
        host = host or os.getenv("PGHOST")
        port = port or os.getenv("PGPORT") or 6432

        missing_params = [k for k, v in locals().items() if v is None]
        if len(missing_params) > 0:
            msg = f"Missing required parameters: {missing_params}"
            raise TypeError(msg)

        conninfo = f"dbname={database} user={user} password={password} host={host} port={port}"
        self._setup_connection_pool(minconn, maxconn, conninfo)

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
        params = ["port", "minconn", "maxconn", "database", "user", "password", "host"]

        config = load_config_file(
            file_path=config_filename,
            start_element=start_element,
            keep_none_values=False,
        )

        config = {k: v for k, v in config.items() if k in params}

        return cls(**config)

    @abstractmethod
    def _setup_connection_pool(self, minconn: int, maxconn: int, conninfo: str):
        """Set up the database connection pool and open the pool."""

    @abstractmethod
    def open(self):
        """Open the database connection pool."""

    @abstractmethod
    def close(self):
        """Close the database connection pool."""

    @abstractmethod
    def execute(self, query: str) -> list[tuple]:
        """Execute a query on the database."""

    @abstractmethod
    def write_records(self, query: str, records: list[tuple]) -> int:
        """Write data records to the database."""


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

    def open(self):
        """Open the database connection pool."""
        self._pool.open(wait=True, timeout=30)

    def close(self):
        """Close the database connection pool."""
        self._pool.close()

    def execute(self, query: str) -> list[tuple] | None:
        """Execute a query on the database."""
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

    def write_records(self, query: str, records: list[tuple]) -> int:
        """Write data records to the database."""
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


class AsyncDatabaseConnection(BaseDatabaseConnection):
    """AsyncDatabaseConnection class to handle the database connection and queries."""

    _pool: AsyncConnectionPool = None

    def _setup_connection_pool(self, minconn: int, maxconn: int, conninfo: str):
        if sys.platform.startswith("win"):
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy()
            )  # pragma: no cover

        self._pool = AsyncConnectionPool(
            conninfo=conninfo,
            min_size=minconn,
            max_size=maxconn,
            open=False,
        )

    async def open(self):
        """Open the database connection pool."""
        await self._pool.open(wait=True, timeout=30)

    async def close(self):
        """Close the database connection pool."""
        await self._pool.close()

    async def execute(self, query: str) -> list[tuple]:
        """Execute a query on the database."""
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

    async def write_records(self, query: str, records: list[tuple]) -> int:
        """Write data records to the database."""
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


def get_json_object_from_query_result(query_result: list[tuple]) -> dict | list | None:
    """Get json from the query result."""
    if len(query_result) == 0 or len(query_result[0]) == 0:
        logging.error("Query result is empty.")
        return None

    first_element = query_result[0][0]

    if not isinstance(first_element, dict | list):
        logging.error(
            "Query result is not a valid json object. Found type: %s", type(first_element)
        )
        return None

    if len(query_result) > 1 or len(query_result[0]) > 1:
        logging.warning(
            "Query result contains multiple objects, only the first object will be returned."
        )

    return first_element
