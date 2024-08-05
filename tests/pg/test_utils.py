"""Test utilities for the pg module."""

import unittest

from shinto.pg import get_json_object_from_query_result


class TestUtilsModule(unittest.TestCase):
    """Tests for the DatabaseConnection module."""

    def test_get_json_object_from_query_result_empty(self):
        """Test get_json_object_from_query_result with empty query result."""
        result = get_json_object_from_query_result([])
        self.assertIsNone(result)

    def test_get_json_object_from_query_result_non_json(self):
        """Test get_json_object_from_query_result with non-JSON object."""
        with self.assertLogs(level="ERROR") as log:
            result = get_json_object_from_query_result([(123,)])
            self.assertIsNone(result)
            self.assertIn("Query result is not a valid json object.", log.output[0])

    def test_get_json_object_from_query_result_valid_json(self):
        """Test get_json_object_from_query_result with valid JSON object."""
        json_obj = {"key": "value"}
        result = get_json_object_from_query_result([(json_obj,)])
        self.assertEqual(result, json_obj)

    def test_get_json_object_from_query_result_multiple_objects(self):
        """Test get_json_object_from_query_result with multiple objects."""
        json_obj = {"key": "value"}
        with self.assertLogs(level="WARNING") as log:
            result = get_json_object_from_query_result(
                [(json_obj,), ({"another_key": "another_value"},)]
            )
            self.assertEqual(result, json_obj)
            self.assertIn("Query result contains multiple objects", log.output[0])


if __name__ == "__main__":
    unittest.main()
