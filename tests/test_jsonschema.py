"""Test cases for the JSON schema module."""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import jsonschema.exceptions
import referencing.exceptions

from shinto.jsonschema import JsonSchemaRegistry, ValidationErrorGroup

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
            schema_id = self.registry.register_schema(self.test_schema_filepath)

        # Test valid data
        data = {"name": "John Doe"}
        self.registry.validate_json_against_schemas(data, [schema_id])
        # Test invalid data
        invalid_data = {"name": 123}
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            self.registry.validate_json_against_schemas(invalid_data, [schema_id])

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
            schema_id = self.registry.register_schema(self.test_schema_filepath)

        # Test valid data
        data = {"name": "John Doe"}
        errors = self.registry.validate_json_against_schemas_complete(data, [schema_id])
        self.assertEqual(len(errors), 0)

        # Test invalid data
        invalid_data = {"name": 123}
        errors = self.registry.validate_json_against_schemas_complete(invalid_data, [schema_id])
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], ValidationErrorGroup)
        self.assertEqual(errors[0].schema_id, schema_id)
        self.assertIsInstance(errors[0].errors[0], jsonschema.exceptions.ValidationError)

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
            schema_id = self.registry.register_schema(self.test_schema_filepath)

        # Test getting registered schema
        schema = self.registry.contents(schema_id)
        self.assertEqual(schema, self.test_schema)
        # Test getting non-registered schema
        with self.assertRaises(KeyError):
            self.registry.contents("non_existent_schema")

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
            schema_id = self.registry.register_schema(self.test_schema_filepath)

        # Test registered schema ID
        self.assertTrue(self.registry.schema_id_in_registry(schema_id))
        # Test non-registered schema ID
        self.assertFalse(self.registry.schema_id_in_registry("non_existent_schema"))

    def test_check_unresolvable_refs(self):
        """Test checking for unresolvable refs when all refs are valid."""
        parent_schema = {
            "$id": "parent_schema",
            "type": "object",
            "properties": {
                "child": {"$ref": "child_schema.json#/properties/name"},
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

        self.registry.check_unresolvable_refs()
        self.assertListEqual(
            self.registry.get_referenced_schema_ids("parent_schema"), ["child_schema"]
        )

    def test_check_unresolvable_refs_error(self):
        """Test checking for unresolvable refs when refs are invalid."""
        parent_schema_2 = {
            "$id": "parent_schema_2",
            "type": "object",
            "properties": {
                "child": {"$ref": "child_schema_2#/properties/bad_ref"},
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

        with self.assertRaises(referencing.exceptions.Unresolvable):
            self.registry.check_unresolvable_refs()

    def test_register_directory(self):
        """Test registering all schemas in a directory."""
        schema1 = {
            "$id": "dir_schema_1",
            "type": "object",
            "properties": {"field1": {"type": "string"}},
        }
        schema2 = {
            "$id": "dir_schema_2",
            "type": "object",
            "properties": {"field2": {"type": "integer"}},
        }

        with patch("shinto.jsonschema.Path.glob") as mock_glob, patch(
            "shinto.jsonschema.Path.open", new_callable=mock_open
        ) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_glob.return_value = [
                Path("test_dir/schema1.json"),
                Path("test_dir/schema2.json"),
            ]
            mock_open_file.return_value.__enter__.return_value.read.side_effect = [
                json.dumps(schema1),
                json.dumps(schema2),
            ]

            self.registry.register_directory("test_dir")

            self.assertTrue(self.registry.schema_id_in_registry("dir_schema_1"))
            self.assertTrue(self.registry.schema_id_in_registry("dir_schema_2"))

    def test_register_directory_with_pattern(self):
        """Test registering schemas in a directory with custom pattern."""
        schema = {
            "$id": "custom_pattern_schema",
            "type": "object",
        }

        with patch("shinto.jsonschema.Path.glob") as mock_glob, patch(
            "shinto.jsonschema.Path.open", new_callable=mock_open
        ) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_glob.return_value = [Path("test_dir/custom.json")]
            mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(
                schema
            )

            self.registry.register_directory("test_dir", pattern="*.json")

            self.assertTrue(self.registry.schema_id_in_registry("custom_pattern_schema"))

    def test_get_schema_ids(self):
        """Test getting all schema IDs in the registry."""
        schema1 = {"$id": "schema_id_1", "type": "object"}
        schema2 = {"$id": "schema_id_2", "type": "object"}

        with patch("shinto.jsonschema.Path.open", new_callable=mock_open) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_open_file.return_value.__enter__.return_value.read.side_effect = [
                json.dumps(schema1),
                json.dumps(schema2),
            ]
            self.registry.register_schema("schema1.json")
            self.registry.register_schema("schema2.json")

        schema_ids = self.registry.get_schema_ids()
        self.assertIn("schema_id_1", schema_ids)
        self.assertIn("schema_id_2", schema_ids)
        self.assertEqual(len(schema_ids), 2)

    def test_get_references(self):
        """Test getting all URI references in a schema."""
        child_schema = {
            "$id": "child_schema",
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }

        parent_schema = {
            "$id": "parent_with_refs",
            "type": "object",
            "properties": {
                "child": {"$ref": "child_schema#/properties/name"},
                "internal": {"$ref": "#/definitions/internal_def"},
            },
            "definitions": {
                "internal_def": {"type": "string"},
            },
        }

        with patch("shinto.jsonschema.Path.open", new_callable=mock_open) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_open_file.return_value.__enter__.return_value.read.side_effect = [
                json.dumps(child_schema),
                json.dumps(parent_schema),
            ]
            self.registry.register_schema("child_schema.json")
            schema_id = self.registry.register_schema("parent_with_refs.json")

        refs = self.registry.get_references(schema_id)
        self.assertIn("child_schema#/properties/name", refs)
        self.assertIn("#/definitions/internal_def", refs)
        self.assertEqual(len(refs), 2)

    def test_register_schema_from_dict(self):
        """Test registering a schema from a dictionary."""
        schema = {
            "$id": "dict_schema",
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }

        schema_id = self.registry.register_schema(schema)
        self.assertEqual(schema_id, "dict_schema")
        self.assertTrue(self.registry.schema_id_in_registry("dict_schema"))

    def test_register_schema_without_id_raises_error(self):
        """Test registering a schema without $id raises ValueError."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }

        with self.assertRaises(ValueError) as context:
            self.registry.register_schema(schema)
        self.assertIn("Schema must have an $id", str(context.exception))

    def test_register_schema_generates_id_from_filepath(self):
        """Test that schema ID is generated from filepath when no $id is present."""
        schema_no_id = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }

        with patch("shinto.jsonschema.Path.open", new_callable=mock_open) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(
                schema_no_id
            )

            with patch("shinto.jsonschema.Path.resolve") as mock_resolve:
                mock_resolve.return_value = Path("C:/test/my_schema.json")
                schema_id = self.registry.register_schema("my_schema.json")

                # Verify that a schema ID was generated
                self.assertTrue(self.registry.schema_id_in_registry(schema_id))

    def test_validate_json_against_nonexistent_schema(self):
        """Test validating against a schema that doesn't exist."""
        data = {"name": "John"}

        with self.assertRaises(KeyError) as context:
            self.registry.validate_json_against_schemas(data, ["nonexistent_schema"])
        self.assertIn("not found in registry", str(context.exception))

    def test_validate_json_against_schemas_complete_nonexistent_schema(self):
        """Test complete validation against a schema that doesn't exist."""
        data = {"name": "John"}

        with self.assertRaises(KeyError) as context:
            self.registry.validate_json_against_schemas_complete(data, ["nonexistent_schema"])
        self.assertIn("not found in registry", str(context.exception))

    def test_validation_error_group(self):
        """Test ValidationErrorGroup class."""
        error = jsonschema.exceptions.ValidationError("Test error")
        error_group = ValidationErrorGroup(
            schema_id="test_schema",
            message="Test message",
            errors=[error],
        )

        self.assertEqual(error_group.schema_id, "test_schema")
        self.assertEqual(error_group.message, "Test message")
        self.assertEqual(len(error_group.errors), 1)
        self.assertIsInstance(error_group.errors[0], jsonschema.exceptions.ValidationError)

    def test_validate_multiple_errors(self):
        """Test validation returns multiple errors for invalid data."""
        complex_schema = {
            "$id": "complex_schema",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "email": {"type": "string", "format": "email"},
            },
            "required": ["name", "age"],
        }

        with patch("shinto.jsonschema.Path.open", new_callable=mock_open) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(
                complex_schema
            )
            schema_id = self.registry.register_schema("complex_schema.json")

        # Test invalid data with multiple errors
        invalid_data = {"name": 123, "age": "not an integer"}
        errors = self.registry.validate_json_against_schemas_complete(invalid_data, [schema_id])

        self.assertGreater(len(errors), 0)
        for error_group in errors:
            self.assertIsInstance(error_group, ValidationErrorGroup)
            self.assertEqual(error_group.schema_id, schema_id)

    def test_nested_ref_resolution(self):
        """Test that nested schema references are properly resolved."""
        grandparent_schema = {
            "$id": "grandparent_schema",
            "type": "object",
            "properties": {
                "parent": {"$ref": "parent_schema.json#/properties/child"},
            },
        }

        parent_schema_nested = {
            "$id": "parent_schema",
            "type": "object",
            "properties": {
                "child": {"$ref": "child_schema.json#/properties/name"},
            },
        }

        child_schema_nested = {
            "$id": "child_schema",
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }

        with patch("shinto.jsonschema.Path.open", new_callable=mock_open) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_open_file.return_value.__enter__.return_value.read.side_effect = [
                json.dumps(child_schema_nested),
                json.dumps(parent_schema_nested),
                json.dumps(grandparent_schema),
            ]
            self.registry.register_schema("child_schema.json")
            self.registry.register_schema("parent_schema.json")
            self.registry.register_schema("grandparent_schema.json")

        # Verify all schemas are registered
        self.assertTrue(self.registry.schema_id_in_registry("grandparent_schema"))
        self.assertTrue(self.registry.schema_id_in_registry("parent_schema"))
        self.assertTrue(self.registry.schema_id_in_registry("child_schema"))

        # Check that references are properly resolved
        self.registry.check_unresolvable_refs()

    def test_register_same_schema_twice_idempotent(self):
        """Test that registering the same schema twice is idempotent."""
        with patch("shinto.jsonschema.Path.open", new_callable=mock_open) as mock_open_file, patch(
            "shinto.jsonschema.Path.exists", new_callable=MagicMock()
        ) as mock_exists:
            mock_exists.return_value = True
            mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(
                self.test_schema
            )

            schema_id1 = self.registry.register_schema(self.test_schema_filepath)
            schema_id2 = self.registry.register_schema(self.test_schema_filepath)

            self.assertEqual(schema_id1, schema_id2)


if __name__ == "__main__":
    unittest.main()
