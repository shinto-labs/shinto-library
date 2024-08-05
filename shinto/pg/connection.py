"""Connection module, a wrapper around psycopg Connection and Async."""

import logging

import psycopg


class Connection(psycopg.Connection):
    """Wrapper for a connection to the database."""

    conn: psycopg.Connection

    def execute_query(self, query: str) -> list[tuple] | None:
        """Execute a query on the database."""
        try:
            with self.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
        except psycopg.Error:
            logging.exception("Error executing query.")

        return None

    def write_records(self, query: str, records: list[tuple]) -> int:
        """Write data records to the database."""
        try:
            with self.cursor() as cur:
                # TODO: look at copy instead of executemany
                # https://shintolabs.atlassian.net/browse/DOT-422
                cur.executemany(query, records, returning=False)
                affected_rows = cur.rowcount
                self.commit()
        except psycopg.Error:
            logging.exception("Error writing records to database, performing rollback.")
            self.rollback()
            affected_rows = -1

        return affected_rows


class AsyncConnection(psycopg.AsyncConnection):
    """Wrapper for an async connection to the database."""

    async def execute_query(self, query: str) -> list[tuple]:
        """Execute a query on the database."""
        try:
            async with self.cursor() as cur:
                await cur.execute(query)
                return await cur.fetchall()
        except psycopg.Error:
            logging.exception("Error executing query.")

        return None

    async def write_records(self, query: str, records: list[tuple]) -> int:
        """Write data records to the database."""
        try:
            async with self.cursor() as cur:
                # TODO: look at copy instead of executemany
                # https://shintolabs.atlassian.net/browse/DOT-422
                await cur.executemany(query, records, returning=False)
                affected_rows = cur.rowcount
                await self.commit()
        except psycopg.Error:
            logging.exception("Error writing records to database, performing rollback.")
            await self.rollback()
            affected_rows = -1

        return affected_rows
