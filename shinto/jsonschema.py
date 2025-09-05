"""Json schema validation functions."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Literal

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
        """Get the schema filepath mappings."""
        return self._schema_mappings.copy()

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
            schema_filepath = str(Path(schema).resolve())
            with JsonSchemaRegistry._lock, Path(schema_filepath).open(encoding="UTF-8") as file:
                schema = json.load(file)
            schema["$id"] = self._clean_schema_id(schema.get("$id", schema_filepath))
            schema_id = self._register_schema(schema)
            self._schema_mappings[schema_filepath] = schema_id
            return schema_id
        return self._register_schema(schema)

    def _register_schema(self, schema: dict | str) -> str:
        if not schema.get("$id"):
            raise ValueError("Schema must have a $id.")
        schema_id = self._clean_schema_id(schema["$id"])
        if self.schema_id_in_registry(schema_id):
            if self.contents(schema_id) != schema and self._resolve_schema_refs(
                self.contents(schema_id),
                True,
            ) != self._resolve_schema_refs(schema, True):
                raise KeyError(f"Schema '{schema_id}' already registered with different contents.")
        else:
            self._registry = self._registry.with_resource(schema_id, Resource(schema, DRAFT7))
            self._validator_cache.clear()
        return schema_id

    def validate_json_against_schemas(
        self,
        data: dict | list,
        schema_filepaths: list[str] | None = None,
        schema_ids: list[str] | None = None,
    ):
        """
        Validate JSON data against JSON schemas.

        Args:
            data (dict | list): The JSON data to validate.
            schema_filepaths (list[str]): A list of schema filepaths to validate against.
            schema_ids (list[str]): A list of schema IDs to validate against.

        Raises:
            jsonschema.exceptions.ValidationError: The first validation error.

        """
        schema_ids = schema_ids or []
        if schema_filepaths:
            schema_ids.extend(
                [sid for fp in schema_filepaths if (sid := self.get_schema_id(fp)) is not None]
            )
        for schema_id in schema_ids:
            if not self.schema_id_in_registry(schema_id):
                raise KeyError(f"Schema '{schema_id}' not found in registry.")
            validator = self._get_validator(schema_id)
            validator.validate(data)

    def validate_json_against_schemas_complete(
        self,
        data: dict | list,
        schema_filepaths: list[str] | None = None,
        schema_ids: list[str] | None = None,
    ) -> list[ValidationErrorGroup]:
        """
        Validate JSON data against JSON schemas and return all errors.

        Args:
            data (dict | list): The JSON data to validate.
            schema_filepaths (list[str]): A list of schema filepaths to validate against.
            schema_ids (list[str]): A list of schema IDs to validate against.

        Returns:
            list[ValidationErrorGroup]: A list of validation error groups.

        """
        schema_ids = schema_ids or []
        if schema_filepaths:
            schema_ids.extend(
                [sid for fp in schema_filepaths if (sid := self.get_schema_id(fp)) is not None]
            )
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

    def _get_validator(self, schema_id: str) -> Draft7Validator:
        """Get a validator for a schema, creating it if it doesn't exist in the cache."""
        if schema_id not in self._validator_cache:
            schema = self._registry.contents(schema_id)
            self._validator_cache[schema_id] = Draft7Validator(
                schema, format_checker=FormatChecker(), registry=self._registry
            )
        return self._validator_cache[schema_id]

    def schema_registered(self, schema_filepath: str) -> bool:
        """Check if a schema filepath is registered."""
        schema_filepath = str(Path(schema_filepath).resolve())
        return schema_filepath in self._schema_mappings

    def schema_id_in_registry(self, schema_id: str) -> bool:
        """Check if a schema ID is in the registry."""
        return self._clean_schema_id(schema_id) in self._registry

    def get_schema(self, schema_id: str) -> dict:
        """Get a schema by its ID."""
        return self._registry.contents(self._clean_schema_id(schema_id))

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

    def _clean_schema_id(self, schema_id: str) -> str:
        """Clean a schema ID or convert a schema filepath to a schema ID."""
        schema_id = re.sub(
            r"[^a-z0-9_]", "", schema_id.replace("/", "_").replace(".json", "").lower()
        )
        return re.sub(r"_+", "_", schema_id).strip("_")

    def update_schema_refs_to(self, convert_to: Literal["id", "filepath"]):
        """
        Update schema refs.

        Update all schema refs in schemas in the registry if possible.
        If the reference cannot be updated, it is left unchanged.

        Args:
            convert_to (Literal["id", "filepath"]): What to replace the refs by.

        """
        self._validator_cache.clear()
        for schema_id in self._registry:
            schema = self._registry.contents(schema_id)
            new_schema = self._resolve_schema_refs(schema, convert_to)
            self._registry = self._registry.with_resource(schema_id, Resource(new_schema, DRAFT7))

    def _resolve_schema_refs(self, schema: dict, convert_to: Literal["id", "filepath"]) -> dict:
        """Update schema refs to schema IDs or filepaths."""
        result = {}
        for key, value in schema.items():
            if isinstance(value, dict):
                result[key] = self._resolve_schema_refs(value, convert_to)
            elif isinstance(value, list):
                result[key] = [
                    self._resolve_schema_refs(item, convert_to) if isinstance(item, dict) else item
                    for item in value
                ]
            elif key == "$ref" and not value.startswith("#"):
                result[key] = self._resolve_ref(value, convert_to)
            else:
                result[key] = value

        return result

    def _resolve_ref(self, ref: str, convert_to: Literal["id", "filepath"]) -> str:
        """Resolve a ref to a schema ID or filepath."""
        parts = ref.split("#", 1)
        ref_identifier = parts[0]
        fragment = f"#{parts[1]}" if len(parts) > 1 else ""
        schema_id = None
        filepath = None
        found_ref = False

        if self.schema_registered(ref_identifier):
            found_ref = True
            schema_id = self.get_schema_id(ref_identifier)
            filepath = str(Path(ref_identifier).resolve())
        elif self.schema_id_in_registry(ref_identifier):
            found_ref = True
            schema_id = self._clean_schema_id(ref_identifier)
            filepath = self.next_filepath_for_schema_id(ref_identifier)

        if found_ref:
            if convert_to == "id":
                return f"{schema_id}{fragment}"
            if convert_to == "filepath":
                if filepath:
                    return f"{filepath}{fragment}"

                logging.warning(
                    "Referenced schema %s is registered from a JSON schema and does not "
                    "have a filepath. Skipping ref update.",
                    ref_identifier,
                )
        else:
            logging.warning("Referenced schema %s not found in registry.", ref_identifier)

        return ref
