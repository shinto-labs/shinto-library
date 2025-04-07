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

    def execute_command(self, query: str, params: None | dict[str:Any] = None) -> int:
        """
        Execute a command (INSERT, UPDATE, DELETE) that doesn't return data.

        Args:
            query (str): The command to execute.
            params (dict): The query parameters to format the command.

        Returns:
            int: The number of rows affected.

        Raises:
            psycopg.Error: If the command execution fails.

        Example:
            >>> conn.execute_command("DELETE FROM table WHERE id = %(id)s", {"id": 1})
            1

        """
        with self.cursor() as cur:
            try:
                cur.execute(query, params)
                self.commit()
            except psycopg.Error:
                self.rollback()
                raise
            else:
                return cur.rowcount

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
            try:
                cur.executemany(query, records, returning=False)
                self.commit()
            except psycopg.Error:
                self.rollback()
                raise
            finally:
                cur.execute("DEALLOCATE ALL")
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

    async def execute_command(self, query: str, params: None | dict[str:Any] = None) -> int:
        """
        Execute a command (INSERT, UPDATE, DELETE) that doesn't return data asynchronously.

        Args:
            query (str): The command to execute.
            params (dict): The query parameters to format the command.

        Returns:
            int: The number of rows affected.

        Raises:
            psycopg.Error: If the command execution fails.

        Example:
            >>> await conn.execute_command("DELETE FROM table WHERE id = %(id)s", {"id": 1})
            1

        """
        async with self.cursor() as cur:
            try:
                await cur.execute(query, params)
                await self.commit()
            except psycopg.Error:
                await self.rollback()
                raise
            else:
                return cur.rowcount

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
            try:
                await cur.executemany(query, records, returning=False)
                await self.commit()
            except psycopg.Error:
                await self.rollback()
                raise
            finally:
                await cur.execute("DEALLOCATE ALL")
            return cur.rowcount
