"""Json schema validation functions."""

import asyncio
import json
import logging
from pathlib import Path

import anyio
import jsonschema


def _validate(data: dict, schema: dict, schema_filepath: str) -> bool:
    """Validate JSON data against a schema."""
    try:
        jsonschema.validate(data, schema)
    except jsonschema.SchemaError:
        logging.exception("JSON schema error in %s", schema_filepath)
        return False
    except jsonschema.ValidationError:
        logging.exception("JSON validation error in %s", schema_filepath)
        return False

    return True


def validate_json_against_schemas(data: dict, schema_filenames: list[str]) -> bool:
    """Validate JSON data against JSON schemas."""
    for schema_filename in schema_filenames:
        schema_filepath = Path(schema_filename).resolve()

        if not schema_filepath.exists():
            logging.error("Schema file not found: %s", schema_filepath)
            return False

        with Path(schema_filepath).open(encoding="UTF-8") as file:
            schema = json.load(file)
            if not _validate(data, schema, schema_filepath):
                return False

    return True


async def _validate_json_against_schemas_async_task(data: dict, schema_filepath: Path) -> bool:
    """Validate JSON data against a schema."""
    async with await anyio.open_file(schema_filepath, encoding="UTF-8") as file:
        schema = json.loads(await file.read())
        if not _validate(data, schema, schema_filepath):
            msg = f"Validation failed for {schema_filepath}"
            raise ValueError(msg)


async def validate_json_against_schemas_async(data: dict, schema_filenames: list[str]) -> bool:
    """Validate JSON data against JSON schemas."""
    tasks: list[asyncio.Future] = []

    for schema_filename in schema_filenames:
        schema_filepath = Path(schema_filename).resolve()

        if not schema_filepath.exists():
            logging.error("Schema file not found: %s", schema_filepath)
            return False

        task = asyncio.create_task(_validate_json_against_schemas_async_task(data, schema_filepath))
        tasks.append(task)

    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
    for task in pending:
        task.cancel()

    return not any(task for task in done if task.exception())
