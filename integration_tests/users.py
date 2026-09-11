# integration_tests/main.py

import logging
from datetime import datetime, timedelta
from shinto.mimir.base import get_user_list, get_default_user_id, create_user_pending, get_user_pending_list

DATABASE_CONFIG = {
        "host": "database",
        "port": 5432,
        "user": "postgres",
        "dbname": "mimir"
    }


def check_user_pending(conn, default_user_id):
    users = get_user_list(conn, action_by=default_user_id)
    logging.info(f"Found {len(users)} users")
    users_pending = get_user_pending_list(conn, action_by=default_user_id)
    logging.info(f"Found {len(users_pending)} pending users")
    return users, users_pending


def run_integration_test(conn):
    logging.info("Clearing user pending table")
    conn.execute_command("TRUNCATE TABLE base.user_pending CASCADE")

    logging.info("Starting users integration test")
    DEFAULT_USER_ID = get_default_user_id(conn)

    _,_ = check_user_pending(conn, DEFAULT_USER_ID)

    logging.info(f"Adding pending user for email test@example.com")
    create_user_pending(conn, action_by=DEFAULT_USER_ID, email="test@example.com", expires_at=datetime.now() + timedelta(days=1))

    _,_ = check_user_pending(conn, DEFAULT_USER_ID)

    logging.info("Integration tests completed")


if __name__ == "__main__":
    main()