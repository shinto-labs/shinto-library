"""Test cases for the JSON schema module."""

import asyncio
import json
import unittest
from itertools import cycle
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import jsonschema.exceptions

from shinto.jsonschema import (
    JsonSchemaRegistry,
    validate_json_against_schemas,
    validate_json_against_schemas_async,
    validate_json_against_schemas_complete,
)

test_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {"name": {"type": "string"}},
}


class TestJsonSchemaRegistry(unittest.TestCase):
    """Test cases for the JsonSchemaRegistry class."""

    def setUp(self):
        """Set up test fixtures."""
        self.registry = JsonSchemaRegistry()
        self.test_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "test_schema",
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        self.test_schema_filepath = "test_schema.json"

    def tearDown(self):
        """Tear down test fixtures."""
        # Clear the singleton instance
        JsonSchemaRegistry._instance = None  # noqa: SLF001
        JsonSchemaRegistry._initialized = False  # noqa: SLF001

    @patch("shinto.jsonschema.Path.open", new_callable=mock_open)
    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    def test_register_schema(self, mock_exists: MagicMock, mock_open_file: MagicMock):
        """Test registering a schema."""
        mock_exists.return_value = True
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(
            self.test_schema
        )

        schema_id = self.registry.register_schema(self.test_schema_filepath)
        self.assertEqual(schema_id, "test_schema")
        self.assertEqual(self.registry.registry.contents(schema_id), self.test_schema)
        self.assertEqual(
            self.registry.schema_mappings[
                self.registry._convert_schema_filepath(self.test_schema_filepath)  # noqa: SLF001
            ],
            "test_schema",
        )

    @patch("shinto.jsonschema.Path.open", new_callable=mock_open)
    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    def test_register_schema_conflict(self, mock_exists: MagicMock, mock_open_file: MagicMock):
        """Test registering a schema with conflicting $id."""
        mock_exists.return_value = True
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(
            self.test_schema
        )

        # Register first schema
        self.registry.register_schema(self.test_schema_filepath)

        # Try to register conflicting schema
        conflicting_schema = self.test_schema.copy()
        conflicting_schema["properties"]["name"]["type"] = "integer"
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(
            conflicting_schema
        )

        with self.assertRaises(KeyError):
            self.registry.register_schema("conflicting_schema.json")

    def test_get_schema_id(self):
        """Test getting schema ID from filepath."""
        # Register a schema first
        with patch("shinto.jsonschema.Path.open", new_callable=mock_open) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(
                self.test_schema
            )
            self.registry.register_schema(self.test_schema_filepath)

        schema_id = self.registry.get_schema_id(self.test_schema_filepath)
        self.assertEqual(schema_id, "test_schema")

    def test_get_schema_id_not_found(self):
        """Test getting schema ID for non-existent schema."""
        with self.assertRaises(KeyError):
            self.registry.get_schema_id("non_existent_schema.json")

    def test_validate_json_against_schemas(self):
        """Test validating JSON against registered schemas."""
        # Register a schema first
        with patch("shinto.jsonschema.Path.open", new_callable=mock_open) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(
                self.test_schema
            )
            self.registry.register_schema(self.test_schema_filepath)

        # Test valid data
        data = {"name": "John Doe"}
        self.registry.validate_json_against_schemas(data, [self.test_schema_filepath])

        # Test invalid data
        invalid_data = {"name": 123}
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            self.registry.validate_json_against_schemas(invalid_data, [self.test_schema_filepath])

    def test_validate_json_against_schemas_complete(self):
        """Test validating JSON against registered schemas and getting all errors."""
        # Register a schema first
        with patch("shinto.jsonschema.Path.open", new_callable=mock_open) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(
                self.test_schema
            )
            self.registry.register_schema(self.test_schema_filepath)

        # Test valid data
        data = {"name": "John Doe"}
        errors = self.registry.validate_json_against_schemas_complete(
            data, [self.test_schema_filepath]
        )
        self.assertEqual(len(errors), 0)

        # Test invalid data
        invalid_data = {"name": 123}
        errors = self.registry.validate_json_against_schemas_complete(
            invalid_data, [self.test_schema_filepath]
        )
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], jsonschema.exceptions.ValidationError)

    def test_convert_schema_filepath(self):
        """Test converting schema filepath to schema ID."""
        test_cases = [
            ("/path/to/schema.json", "path_to_schema"),
            ("schema.json", "schema"),
            ("/path/to/schema.with.dots.json", "path_to_schema_with_dots"),
        ]
        for filepath, expected in test_cases:
            self.assertEqual(self.registry._convert_schema_filepath(filepath), expected)  # noqa: SLF001


