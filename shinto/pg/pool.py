"""Connection pool module, a wrapper around psycopg_pool ConnectionPool and AsyncConnectionPool."""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING

import psycopg_pool

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import AsyncGenerator, Generator

    from shinto.pg.connection import AsyncConnection, Connection


class ConnectionPool(psycopg_pool.ConnectionPool):
    """
    ConnectionPool class.

    Example:
        >>> pool = shinto.pg.ConnectionPool(
        ...     min_size=1,
        ...     max_size=10,
        ...     kwargs={
        ...         "host": "localhost",
        ...         "port": 6432,
        ...         "database": "mydb",
        ...         "user": "myuser",
        ...         "password": "mypass",
        ...     },
        ... )
        >>> with pool.connection() as conn:
        ...     conn.execute_query("SELECT * FROM mytable")

    """

    @contextmanager
    def connection(self, timeout: float | None = None) -> Generator[Connection, None, None]:
        """
        Context manager to obtain a connection from the pool.

        Yields a custom Connection object that extends psycopg.Connection.

        Args:
            timeout (float | None): The maximum time to wait for a connection.

        Yields:
            Connection: A connection to the database.

        """
        with super().connection(timeout) as conn:
            yield conn


class AsyncConnectionPool(psycopg_pool.AsyncConnectionPool):
    """
    AsyncConnectionPool class.

    Example:
        >>> pool = shinto.pg.AsyncConnectionPool(
        ...     min_size=1,
        ...     max_size=10,
        ...     kwargs={
        ...         "host": "localhost",
        ...         "port": 6432,
        ...         "dbname": "mydb",
        ...         "user": "myuser",
        ...         "password": "mypass",
        ...     },
        ... )
        >>> async with pool.connection() as conn:
        ...     await conn.execute_query("SELECT * FROM mytable")

    """

    @asynccontextmanager
    async def connection(
        self,
        timeout: float | None = None,  # noqa: ASYNC109, RUF100: Use `asyncio.timeout` instead. Not applicable for overriding method.
    ) -> AsyncGenerator[AsyncConnection, None, None]:
        """
        Context manager to obtain an async connection from the pool.

        Yields a custom AsyncConnection object that extends psycopg.AsyncConnection.

        Args:
            timeout (float | None): The maximum time to wait for a connection.

        Yields:
            AsyncConnection: A connection to the database.

        """
        async with super().connection(timeout) as conn:
            yield conn
