"""metrics module."""

import logging

from psycopg import connect


def push_metrics(application_name, metric_name, value):
    """Push a metric to a monitoring system."""
    logging.info(
        f"Pushing metric {metric_name} with value {value} for application {application_name}"
    )

    with connect("dbname=metrics") as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO metrics (application_name, metric_name, value) VALUES (%s, %s, %s)",
                (application_name, metric_name, value))

