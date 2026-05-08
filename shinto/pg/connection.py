"""Connection module, a wrapper around psycopg Connection and Async."""

from __future__ import annotations

from typing import Any

import psycopg
import logging
import os

class Connection(psycopg.Connection):
    """Wrapper for a connection to the database."""

    def execute_query(self, query: str, params: None | dict | tuple | list = None) -> list[tuple]:
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

    def execute_command(
        self, query: str, params: None | dict | tuple | list = None, should_commit: bool = True
    ) -> int:
        """
        Execute a command (INSERT, UPDATE, DELETE) that doesn't return data.

        Args:
            query (str): The command to execute.
            params (dict): The query parameters to format the command.
            should_commit (bool): Whether to commit the transaction after execution.

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
                if should_commit:
                    self.commit()
            except psycopg.Error:
                if should_commit:
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

    async def execute_query(self, query: str, params: None | dict | tuple | list = None) -> list[tuple]:
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

    async def execute_command(
        self,
        query: str,
        params: None | dict | tuple | list = None,
        should_commit: bool = True,
    ) -> int:
        """
        Execute a command (INSERT, UPDATE, DELETE) that doesn't return data asynchronously.

        Args:
            query (str): The command to execute.
            params (dict): The query parameters to format the command.
            should_commit (bool): Whether to commit the transaction after execution.

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
                if should_commit:
                    await self.commit()
            except psycopg.Error:
                if should_commit:
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

def get_connection(
        config: dict | None = None,
        host: str = None,
        port: int = None,
        dbname: str = None,
        user: str = None,
        password: str = None
) -> Connection:
    """Get a Database Connection object.
    Config can be passed as a dict or as individual parameters.
    Individual parameters will override config values.
    Environment variables will be used as defaults
    if neither config nor individual parameters are provided.
    example config dict:
    {
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "dbname": "postgres"
    }
    """

    # Start with config values if provided
    params = {
        "host": None,
        "port": None,
        "user": None,
        "dbname": None,
        "password": None,
    }
    if config:
        params["host"] = config.get("host")
        params["port"] = config.get("port")
        params["user"] = config.get("user")
        params["dbname"] = config.get("dbname")
        params["password"] = config.get("password")

    # Override with explicit arguments if provided
    if host is not None:
        params["host"] = host
    if port is not None:
        params["port"] = port
    if user is not None:
        params["user"] = user
    if dbname is not None:
        params["dbname"] = dbname
    if password is not None:
        params["password"] = password

    # Fallback to environment variables or sensible defaults
    params["host"] = params["host"] or os.getenv("PGHOST", "localhost")
    params["port"] = params["port"] or os.getenv("PGPORT", "5432")
    params["user"] = params["user"] or os.getenv("PGUSER", os.getlogin())
    params["dbname"] = params["dbname"] or os.getenv("PGDATABASE", "mimir")
    params["password"] = params["password"] or os.getenv("PGPASSWORD", None)

    # Build connection string (excluding password for logging)
    connect_str = " "
    for key, value in params.items():
        connect_str += f"{key}={value} "

    return Connection.connect(connect_str.strip())