class TestJsonSchema(unittest.TestCase):
    """Test cases for the JSON schema module."""

    @patch(
        "shinto.jsonschema.Path.open",
        new_callable=mock_open,
        read_data=json.dumps(test_schema),
    )
    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    def test_validate_json_against_schemas_valid(
        self, mock_exists: MagicMock, mock_open_file: MagicMock
    ):
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
        read_data=json.dumps(test_schema),
    )
    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    def test_validate_json_against_schemas_validate_error(
        self, mock_exists: MagicMock, mock_open_file: MagicMock
    ):
        """Test validate_json_against_schemas with invalid schema."""
        mock_exists.return_value = True
        data = {"name": 123}
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
    def test_validate_json_against_schemas_schema_error(
        self, mock_exists: MagicMock, mock_open_file: MagicMock
    ):
        """Test validate_json_against_schemas with invalid schema."""
        mock_exists.return_value = True
        data = {"name": "John Doe"}
        schema_filenames = ["invalid_schema.json"]
        with self.assertRaises(jsonschema.exceptions.SchemaError):
            validate_json_against_schemas(data, schema_filenames)
        mock_open_file.assert_called_once_with(encoding="UTF-8")

    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    def test_validate_json_against_schemas_non_existing_schema(self, mock_exists: MagicMock):
        """Test validate_json_against_schemas with non-existing schema."""
        mock_exists.return_value = False

        data = {"name": "John Doe"}
        schema_filenames = ["non_existing_schema.json"]
        with self.assertRaises(FileNotFoundError):
            validate_json_against_schemas(data, schema_filenames)
        mock_exists.assert_called_once_with()

    @patch(
        "shinto.jsonschema.Path.open",
        new_callable=mock_open,
        read_data=json.dumps(test_schema),
    )
    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    def test_validate_json_against_schemas_complete_valid(
        self, mock_exists: MagicMock, mock_open_file: MagicMock
    ):
        """Test validate_json_against_schemas_complete."""
        mock_exists.return_value = True
        data = {"name": "John Doe"}
        schema_filenames = ["valid_schema.json"]
        errors = validate_json_against_schemas_complete(data, schema_filenames)
        mock_exists.assert_called_once_with()
        mock_open_file.assert_called_once_with(encoding="UTF-8")
        self.assertEqual(len(errors), 0)
        mock_exists.assert_called_once_with()

    @patch(
        "shinto.jsonschema.Path.open",
        new_callable=mock_open,
        read_data=json.dumps(test_schema),
    )
    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    def test_validate_json_against_schemas_complete_validate_error(
        self, mock_exists: MagicMock, mock_open_file: MagicMock
    ):
        """Test validate_json_against_schemas_complete."""
        mock_exists.return_value = True
        data = {"name": 123}
        schema_filenames = ["valid_schema.json"]
        errors = validate_json_against_schemas_complete(data, schema_filenames)
        mock_exists.assert_called_once_with()
        mock_open_file.assert_called_once_with(encoding="UTF-8")
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], jsonschema.exceptions.ValidationError)
        mock_exists.assert_called_once_with()

    @patch(
        "shinto.jsonschema.Path.open",
        new_callable=mock_open,
        read_data=json.dumps(test_schema).replace("string", "bad_type"),
    )
    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    def test_validate_json_against_schemas_complete_schema_error(
        self, mock_exists: MagicMock, mock_open_file: MagicMock
    ):
        """Test validate_json_against_schemas_complete."""
        mock_exists.return_value = True
        data = {"name": "John Doe"}
        schema_filenames = ["invalid_schema.json"]
        with self.assertRaises(jsonschema.exceptions.UnknownType):
            validate_json_against_schemas_complete(data, schema_filenames)
        mock_open_file.assert_called_once_with(encoding="UTF-8")
        mock_exists.assert_called_once_with()

    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    def test_validate_json_against_schemas_complete_non_existing_schema(
        self, mock_exists: MagicMock
    ):
        """Test validate_json_against_schemas_complete with non-existing schema."""
        mock_exists.return_value = False

        data = {"name": "John Doe"}
        schema_filenames = ["non_existing_schema.json"]
        with self.assertRaises(FileNotFoundError):
            validate_json_against_schemas_complete(data, schema_filenames)
        mock_exists.assert_called_once_with()


class TestAsyncJsonSchema(unittest.IsolatedAsyncioTestCase):
    """Test cases for the JSON schema module."""

    @patch("shinto.jsonschema.anyio.open_file", new_callable=AsyncMock)
    @patch("shinto.jsonschema.Path.exists", new_callable=MagicMock())
    async def test_validate_json_against_schemas_async_valid(
        self, mock_exists: MagicMock, mock_open_file: AsyncMock
    ):
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
    async def test_validate_json_against_schemas_async_validate_error(
        self, mock_exists: MagicMock, mock_open_file: AsyncMock
    ):
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
    async def test_validate_json_against_schemas_async_multiple_schemas_validate_error(
        self, mock_exists: MagicMock, mock_open_file: AsyncMock
    ):
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
    async def test_validate_json_against_schemas_async_schema_error(
        self, mock_exists: MagicMock, mock_open_file: AsyncMock
    ):
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
    async def test_validate_json_against_schemas_async_non_existing_schema(
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
