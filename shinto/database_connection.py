"""Database connection module to handle the database connection and queries."""

import asyncio
import json
import logging
import os
import sys
from typing import List, Tuple

try:
    import jsonschema
    import psycopg
    import psycopg_pool
except ImportError as e:
    raise ImportError("Database module requires shinto['database'] or shinto['all'] extras.") from e

from .config import load_config_file


class DatabaseConnection:
    """DatabaseConnection class to handle the database connection and queries."""

    _pool: psycopg_pool.AsyncConnectionPool = None

    def __init__(
        self,
        minconn: int = None,
        maxconn: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        host: str = None,
        port: int = None,
        use_env: bool = False,
    ):
        """
        Initialize the database class.

        Args:
            minconn: (defaults to 1) Minimum number of connections in the pool.
            maxconn: (defaults to 3) Maximum number of connections in the pool.
            database: Database name.
            user: Database user.
            password: Database password.
            host: Database host.
            port: (defaults to 6432) Database port.
            use_env: Use environment variables for connection parameters.

        Env variables can be provided as: `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGHOST`, `PGPORT`.
        If arguments are provided, they take precedence over environment variables.

        """
        if sys.platform.startswith("win"):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        if use_env:
            database = database or os.environ.get("PGDATABASE")
            user = user or os.environ.get("PGUSER")
            password = password or os.environ.get("PGPASSWORD")
            host = host or os.environ.get("PGHOST")
            port = port or os.environ.get("PGPORT")

        port = port or 6432
        minconn = minconn or 1
        maxconn = maxconn or 3

        conninfo = f"dbname={database} user={user} password={password} host={host} port={port}"

        self._pool = psycopg_pool.AsyncConnectionPool(
            conninfo=conninfo, min_size=minconn, max_size=maxconn, open=False
        )

    async def connect(self):
        """Open the database connection pool."""
        await self._pool.open()

    async def disconnect(self):
        """Close the database connection pool."""
        await self._pool.close()

    async def execute_query(self, query: str, **kwargs) -> List[Tuple]:
        """Execute a query on the database."""
        data = None

        try:
            async with self._pool.connection() as conn:
                async with conn.cursor() as cur:
                    try:
                        await cur.execute(query, **kwargs)
                        data = await cur.fetchall()
                    except psycopg.Error as e:
                        logging.error("Error executing query: %s", str(e))
        except psycopg.OperationalError as e:
            logging.error("Error setting up database connection: %s", str(e))

        return data

    async def write_records(self, query: str, records: List[Tuple]) -> bool:
        """Write data records to the database."""
        try:
            async with self._pool.connection() as conn:
                async with conn.cursor() as cur:
                    try:
                        await cur.execute(query, records)
                        await conn.commit()
                        return True
                    except psycopg.Error as e:
                        logging.error(
                            "Performing rollback, " + "Error writing records to database: %s",
                            str(e),
                        )
                        await conn.rollback()
                        return False
        except psycopg.Error as e:
            logging.error("Error setting up database connection: %s", str(e))
            return False

    async def execute_json_query(
        self, query: str, schema_filenames: List[str] = None
    ) -> Tuple[object, bool]:
        """Execute a query and validate the result against json schemas if provided."""
        json_object = None
        schema_filenames = schema_filenames or []

        data = await self.execute_query(query)
        if (
            data is not None
            and isinstance(data, list)
            and len(data) == 1
            and isinstance(data[0], Tuple)
            and len(data[0]) == 1
        ):
            json_object = data[0][0]
        else:
            logging.error("Query did not return a single object")
            return (None, False)

        if len(schema_filenames) > 0:
            validate_ok = await self.validate_json_against_schemas(json_object, schema_filenames)
        else:
            validate_ok = True

        return (json_object, validate_ok)

    async def validate_json_against_schemas(self, data: object, schema_filenames: List[str]):
        """Validate a json object against schemas."""
        validate_ok = True
        tasks = []

        loop = asyncio.get_event_loop()

        for schema_filename in schema_filenames:
            schema_filename = os.path.abspath(schema_filename)

            with open(schema_filename, encoding="UTF-8") as file:
                schema = json.load(file)
                task = loop.run_in_executor(None, jsonschema.validate, data, schema)
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result, schema_filename in zip(results, schema_filenames):
            if isinstance(result, Exception):
                if isinstance(result, jsonschema.SchemaError):
                    logging.error("JSON schema error in %s: %s", schema_filename, str(result))
                elif isinstance(result, jsonschema.ValidationError):
                    logging.error("JSON validation error in %s: %s", schema_filename, str(result))
                validate_ok = False

        return validate_ok


def database_connection_from_config(
    config_filename: str, start_element: List[str] = None
) -> DatabaseConnection:
    """
    Create a database connection from a configuration file.

    Args:
        config_filename: Path to the configuration file.
        start_element: Path to the database connection parameters in the configuration file.
        Should be used if the connection parameters are not at the root level of the config file.

    The configuration file should have the following parameters:
        minconn: Minimum number of connections in the pool.
        maxconn: Maximum number of connections in the pool.
        database: Database name.
        user: Username.
        password: Password.
        host: Hostname.
        port: Port number.

    """
    required_params = {
        "minconn": None,
        "maxconn": None,
        "database": None,
        "user": None,
        "password": None,
        "host": None,
        "port": None,
    }

    config = load_config_file(
        config_filename, required_params=required_params, start_element=start_element
    )

    return DatabaseConnection(**config)
