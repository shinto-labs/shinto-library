"""Utility functions for the shinto.pg package."""

from __future__ import annotations


class EmptyQueryResultError(Exception):
    """Error raised when the query result is empty."""


class InvalidJsonError(Exception):
    """Error raised when the json object is invalid."""


class MultipleObjectsReturnedError(Exception):
    """Error raised when multiple objects are returned from a query."""


def parse_json_from_query_result(query_result: list[tuple]) -> dict | list:
    """
    Get json from the query result.

    Args:
        query_result (list[tuple]): The query result to parse.

    Returns:
        (dict | list): The parsed json object.

    Raises:
        EmptyQueryResultError: If the query result is empty.
        MultipleObjectsReturnedError: If the query result contains multiple objects.
        JsonParseError: If the query result is not a valid dict or list.

    """
    # TODO: check if this is the correct way to handle this
    # https://shintolabs.atlassian.net/browse/DOT-519
    if len(query_result) == 0 or len(query_result[0]) == 0:
        msg = "Query result is empty."
        raise EmptyQueryResultError(msg)

    first_element = query_result[0][0]

    if len(query_result) > 1 or len(query_result[0]) > 1:
        msg = "Query result contains multiple objects."
        raise MultipleObjectsReturnedError(msg)

    if not isinstance(first_element, dict | list):
        msg = f"Query result is not a valid json object. Found type: {type(first_element)}"
        raise InvalidJsonError(msg)

    return first_element
