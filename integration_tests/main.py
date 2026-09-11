# integration_tests/main.py

import logging
from tabnanny import verbose

from shinto import setup_logging
from shinto.pg.connection import get_connection

from qc_pack import run_integration_test as run_qc_pack_integration_test
from schema_package import run_integration_test as run_schema_package_integration_test
from users import run_integration_test as run_users_integration_test

DATABASE_CONFIG = {
    "host": "database",
    "port": 5432,
    "user": "postgres",
    "dbname": "mimir",
}


def main():
    setup_logging(application_name="tests", loglevel=logging.INFO)
    logging.info("Starting integration tests")

    conn = get_connection(DATABASE_CONFIG)
    logging.info(f"Connected to database: {conn}")
    try:
        res = conn.execute_query("SELECT base.mimir_version()")
        logging.info(f"Mimir version: {res[0]}")

        run_users_integration_test(conn)
        run_qc_pack_integration_test(conn)
        run_schema_package_integration_test(conn)

        conn.commit()
    except Exception as e:
        logging.error(f"Error: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

    logging.info("Integration tests completed")


if __name__ == "__main__":
    main()
