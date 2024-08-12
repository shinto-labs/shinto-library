"""Connection module, a wrapper around psycopg Connection and Async."""

import psycopg


class Connection(psycopg.Connection):
    """Wrapper for a connection to the database."""

    conn: psycopg.Connection

    def execute_query(self, query: str) -> list[tuple]:
        """
        Execute a query or command to the database.

        Args:
            query (str): The query to execute.

        Returns:
            list[tuple]: The result of the query.

        Raises:
            psycopg.Error: If the query execution fails.

        """
        with self.cursor() as cur:
            cur.execute(query)
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

    async def execute_query(self, query: str) -> list[tuple]:
        """
        Execute a query or command to the database asynchronously.

        Args:
            query (str): The query to execute.

        Returns:
            list[tuple]: The result of the query.

        Raises:
            psycopg.Error: If the query execution fails.

        """
        async with self.cursor() as cur:
            await cur.execute(query)
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
