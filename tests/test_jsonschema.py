"""Test cases for the JSON schema module."""

import json
import unittest
from unittest.mock import mock_open, patch

from shinto.jsonschema import validate_json_against_schemas

test_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {"name": {"type": "string"}},
}

test_invalid_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {"name": {"type": "integer"}},
}


class TestJsonSchema(unittest.IsolatedAsyncioTestCase):
    """Test cases for the JSON schema module."""

    @patch(
        "shinto.jsonschema.Path.open",
        new_callable=mock_open,
        read_data=json.dumps(test_schema),
    )
    def test_valid_schema(self, mock_file):
        """Test validate_json_against_schemas with valid schema."""
        data = {"name": "John Doe"}
        schema_filenames = ["valid_schema.json"]
        result = validate_json_against_schemas(data, schema_filenames)
        self.assertTrue(result)

    @patch(
        "shinto.jsonschema.Path.open",
        new_callable=mock_open,
        read_data=json.dumps(test_invalid_schema),
    )
    def test_schema_error(self, mock_file):
        """Test validate_json_against_schemas with invalid schema."""
        data = {"name": "John Doe"}
        schema_filenames = ["invalid_schema.json"]
        result = validate_json_against_schemas(data, schema_filenames)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
