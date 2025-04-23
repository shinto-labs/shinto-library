"""Json schema validation functions."""

from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Self

import anyio
import jsonschema
from deprecated.sphinx import deprecated
from jsonschema import Draft7Validator, FormatChecker
from referencing import Registry
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
        if JsonSchemaRegistry._initialized:
            return
        with JsonSchemaRegistry._lock:
            if JsonSchemaRegistry._initialized:
                return
            self._registry = Registry().with_resource("", DRAFT7)
            self._schema_mappings = {}
            self._validator_cache = {}
            JsonSchemaRegistry._initialized = True

    def __new__(cls) -> Self:
        """Create a new instance of the JsonSchemaValidator class."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def register_schema(self, schema_filepath: str) -> str:
        """
        Add a schema to the registry.

        Args:
            schema_filepath (str): The path to the schema file.

        Returns:
            int: The schema ID.

        Raises:
            KeyError: If a conflicting schema is already registered.

        """
        with JsonSchemaRegistry._lock, Path(schema_filepath).resolve().open(
            encoding="UTF-8"
        ) as file:
            schema = json.load(file)
            schema_id = schema.get("$id", schema_filepath)
            if schema_id in self._registry:
                if self._registry[schema_id] != schema:
                    raise KeyError(
                        f"Schema with $id '{schema_id}' exists, "
                        f"but is different from '{schema_filepath}'"
                    )
            else:
                self._registry = self._registry.with_resource(schema_id, schema)
                self._validator_cache.clear()
            self._schema_mappings[self._convert_schema_filepath(schema_filepath)] = schema_id
            return schema_id

    def get_schema_id(self, schema_filepath: str) -> str:
        """
        Get the schema ID for a given schema filepath.

        Args:
            schema_filepath (str): The path to the schema file.

        Returns:
            str: The schema ID.

        Raises:
            KeyError: If no schema ID is found for the given filepath.

        """
        return self._schema_mappings[self._convert_schema_filepath(schema_filepath)]

    def get_schema_by_filepath(self, schema_filepath: str) -> dict:
        """
        Get the JSON schema for a given schema filepath.

        Args:
            schema_filepath (str): The path to the schema file.

        Returns:
            dict: The JSON schema.

        Raises:
            KeyError: If no schema is found for the given filepath.

        """
        return self._registry[self.get_schema_id(schema_filepath)]

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
        for schema_id in [self.get_schema_id(fp) for fp in schema_filepaths]:
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
        for schema_id in [self.get_schema_id(fp) for fp in schema_filepaths]:
            validator = self._get_validator(schema_id)
            validation_errors.extend(list(validator.iter_errors(data)))
        return validation_errors

    def _convert_schema_filepath(self, schema_filepath: str) -> str:
        """Convert a schema filepath to a schema ID."""
        trimmed = schema_filepath[1:] if schema_filepath.startswith("/") else schema_filepath
        return trimmed.replace(".json", "").replace("/", "_").replace(".", "_")

    def _get_validator(self, schema_id: str) -> Draft7Validator:
        """Get a validator for a schema, creating it if it doesn't exist in the cache."""
        if schema_id not in self._validator_cache:
            schema = self._registry[schema_id]
            self._validator_cache[schema_id] = Draft7Validator(
                schema, format_checker=FormatChecker(), registry=self._registry
            )
        return self._validator_cache[schema_id]
