"""Connection module, a wrapper around psycopg Connection and Async."""

from __future__ import annotations

from typing import Any

import psycopg


class Connection(psycopg.Connection):
    """Wrapper for a connection to the database."""

    def execute_query(self, query: str, params: None | dict[str:Any] = None) -> list[tuple]:
        """
        Execute a query or command to the database.

        Args:
            query (str): The query to execute.
            params (dict): The query parameters to format the query.

        Returns:
            list[tuple]: The result of the query.

        Raises:
            psycopg.Error: If the query execution fails.

        Example:
            >>> conn.execute_query("SELECT * FROM table WHERE id = %(id)s", {"id": 1})
            [(1, "name")]

        """
        with self.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def write_records(self, query: str, records: list[tuple]) -> int:
        """
        Write data records to the database.

        Args:
            query (str): The query to execute.
            records (list[tuple]): The records to write.

        Returns:
            int: The number of records written.

        Raises:
            psycopg.Error: If the query execution fails.

        """
        with self.cursor() as cur:
            # TODO: look at copy instead of executemany
            # https://shintolabs.atlassian.net/browse/DOT-422
            cur.executemany(query, records, returning=False)
            return cur.rowcount


class AsyncConnection(psycopg.AsyncConnection):
    """Wrapper for an async connection to the database."""

    async def execute_query(self, query: str, params: None | dict[str:Any] = None) -> list[tuple]:
        """
        Execute a query or command to the database asynchronously.

        Args:
            query (str): The query to execute.
            params (dict): The query parameters to format the query.

        Returns:
            list[tuple]: The result of the query.

        Raises:
            psycopg.Error: If the query execution fails.

        Example:
            >>> await conn.execute_query("SELECT * FROM table WHERE id = %(id)s", {"id": 1})
            [(1, "name")]

        """
        async with self.cursor() as cur:
            await cur.execute(query, params)
            return await cur.fetchall()

    async def write_records(self, query: str, records: list[tuple]) -> int:
        """
        Write data records to the database asynchronously.

        Args:
            query (str): The query to execute.
            records (list[tuple]): The records to write.

        Returns:
            int: The number of records written.

        Raises:
            psycopg.Error: If the query execution fails.

        """
        async with self.cursor() as cur:
            # TODO: look at copy instead of executemany
            # https://shintolabs.atlassian.net/browse/DOT-422
            await cur.executemany(query, records, returning=False)
            return cur.rowcount
