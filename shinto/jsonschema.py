"""Json schema validation functions."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING

import anyio
import jsonschema
from deprecated.sphinx import deprecated
from jsonschema import Draft7Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

if TYPE_CHECKING:  # pragma: no cover
    from jsonschema.exceptions import ValidationError
    from referencing.jsonschema import SchemaRegistry


@deprecated(version="1.1.0", reason="Use JsonSchemaRegistry.validate_json_against_schemas instead")
def validate_json_against_schemas(data: dict | list, schema_filenames: list[str]):
    """
    Validate JSON data against JSON schemas.

    Args:
        data (dict | list): The JSON data to validate.
        schema_filenames (list[str]): A list of schema filenames to validate against.

    Raises:
        FileNotFoundError: If the schema file is not found.
        jsonschema.exceptions.ValidationError: If the data does not validate against the schema.
        (Any other jsonschema.exceptions exceptions)

    """
    for schema_filename in schema_filenames:
        schema_filepath = Path(schema_filename).resolve()

        if not schema_filepath.exists():
            msg = f"Schema file not found: {schema_filepath}"
            raise FileNotFoundError(msg)

        with Path(schema_filepath).open(encoding="UTF-8") as file:
            schema = json.load(file)
            jsonschema.validate(data, schema, format_checker=FormatChecker())


@deprecated(
    version="1.1.0", reason="Use JsonSchemaRegistry.validate_json_against_schemas_complete instead"
)
def validate_json_against_schemas_complete(
    data: dict | list, schema_filenames: list[str]
) -> list[ValidationError]:
    """
    Validate JSON data against JSON schemas and return all errors.

    Args:
        data (dict | list): The JSON data to validate.
        schema_filenames (list[str]): A list of schema filenames to validate against.

    Returns:
        list[jsonschema.exceptions.ValidationError]: A list of validation errors.

    Raises:
        FileNotFoundError: If the schema file is not found.
        (Any other jsonschema.exceptions exceptions)

    """
    validation_errors = []
    for schema_filename in schema_filenames:
        schema_filepath = Path(schema_filename).resolve()

        if not schema_filepath.exists():
            msg = f"Schema file not found: {schema_filepath}"
            raise FileNotFoundError(msg)

        with Path(schema_filepath).open(encoding="UTF-8") as file:
            schema = json.load(file)
            validator = Draft7Validator(schema, format_checker=FormatChecker())
            validation_errors.extend(list(validator.iter_errors(data)))
    return validation_errors


async def _validate_json_against_schemas_async_task(data: dict | list, schema_filepath: Path):
    """Validate JSON data against a schema."""
    async with await anyio.open_file(schema_filepath, encoding="UTF-8") as file:
        schema = json.loads(await file.read())
        jsonschema.validate(data, schema, format_checker=FormatChecker())


@deprecated(version="1.1.0", reason="Use JsonSchemaRegistry.validate_json_against_schemas instead")
async def validate_json_against_schemas_async(data: dict | list, schema_filenames: list[str]):
    """
    Validate JSON data against JSON schemas.

    Args:
        data (dict | list): The JSON data to validate.
        schema_filenames (list[str]): A list of schema filenames to validate against.

    Raises:
        FileNotFoundError: If the schema file is not found.
        jsonschema.exceptions.SchemaError: If the schema is invalid.
        jsonschema.exceptions.ValidationError: If the data does not validate against the schema.

    """
    tasks: list[asyncio.Future] = []

    for schema_filename in schema_filenames:
        schema_filepath = Path(schema_filename).resolve()

        if not schema_filepath.exists():
            msg = f"Schema file not found: {schema_filepath}"
            raise FileNotFoundError(msg)

        task = asyncio.create_task(_validate_json_against_schemas_async_task(data, schema_filepath))
        tasks.append(task)

    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
    for task in pending:
        task.cancel()

    for task in done:
        exception = task.exception()
        if exception:
            raise exception


class JsonSchemaRegistry:
    """Class for validating JSON against JSON schemas."""

    _instance: JsonSchemaRegistry | None = None
    _lock = threading.Lock()
    _initialized = False
    _registry: SchemaRegistry
    _schema_mappings: dict[str, str]
    _validator_cache: dict[str, Draft7Validator]

    def __init__(self) -> None:
        """Initialize the JsonSchemaValidator class."""
        self._registry = Registry()
        self._schema_mappings = {}
        self._validator_cache = {}

    @property
    def schema_mappings(self) -> dict[str, str]:
        """Get the schema mappings."""
        return self._schema_mappings.copy()

    def register_schema(self, schema_filepath: str) -> str:
        """
        Add a schema to the registry.

        Args:
            schema_filepath (str): The path to the schema file.

        Returns:
            str: The schema ID.

        Raises:
            KeyError: If a conflicting schema is already registered.

        """
        schema_filepath = str(Path(schema_filepath).resolve())
        with JsonSchemaRegistry._lock, Path(schema_filepath).open(encoding="UTF-8") as file:
            schema = json.load(file)
            schema_id = self._clean_schema_id(schema.get("$id", schema_filepath))
            schema["$id"] = schema_id
            if self.schema_id_in_registry(schema_id):
                if self.contents(schema_id) != schema and self._resolve_schema_refs(
                    self.contents(schema_id)
                ) != self._resolve_schema_refs(schema):
                    raise KeyError(
                        f"Schema with $id '{schema_id}' exists, "
                        f"but is different from '{schema_filepath}'"
                    )
            else:
                self._registry = self._registry.with_resource(schema_id, Resource(schema, DRAFT7))
                self._validator_cache.clear()
            self._schema_mappings[schema_filepath] = schema_id
            return schema_id

    def validate_json_against_schemas(self, data: dict | list, schema_filepaths: list[str]):
        """
        Validate JSON data against JSON schemas.

        Args:
            data (dict | list): The JSON data to validate.
            schema_filepaths (list[str]): A list of schema filepaths to validate against.

        Raises:
            KeyError: If the schema is not found in the registry.
            jsonschema.exceptions.ValidationError: The first validation error, if any.
            (Any other jsonschema.exceptions exceptions)

        """
        for schema_id in [self.get_schema_id(str(Path(fp).resolve())) for fp in schema_filepaths]:
            validator = self._get_validator(schema_id)
            validator.validate(data)

    def validate_json_against_schemas_complete(
        self, data: dict | list, schema_filepaths: list[str]
    ) -> list[ValidationError]:
        """
        Validate JSON data against JSON schemas and return all errors.

        Args:
            data (dict | list): The JSON data to validate.
            schema_filepaths (list[str]): A list of schema filepaths to validate against.

        Returns:
            list[jsonschema.exceptions.ValidationError]: A list of validation errors.

        Raises:
            KeyError: If the schema is not found in the registry.
            (Any other jsonschema.exceptions exceptions)

        """
        validation_errors = []
        for schema_id in [self.get_schema_id(str(Path(fp).resolve())) for fp in schema_filepaths]:
            validator = self._get_validator(schema_id)
            validation_errors.extend(list(validator.iter_errors(data)))
        return validation_errors

    def schema_registered(self, schema_filepath: str) -> bool:
        """Check if a schema filepath is registered."""
        schema_filepath = str(Path(schema_filepath).resolve())
        return schema_filepath in self._schema_mappings

    def schema_id_in_registry(self, schema_id: str) -> bool:
        """Check if a schema ID is in the registry."""
        return self._clean_schema_id(schema_id) in self._registry

    def contents(self, schema_id: str) -> dict:
        """Get the contents of a schema."""
        return self._registry.contents(self._clean_schema_id(schema_id))

    def next_filepath_for_schema_id(self, schema_id: str) -> str | None:
        """Get the first filepath for a schema ID."""
        schema_id = self._clean_schema_id(schema_id)
        return next((f for f, m in self._schema_mappings.items() if m == schema_id), None)

    def get_schema_id(self, schema_filepath: str) -> str | None:
        """Get the schema ID for a given schema filepath."""
        schema_filepath = str(Path(schema_filepath).resolve())
        return self._schema_mappings.get(schema_filepath)

    def update_schema_refs_to_ids(self):
        """Update schema refs to schema IDs."""
        self._validator_cache.clear()
        for schema_id in self._registry:
            schema = self._registry.contents(schema_id)
            new_schema = self._resolve_schema_refs(schema, True)
            self._registry = self._registry.with_resource(schema_id, Resource(new_schema, DRAFT7))

    def update_schema_refs_to_filepaths(self):
        """Update schema refs to schema filepaths."""
        self._validator_cache.clear()
        for schema_id in self._registry:
            schema = self._registry.contents(schema_id)
            new_schema = self._resolve_schema_refs(schema, False)
            self._registry = self._registry.with_resource(schema_id, Resource(new_schema, DRAFT7))

    def _get_validator(self, schema_id: str) -> Draft7Validator:
        """Get a validator for a schema, creating it if it doesn't exist in the cache."""
        if schema_id not in self._validator_cache:
            schema = self._registry.contents(schema_id)
            self._validator_cache[schema_id] = Draft7Validator(
                schema, format_checker=FormatChecker(), registry=self._registry
            )
        return self._validator_cache[schema_id]

    def _clean_schema_id(self, schema_id: str) -> str:
        """Clean a schema ID or convert a schema filepath to a schema ID."""
        schema_id = schema_id.lower()
        schema_id = "".join(c if c.isalnum() else "_" for c in schema_id)
        while "__" in schema_id:
            schema_id = schema_id.replace("__", "_")
        return schema_id.strip("_")

    def _resolve_schema_refs(self, schema: dict, convert_to_id: bool) -> dict:
        """
        Update schema refs to schema IDs or filepaths.

        Args:
            schema (dict): The schema to process
            convert_to_id (bool): If True, convert refs to schema IDs, otherwise to filepaths

        Returns:
            dict: The processed schema with updated refs

        """
        result = {}
        for key, value in schema.items():
            if isinstance(value, dict):
                result[key] = self._resolve_schema_refs(value, convert_to_id)
            elif isinstance(value, list):
                result[key] = [
                    self._resolve_schema_refs(item, convert_to_id)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            elif key == "$ref" and not value.startswith("#"):
                parts = value.split("#", 1)
                ref_identifier = parts[0]
                fragment = f"#{parts[1]}" if len(parts) > 1 else ""
                schema_id = None
                filepath = None

                if self.schema_registered(ref_identifier):
                    schema_id = self.get_schema_id(ref_identifier)
                    filepath = str(Path(ref_identifier).resolve())
                elif self.schema_id_in_registry(ref_identifier):
                    schema_id = self._clean_schema_id(ref_identifier)
                    filepath = self.next_filepath_for_schema_id(ref_identifier)
                else:
                    logging.warning("Referenced schema %s not found in registry.", ref_identifier)

                if convert_to_id:
                    result[key] = f"{schema_id}{fragment}"
                else:
                    result[key] = f"{filepath}{fragment}"
            else:
                result[key] = value

        return result
