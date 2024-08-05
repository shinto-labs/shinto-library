"""Utility functions for the shinto.pg package."""

import logging


def get_json_object_from_query_result(query_result: list[tuple]) -> dict | list | None:
    """Get json from the query result."""
    if len(query_result) == 0 or len(query_result[0]) == 0:
        logging.error("Query result is empty.")
        return None

    first_element = query_result[0][0]

    if not isinstance(first_element, dict | list):
        logging.error(
            "Query result is not a valid json object. Found type: %s", type(first_element)
        )
        return None

    if len(query_result) > 1 or len(query_result[0]) > 1:
        logging.warning(
            "Query result contains multiple objects, only the first object will be returned."
        )

    return first_element
