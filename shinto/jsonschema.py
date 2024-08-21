"""Json schema validation functions."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING

import anyio
import jsonschema
from jsonschema import Draft7Validator, FormatChecker

if TYPE_CHECKING:  # pragma: no cover
    from jsonschema.exceptions import ValidationError


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
