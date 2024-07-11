"""Test cases for the JSON schema module."""

import asyncio
from itertools import cycle
import json
import random
import unittest
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

from shinto.jsonschema import async_validate_json_against_schemas, validate_json_against_schemas

test_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {"name": {"type": "string"}},
}


class TestJsonSchema(unittest.TestCase):
    """Test cases for the JSON schema module."""

    @patch(
        "shinto.jsonschema.Path.open",
        new_callable=mock_open,
        read_data=json.dumps(test_schema),
    )
    def test_valid_schema(self, _mock_open_file: MagicMock):
        """Test validate_json_against_schemas with valid schema."""
        data = {"name": "John Doe"}
        schema_filenames = ["valid_schema.json"]
        result = validate_json_against_schemas(data, schema_filenames)
        self.assertTrue(result)

    @patch(
        "shinto.jsonschema.Path.open",
        new_callable=mock_open,
        read_data=json.dumps(test_schema).replace("string", "integer"),
    )
    def test_schema_error(self, _mock_open_file: MagicMock):
        """Test validate_json_against_schemas with invalid schema."""
        data = {"name": "John Doe"}
        schema_filenames = ["invalid_schema.json"]
        result = validate_json_against_schemas(data, schema_filenames)
        self.assertFalse(result)

    @patch(
        "shinto.jsonschema.Path.open",
        new_callable=mock_open,
        read_data=json.dumps(test_schema).replace("string", "bad_type"),
    )
    def test_bad_schema_error(self, _mock_open_file: MagicMock):
        """Test validate_json_against_schemas with invalid schema."""
        data = {"name": "John Doe"}
        schema_filenames = ["invalid_schema.json"]
        result = validate_json_against_schemas(data, schema_filenames)
        self.assertFalse(result)


class TestAsyncJsonSchema(unittest.IsolatedAsyncioTestCase):
    """Test cases for the JSON schema module."""

    @patch("shinto.jsonschema.anyio.open_file", new_callable=AsyncMock)
    async def test_valid_schema(self, mock_open_file: AsyncMock):
        """Test validate_json_against_schemas with valid schema."""
        mock_open_file.return_value.__aenter__.return_value.read = AsyncMock(
            return_value=json.dumps(test_schema),
        )

        data = {"name": "John Doe"}
        schema_filenames = ["valid_schema.json"]
        result = await async_validate_json_against_schemas(data, schema_filenames)
        self.assertTrue(result)

    @patch("shinto.jsonschema.anyio.open_file", new_callable=AsyncMock)
    async def test_schema_error(self, mock_open_file: AsyncMock):
        """Test validate_json_against_schemas with invalid schema."""
        mock_open_file.return_value.__aenter__.return_value.read = AsyncMock(
            return_value=json.dumps(test_schema).replace("string", "integer"),
        )

        data = {"name": "John Doe"}
        schema_filenames = ["invalid_schema.json"]
        result = await async_validate_json_against_schemas(data, schema_filenames)
        self.assertFalse(result)

    @patch("shinto.jsonschema.anyio.open_file", new_callable=AsyncMock)
    async def test_multiple_schemas_error(self, mock_open_file: AsyncMock):
        """Test validate_json_against_schemas with invalid schema."""
        delays = cycle([0, 0.2])

        async def mock_read() -> str:
            """Mock read function with simulated delay in file read."""
            await asyncio.sleep(next(delays))
            return json.dumps(test_schema).replace("string", "integer")

        mock_open_file.return_value.__aenter__.return_value.read = AsyncMock(side_effect=mock_read)

        data = {"name": "John Doe"}
        schema_filenames = ["invalid_schema.json"] * 2
        result = await async_validate_json_against_schemas(data, schema_filenames)
        self.assertFalse(result)

    @patch("shinto.jsonschema.anyio.open_file", new_callable=AsyncMock)
    async def test_bad_schema_error(self, mock_open_file: AsyncMock):
        """Test validate_json_against_schemas with invalid schema."""
        mock_open_file.return_value.__aenter__.return_value.read = AsyncMock(
            return_value=json.dumps(test_schema).replace("string", "bad_type"),
        )

        data = {"name": "John Doe"}
        schema_filenames = ["invalid_schema.json"]
        result = await async_validate_json_against_schemas(data, schema_filenames)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
