"""Test cases for the JSON schema module."""

import asyncio
import json
import unittest
from itertools import cycle
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import jsonschema.exceptions

from shinto.jsonschema import validate_json_against_schemas, validate_json_against_schemas_async

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
    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    def test_valid_schema(self, mock_exists: MagicMock, mock_open_file: MagicMock):
        """Test validate_json_against_schemas with valid schema."""
        mock_exists.return_value = True
        data = {"name": "John Doe"}
        schema_filenames = ["valid_schema.json"]
        validate_json_against_schemas(data, schema_filenames)
        mock_exists.assert_called_once_with()
        mock_open_file.assert_called_once_with(encoding="UTF-8")

    @patch(
        "shinto.jsonschema.Path.open",
        new_callable=mock_open,
        read_data=json.dumps(test_schema).replace("string", "integer"),
    )
    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    def test_schema_error(self, mock_exists: MagicMock, mock_open_file: MagicMock):
        """Test validate_json_against_schemas with invalid schema."""
        mock_exists.return_value = True
        data = {"name": "John Doe"}
        schema_filenames = ["invalid_schema.json"]
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            validate_json_against_schemas(data, schema_filenames)
        mock_open_file.assert_called_once_with(encoding="UTF-8")

    @patch(
        "shinto.jsonschema.Path.open",
        new_callable=mock_open,
        read_data=json.dumps(test_schema).replace("string", "bad_type"),
    )
    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    def test_bad_schema_error(self, mock_exists: MagicMock, mock_open_file: MagicMock):
        """Test validate_json_against_schemas with invalid schema."""
        mock_exists.return_value = True
        data = {"name": "John Doe"}
        schema_filenames = ["invalid_schema.json"]
        with self.assertRaises(jsonschema.exceptions.SchemaError):
            validate_json_against_schemas(data, schema_filenames)
        mock_open_file.assert_called_once_with(encoding="UTF-8")

    @patch(
        "shinto.jsonschema.Path.open",
        new_callable=mock_open,
        read_data=json.dumps(test_schema).replace("string", "bad_type"),
    )
    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    def test_non_existing_schema_error(self, mock_exists: MagicMock, mock_open_file: MagicMock):
        """Test validate_json_against_schemas with non-existing schema."""
        mock_exists.return_value = False

        data = {"name": "John Doe"}
        schema_filenames = ["non_existing_schema.json"]
        with self.assertRaises(FileNotFoundError):
            validate_json_against_schemas(data, schema_filenames)
        mock_exists.assert_called_once_with()
        mock_open_file.assert_not_called()


class TestAsyncJsonSchema(unittest.IsolatedAsyncioTestCase):
    """Test cases for the JSON schema module."""

    @patch("shinto.jsonschema.anyio.open_file", new_callable=AsyncMock)
    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    async def test_valid_schema(self, mock_exists: MagicMock, mock_open_file: AsyncMock):
        """Test validate_json_against_schemas with valid schema."""
        mock_open_file.return_value.__aenter__.return_value.read = AsyncMock(
            return_value=json.dumps(test_schema),
        )
        mock_exists.return_value = True

        data = {"name": "John Doe"}
        schema_filenames = ["valid_schema.json"]
        full_path = Path(schema_filenames[0]).resolve()

        await validate_json_against_schemas_async(data, schema_filenames)

        mock_exists.assert_called_once_with()
        mock_open_file.assert_called_once_with(full_path, encoding="UTF-8")

    @patch("shinto.jsonschema.anyio.open_file", new_callable=AsyncMock)
    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    async def test_schema_error(self, mock_exists: MagicMock, mock_open_file: AsyncMock):
        """Test validate_json_against_schemas with invalid schema."""
        mock_open_file.return_value.__aenter__.return_value.read = AsyncMock(
            return_value=json.dumps(test_schema).replace("string", "integer"),
        )
        mock_exists.return_value = True

        data = {"name": "John Doe"}
        schema_filenames = ["invalid_schema.json"]
        full_path = Path(schema_filenames[0]).resolve()
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            await validate_json_against_schemas_async(data, schema_filenames)
        mock_exists.assert_called_once_with()
        mock_open_file.assert_called_once_with(full_path, encoding="UTF-8")

    @patch("shinto.jsonschema.anyio.open_file", new_callable=AsyncMock)
    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    async def test_multiple_schemas_error(self, mock_exists: MagicMock, mock_open_file: AsyncMock):
        """Test validate_json_against_schemas with invalid schema."""
        mock_exists.return_value = True
        delays = cycle([0, 0.2])

        async def mock_read() -> str:
            """Mock read function with simulated delay in file read."""
            await asyncio.sleep(next(delays))
            return json.dumps(test_schema).replace("string", "integer")

        mock_open_file.return_value.__aenter__.return_value.read = AsyncMock(side_effect=mock_read)

        data = {"name": "John Doe"}
        schema_filenames = ["invalid_schema.json"] * 2
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            await validate_json_against_schemas_async(data, schema_filenames)
        mock_exists.assert_has_calls([unittest.mock.call()] * 2)

    @patch("shinto.jsonschema.anyio.open_file", new_callable=AsyncMock)
    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    async def test_bad_schema_error(self, mock_exists: MagicMock, mock_open_file: AsyncMock):
        """Test validate_json_against_schemas with invalid schema."""
        mock_open_file.return_value.__aenter__.return_value.read = AsyncMock(
            return_value=json.dumps(test_schema).replace("string", "bad_type"),
        )
        mock_exists.return_value = True

        data = {"name": "John Doe"}
        schema_filenames = ["invalid_schema.json"]
        full_path = Path(schema_filenames[0]).resolve()
        with self.assertRaises(jsonschema.exceptions.SchemaError):
            await validate_json_against_schemas_async(data, schema_filenames)
        mock_exists.assert_called_once_with()
        mock_open_file.assert_called_once_with(full_path, encoding="UTF-8")

    @patch("shinto.jsonschema.anyio.open_file", new_callable=AsyncMock)
    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    async def test_non_existing_schema_error(
        self, mock_exists: MagicMock, mock_open_file: AsyncMock
    ):
        """Test validate_json_against_schemas with non-existing schema."""
        mock_exists.return_value = False

        data = {"name": "John Doe"}
        schema_filenames = ["non_existing_schema.json"]
        with self.assertRaises(FileNotFoundError):
            await validate_json_against_schemas_async(data, schema_filenames)
        mock_exists.assert_called_once_with()
        mock_open_file.assert_not_called()


if __name__ == "__main__":
    unittest.main()
