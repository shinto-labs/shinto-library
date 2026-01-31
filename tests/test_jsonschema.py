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
    ValidationErrorGroup,
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
        self.assertEqual(self.registry.contents(schema_id), self.test_schema)
        self.assertEqual(
            self.registry.get_schema_id(self.test_schema_filepath),
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
        self.assertEqual(None, self.registry.get_schema_id("non_existent_schema.json"))

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
        self.assertIsInstance(errors[0], ValidationErrorGroup)
        self.assertEqual(errors[0].schema_id, "test_schema")
        self.assertIsInstance(errors[0].errors[0], jsonschema.exceptions.ValidationError)

    def test_schema_registered(self):
        """Test checking if a schema is registered."""
        # Register a schema first
        with patch("shinto.jsonschema.Path.open", new_callable=mock_open) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(
                self.test_schema
            )
            self.registry.register_schema(self.test_schema_filepath)

        # Test registered schema
        self.assertTrue(self.registry.schema_registered(self.test_schema_filepath))
        # Test non-registered schema
        self.assertFalse(self.registry.schema_registered("non_existent_schema.json"))

    def test_get_schema(self):
        """Test getting a schema by its ID."""
        # Register a schema first
        with patch("shinto.jsonschema.Path.open", new_callable=mock_open) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(
                self.test_schema
            )
            self.registry.register_schema(self.test_schema_filepath)

        # Test getting registered schema
        schema = self.registry.get_schema("test_schema")
        self.assertEqual(schema, self.test_schema)
        # Test getting non-registered schema
        with self.assertRaises(KeyError):
            self.registry.get_schema("non_existent_schema")

    def test_schema_id_in_registry(self):
        """Test checking if a schema ID is in the registry."""
        # Register a schema first
        with patch("shinto.jsonschema.Path.open", new_callable=mock_open) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(
                self.test_schema
            )
            self.registry.register_schema(self.test_schema_filepath)

        # Test registered schema ID
        self.assertTrue(self.registry.schema_id_in_registry("test_schema"))
        # Test non-registered schema ID
        self.assertFalse(self.registry.schema_id_in_registry("non_existent_schema"))

    def test_next_filepath_for_schema_id(self):
        """Test getting filepath for a schema ID."""
        # Register a schema first
        with patch("shinto.jsonschema.Path.open", new_callable=mock_open) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(
                self.test_schema
            )
            self.registry.register_schema(self.test_schema_filepath)

        # Test getting filepath for registered schema ID
        self.assertEqual(
            self.registry.next_filepath_for_schema_id("test_schema"),
            str(Path(self.test_schema_filepath).resolve()),
        )
        # Test getting filepath for non-registered schema ID
        self.assertIsNone(self.registry.next_filepath_for_schema_id("non_existent_schema"))

    def test_update_schema_refs(self):
        """Test updating schema references."""
        # Create a schema with references
        schema_with_refs = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "parent_schema",
            "type": "object",
            "properties": {
                "child": {"$ref": "child_schema.json"},
                "nested": {
                    "type": "object",
                    "properties": {
                        "grandchild": {"$ref": "grandchild_schema.json#/definitions/type"}
                    },
                },
            },
        }

        child_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "child_schema",
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }

        grandchild_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "grandchild_schema",
            "definitions": {"type": {"type": "string"}},
        }

        # Register schemas
        with patch("shinto.jsonschema.Path.open", new_callable=mock_open) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_open_file.return_value.__enter__.return_value.read.side_effect = [
                json.dumps(schema_with_refs),
                json.dumps(child_schema),
                json.dumps(grandchild_schema),
            ]
            self.registry.register_schema("parent_schema.json")
            self.registry.register_schema("child_schema.json")
            self.registry.register_schema("grandchild_schema.json")

        # Test updating refs to IDs
        self.registry.update_schema_refs_to("id")
        schema = self.registry.contents("parent_schema")
        self.assertEqual(schema["properties"]["child"]["$ref"], "child_schema")
        self.assertEqual(
            schema["properties"]["nested"]["properties"]["grandchild"]["$ref"],
            "grandchild_schema#/definitions/type",
        )

        # Test updating refs to filepaths
        self.registry.update_schema_refs_to("filepath")
        schema = self.registry.contents("parent_schema")
        self.assertEqual(
            schema["properties"]["child"]["$ref"],
            str(Path("child_schema.json").resolve()),
        )
        self.assertEqual(
            schema["properties"]["nested"]["properties"]["grandchild"]["$ref"],
            f"{Path('grandchild_schema.json').resolve()!s}#/definitions/type",
        )

    def test_check_unresolvable_refs_none(self):
        """Test checking for unresolvable refs when all refs are valid."""
        parent_schema = {
            "$id": "parent_schema",
            "type": "object",
            "properties": {
                "child": {"$ref": "child_schema#/properties/name"},
            },
        }

        child_schema = {
            "$id": "child_schema",
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }

        with patch("shinto.jsonschema.Path.open", new_callable=mock_open) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_open_file.return_value.__enter__.return_value.read.side_effect = [
                json.dumps(parent_schema),
                json.dumps(child_schema),
            ]
            self.registry.register_schema("parent_schema.json")
            self.registry.register_schema("child_schema.json")

        unresolvable = self.registry.check_unresolvable_refs()
        self.assertEqual(len(unresolvable), 0)

    def test_check_unresolvable_refs_found(self):
        """Test checking for unresolvable refs when refs are invalid."""
        parent_schema_2 = {
            "$id": "parent_schema_2",
            "type": "object",
            "properties": {
                "child": {"$ref": "child_schema#/properties/bad_ref"},
            },
        }

        child_schema_2 = {
            "$id": "child_schema_2",
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }

        with patch("shinto.jsonschema.Path.open", new_callable=mock_open) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_open_file.return_value.__enter__.return_value.read.side_effect = [
                json.dumps(parent_schema_2),
                json.dumps(child_schema_2),
            ]
            self.registry.register_schema("parent_schema_2.json")
            self.registry.register_schema("child_schema_2.json")
        unresolvable = self.registry.check_unresolvable_refs()
        self.assertEqual(len(unresolvable), 1)


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
