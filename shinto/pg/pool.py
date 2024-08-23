"""Connection pool module, a wrapper around psycopg_pool ConnectionPool and AsyncConnectionPool."""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING

import psycopg_pool

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import AsyncGenerator, Generator

    from shinto.pg.connection import AsyncConnection, Connection


class ConnectionPool(psycopg_pool.ConnectionPool):
    """ConnectionPool class."""

    @contextmanager
    def connection(self, timeout: float | None = None) -> Generator[Connection, None, None]:  # noqa: D102, inherit docstring from base method
        with super().connection(timeout) as conn:
            yield conn


class AsyncConnectionPool(psycopg_pool.AsyncConnectionPool):
    """AsyncConnectionPool class."""

    @asynccontextmanager
    async def connection(  # noqa: D102, inherit docrstring from base method
        self,
        timeout: float | None = None,  # noqa: ASYNC109, RUF100 does not make sense for overloading connection method
    ) -> AsyncGenerator[AsyncConnection, None, None]:
        async with super().connection(timeout) as conn:
            yield conn
