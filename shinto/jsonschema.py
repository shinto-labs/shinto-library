"""Json schema validation functions."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from jsonschema import Draft7Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

if TYPE_CHECKING:  # pragma: no cover
    from jsonschema.exceptions import ValidationError


class ValidationErrorGroup:
    """
    A group of validation errors.

    schema_id: The ID of the schema that the errors belong to.
    message: A message describing the errors.
    errors: A list of validation errors.
    """

    schema_id: str
    message: str
    errors: list[ValidationError]

    def __init__(self, schema_id: str, message: str, errors: list[ValidationError]):
        """Initialize the ValidationErrorGroup class."""
        self.schema_id = schema_id
        self.message = message
        self.errors = errors


class JsonSchemaRegistry:
    """Class for validating JSON against JSON schemas."""

    _registry: Registry

    def __init__(self) -> None:
        """Initialize the JsonSchemaValidator class."""
        self._registry = Registry()

    def register_directory(self, directory: str, pattern: str = "**/*.json"):
        """Register all schemas in a directory."""
        for schema_filepath in Path(directory).resolve().glob(pattern):
            self.register_schema(str(schema_filepath))

    def register_schema(self, schema: str | dict) -> str:
        """
        Add a schema to the registry.

        When registering a schema from a dict,
        you can only reference the schema using the $id not the filepath.
        When registering a schema from a filepath, and the schema does not have a $id,
        the schema ID is generated from the filepath.

        Args:
            schema (str | dict): JSON schema or filepath to schema.

        Returns:
            str: The schema ID.

        Raises:
            ValueError: If the schema does not have a $id. For filepaths,
            KeyError: If a conflicting schema is already registered.

        """
        if isinstance(schema, str):
            schema_filepath = Path(schema).resolve()
            with schema_filepath.open(encoding="UTF-8") as file:
                schema = json.load(file)
            schema["$id"] = schema.get("$id", str(schema_filepath))

        if not schema.get("$id"):
            raise ValueError("Schema must have an $id.")

        schema_id = self._normalize_schema_id(schema["$id"])
        schema["$id"] = schema_id

        schema = self._normalize_schema_refs(schema)

        if self.schema_id_in_registry(schema_id):
            if self.contents(schema_id) != schema:
                raise KeyError(f"Schema '{schema_id}' already registered with different contents.")
        else:
            self._registry = self._registry.with_resource(schema_id, Resource(schema, DRAFT7))

        return schema_id

    def validate_json_against_schemas(
        self,
        data: dict | list,
        schema_ids: list[str],
    ):
        """
        Validate JSON data against JSON schemas.

        Args:
            data (dict | list): The JSON data to validate.
            schema_ids (list[str]): A list of schema IDs to validate against.

        Raises:
            jsonschema.exceptions.ValidationError: The first validation error.

        """
        schema_ids = [self._normalize_schema_id(sid) for sid in schema_ids]
        for schema_id in schema_ids:
            if not self.schema_id_in_registry(schema_id):
                raise KeyError(f"Schema '{schema_id}' not found in registry.")
            validator = self._get_validator(schema_id)
            validator.validate(data)

    def validate_json_against_schemas_complete(
        self,
        data: dict | list,
        schema_ids: list[str],
    ) -> list[ValidationErrorGroup]:
        """
        Validate JSON data against JSON schemas and return all errors.

        Args:
            data (dict | list): The JSON data to validate.
            schema_ids (list[str]): A list of schema IDs to validate against.

        Returns:
            list[ValidationErrorGroup]: A list of validation error groups.

        """
        schema_ids = [self._normalize_schema_id(sid) for sid in schema_ids]
        validation_errors = []
        for schema_id in schema_ids:
            if not self.schema_id_in_registry(schema_id):
                raise KeyError(f"Schema '{schema_id}' not found in registry.")
            validator = self._get_validator(schema_id)
            errors = list(validator.iter_errors(data))

            unique_errors = {}
            for error in errors:
                path = ".".join(p if isinstance(p, str) else "item" for p in error.path)
                message = f"{path}: {error.message}"
                unique_errors.setdefault(message, [])
                unique_errors[message].append(error)

            for message, errors in unique_errors.items():
                validation_errors.append(ValidationErrorGroup(schema_id, message, errors))
        return validation_errors

    def schema_id_in_registry(self, schema_id: str) -> bool:
        """Check if a schema ID is in the registry."""
        return self._normalize_schema_id(schema_id) in self._registry

    def get_schema_ids(self) -> list[str]:
        """Get all schema IDs in the registry."""
        return list(self._registry)

    def contents(self, schema_id: str) -> dict:
        """Get the contents of a schema."""
        return self._registry.contents(self._normalize_schema_id(schema_id))

    def get_referenced_schema_ids(self, schema_id: str) -> list[str]:
        """
        Get all referenced schema IDs in a schema.

        If referenced schemas are registered in the registry, this method
        recursively traverses them to find all child references.

        Args:
            schema_id (str): The schema ID to analyse.

        Returns:
            list[str]: A list of schema IDs.

        """
        schema_id = self._normalize_schema_id(schema_id)
        schema = self._registry.contents(schema_id)
        references = self._find_references_recursively(schema)

        referenced_ids = set()
        for ref in references:
            if ref.startswith("#"):
                continue
            referenced_ids.add(ref.split("#")[0])

        return list(referenced_ids)

    def get_references(self, schema_id: str) -> list[str]:
        """
        Get all $ref URI references in a schema.

        If referenced schemas are registered in the registry, this method
        recursively traverses them to find all child references.

        Args:
            schema_id (str): The schema ID to analyse.

        Returns:
            list[str]: A list of all $ref URIs found directly or transitively.

        """
        schema_id = self._normalize_schema_id(schema_id)
        schema = self._registry.contents(schema_id)
        return list(self._find_references_recursively(schema))

    def check_unresolvable_refs(self):
        """
        Check all schemas in the registry for unresolvable references.

        Raises:
            referencing.exceptions.Unresolvable: If a referenced schema is not found.

        """
        resolver = self._registry.resolver()
        for schema_id in self._registry:
            for ref in self.get_references(schema_id):
                resolver.lookup(ref)

    def _normalize_schema_refs(self, schema: dict) -> dict:
        """Update schema refs to schema IDs."""
        result = {}
        for key, value in schema.items():
            if isinstance(value, dict):
                result[key] = self._normalize_schema_refs(value)
            elif isinstance(value, list):
                result[key] = [
                    self._normalize_schema_refs(item) if isinstance(item, dict) else item
                    for item in value
                ]
            elif key == "$ref" and not value.startswith("#"):
                parts = value.split("#", 1)
                ref_identifier = self._normalize_schema_id(parts[0])
                result[key] = f"{ref_identifier}#{parts[1]}" if len(parts) > 1 else ref_identifier
            else:
                result[key] = value

        return result

    def _find_references_recursively(self, schema: dict) -> set[str]:
        """Find all references in a schema recursively."""
        references = set()
        for key, value in schema.items():
            if key == "$ref" and isinstance(value, str):
                references.add(value)
                if not value.startswith("#"):
                    parts = value.split("#", 1)
                    if self.schema_id_in_registry(parts[0]):
                        ref_schema = self._registry.contents(parts[0])
                        references.update(self._find_references_recursively(ref_schema))
                    else:
                        logging.warning("Referenced schema '%s' not found in registry.", parts[0])
            elif isinstance(value, dict):
                references.update(self._find_references_recursively(value))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        references.update(self._find_references_recursively(item))
        return references

    def _normalize_schema_id(self, schema_id: str) -> str:
        """
        Clean a schema ID or convert a schema filepath to a schema ID.

        The schema ID is lowercased, slashes and ".json" are replaced with underscores,
        and schema IDs are stripped of character not in [a-z0-9_].

        Args:
            schema_id (str): The schema ID or filepath.

        Returns:
            str: The normalized schema ID.

        """
        schema_id = re.sub(
            r"[^a-z0-9_]",
            "",
            schema_id.replace("/", "_").replace(".json", "").lower(),
        )
        return re.sub(r"_+", "_", schema_id).strip("_")

    def _get_validator(self, schema_id: str) -> Draft7Validator:
        """Get a validator for a schema, creating it if it doesn't exist in the cache."""
        return Draft7Validator(
            self._registry.contents(schema_id),
            format_checker=FormatChecker(),
            registry=self._registry,
        )
