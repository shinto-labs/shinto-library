"""Connection pool module, a wrapper around psycopg_pool ConnectionPool and AsyncConnectionPool."""

import os
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

import psycopg_pool

from shinto.pg.connection import AsyncConnection, Connection


class BaseConnectionPool(ABC):
    """BaseConnectionPool class."""

    def __init__(
        self,
        database: str | None = None,
        user: str | None = None,
        password: str | None = None,
        host: str | None = None,
        port: int | str | None = None,
        min_size: int = 1,
        max_size: int = 3,
    ):
        """
        Initialize the connection pool.

        Args:
            database (str): Database name.
            user (str): Database user.
            password (str): Database password.
            host (str): Database host.
            port (int): Database port. Defaults to 6432.
            min_size (int): Minimum number of connections in the connnection pool.
            max_size (int): Maximum number of connections in the connnection pool.

        Raises:
            TypeError: If any of the required parameters are missing.

        Arguments can also be provided as environment variables:
        -------------------------------------------------------
        - `PGDATABASE`
        - `PGUSER`
        - `PGPASSWORD`
        - `PGHOST`
        - `PGPORT`

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
        self._setup_connection_pool(conninfo, min_size, max_size)

    @abstractmethod
    def _setup_connection_pool(self, conninfo: str, min_size: int, max_size: int):
        """
        Initialize the connection pool.

        This method is called during the initialization of the BaseConnectionPool class.

        """


class ConnectionPool(BaseConnectionPool, psycopg_pool.ConnectionPool):
    """ConnectionPool class."""

    def _setup_connection_pool(self, conninfo: str, min_size: int, max_size: int) -> None:
        """
        Initialize the connection pool.

        This method is called during the initialization of the ConnectionPool class.

        """
        psycopg_pool.ConnectionPool.__init__(
            self,
            conninfo=conninfo,
            min_size=min_size,
            max_size=max_size,
            open=False,
            connection_class=Connection,
        )

    @contextmanager
    def connection(self, timeout: float | None = None) -> Generator[Connection | None, None, None]:
        """Context manager for connection pool."""
        with super().connection(timeout) as conn:
            yield conn


class AsyncConnectionPool(BaseConnectionPool, psycopg_pool.AsyncConnectionPool):
    """AsyncConnectionPool class."""

    def _setup_connection_pool(self, conninfo: str, min_size: int, max_size: int):
        """
        Initialize the async connection pool.

        This method is called during the initialization of the AsyncConnectionPool class.

        """
        psycopg_pool.AsyncConnectionPool.__init__(
            self,
            conninfo=conninfo,
            min_size=min_size,
            max_size=max_size,
            open=False,
            connection_class=AsyncConnection,
        )

    @asynccontextmanager
    async def connection(
        self, timeout: float | None = None
    ) -> AsyncGenerator[AsyncConnection | None, None, None]:
        """Async context manager for connection pool."""
        async with super().connection(timeout) as conn:
            yield conn
