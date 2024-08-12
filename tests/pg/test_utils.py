"""Test utilities for the pg module."""

import unittest

from shinto.pg.utils import (
    EmptyQueryResultError,
    InvalidJsonError,
    MultipleObjectsReturnedError,
    parse_json_from_query_result,
)


class TestUtilsModule(unittest.TestCase):
    """Tests for the DatabaseConnection module."""

    def test_get_json_object_from_query_result_valid_json(self):
        """Test get_json_object_from_query_result with valid JSON object."""
        parse_json_from_query_result([({"key": "value"},)])

    def test_get_json_object_from_query_result_non_json(self):
        """Test get_json_object_from_query_result with non-JSON object."""
        with self.assertRaises(InvalidJsonError):
            parse_json_from_query_result([(123,)])

    def test_get_json_object_from_query_result_empty(self):
        """Test get_json_object_from_query_result with empty query result."""
        with self.assertRaises(EmptyQueryResultError):
            parse_json_from_query_result([])

    def test_get_json_object_from_query_result_multiple_objects(self):
        """Test get_json_object_from_query_result with multiple objects."""
        json_obj = {"key": "value"}
        with self.assertRaises(MultipleObjectsReturnedError):
            parse_json_from_query_result([(json_obj,), ({"another_key": "another_value"},)])


if __name__ == "__main__":
    unittest.main()
