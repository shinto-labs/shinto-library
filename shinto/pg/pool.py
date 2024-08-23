"""Connection pool module, a wrapper around psycopg_pool ConnectionPool and AsyncConnectionPool."""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING

import psycopg_pool

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from shinto.pg.connection import AsyncConnection, Connection


class ConnectionPool(psycopg_pool.ConnectionPool):
    """ConnectionPool class."""

    @contextmanager
    def connection(self, timeout: float | None = None) -> Generator[Connection, None, None]:
        """
        Context manager to obtain a connection from the pool.

        Return the connection immediately if available, otherwise wait up to timeout or self.timeout
        seconds and throw PoolTimeout if a connection is not available in time.

        Upon context exit, return the connection to the pool. Apply the normal connection context
        behaviour <with-connection> (commit/rollback the transaction in case of success/error).
        If the connection is no more in working state, replace it with a new one.

        """
        with super().connection(timeout) as conn:
            yield conn


class AsyncConnectionPool(psycopg_pool.AsyncConnectionPool):
    """AsyncConnectionPool class."""

    @asynccontextmanager
    async def connection(
        self,
        timeout: float | None = None,  # noqa: ASYNC109, RUF100 does not make sense for overloading connection method
    ) -> AsyncGenerator[AsyncConnection, None, None]:
        """
        Async context manager to obtain a connection from the pool.

        Return the connection immediately if available, otherwise wait up to timeout or self.timeout
        seconds and throw PoolTimeout if a connection is not available in time.

        Upon context exit, return the connection to the pool. Apply the normal connection context
        behaviour <with-connection> (commit/rollback the transaction in case of success/error).
        If the connection is no more in working state, replace it with a new one.

        """
        async with super().connection(timeout) as conn:
            yield conn
