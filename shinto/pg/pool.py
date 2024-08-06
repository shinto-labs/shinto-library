"""Connection pool module, a wrapper around psycopg_pool ConnectionPool and AsyncConnectionPool."""

import os
from abc import ABC, abstractmethod

import psycopg_pool

from shinto.config import load_config_file
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
        minconn: int = 1,
        maxconn: int = 3,
    ):
        """
        Initialize the connection pool.

        Args:
            database (str): Database name.
            user (str): Database user.
            password (str): Database password.
            host (str): Database host.
            port (int): Database port. Defaults to 6432.
            minconn (int): Minimum number of connections in the connnection pool.
            maxconn (int): Maximum number of connections in the connnection pool.

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
        self._setup_connection_pool(conninfo, minconn, maxconn)

    @classmethod
    def from_config_file(cls, file_path: str, start_element: list[str] | None = None):  # noqa: ANN206
        """
        Create a connection pool from a configuration file.

        Args:
            file_path (str): Path to the configuration file.
            start_element (list):
                Path to the database connection parameters in the configuration file.
                Should be used when the parameters are nested in the configuration file.

        Database connection parameters are prioritised in the following order:
        ----------------------------------------------------------------------
        1. Environment variables
        2. Configuration file
        3. Default values

        Parameters can be provided as environment variables:
        ---------------------------------------------------
        - `PGDATABASE`
        - `PGUSER`
        - `PGPASSWORD`
        - `PGHOST`
        - `PGPORT`

        Parameters can be provided in the configuration file:
        ----------------------------------------------------
        - `database`
        - `user`
        - `password`
        - `host`
        - `port`: default 6432
        - `minconn`: default 1
        - `maxconn`: default 3

        """
        # Load the database connection parameters from the configuration file
        config = load_config_file(file_path=file_path, start_element=start_element)

        # 1. Get the database connection parameters from environment variables
        # 2. Otherwise use the parameters from the configuration file
        # 3. Otherwise use the default parameters
        host = os.getenv("PGHOST", config.get("host"))
        port = os.getenv("PGPORT", config.get("port", 6432))
        database = os.getenv("PGDATABASE", config.get("database"))
        user = os.getenv("PGUSER", config.get("user"))
        password = os.getenv("PGPASSWORD", config.get("password"))
        minconn = config.get("minconn", 1)
        maxconn = config.get("maxconn", 3)

        # Create the database connection
        return cls(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            minconn=minconn,
            maxconn=maxconn,
        )

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
