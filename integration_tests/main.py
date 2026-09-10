# integration_tests/main.py

import logging
from sqlite3 import DatabaseError
from shinto import setup_logging
from shinto.pg.connection import get_connection

from users import run_integration_test as run_users_integration_test

DATABASE_CONFIG = {
        "host": "database",
        "port": 5432,
        "user": "postgres",
        "dbname": "mimir"
    }

def main():
    setup_logging(
        application_name="tests",
        loglevel=logging.INFO)
    logging.info("Starting integration tests")

    conn = get_connection(DATABASE_CONFIG)

    run_users_integration_test(conn)


    logging.info("Integration tests completed")



if __name__ == "__main__":
    main()