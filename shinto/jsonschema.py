"""Json schema validation functions."""

import asyncio
import json
import logging
from pathlib import Path

import anyio
import jsonschema


def validate_json_against_schemas(data: dict, schema_filenames: list[str]) -> bool:
    """Validate JSON data against JSON schemas."""
    for schema_filename in schema_filenames:
        schema_filepath = Path(schema_filename).resolve()

        with Path(schema_filepath).open(encoding="UTF-8") as file:
            schema = json.load(file)
            try:
                jsonschema.validate(data, schema)
            except jsonschema.SchemaError:
                logging.exception("JSON schema error in %s", schema_filepath)
                return False
            except jsonschema.ValidationError:
                logging.exception("JSON validation error in %s", schema_filepath)
                return False

    return True


async def _async_validate_json_against_schemas_task(data: dict, schema_filepath: Path) -> None:
    """Validate JSON data against a schema."""
    async with await anyio.open_file(schema_filepath, encoding="UTF-8") as file:
        schema = json.loads(await file.read())
        try:
            jsonschema.validate(data, schema)
        except jsonschema.SchemaError:
            logging.exception("JSON schema error in %s", schema_filepath)
            raise
        except jsonschema.ValidationError:
            logging.exception("JSON validation error in %s", schema_filepath)
            raise


async def async_validate_json_against_schemas(data: dict, schema_filenames: list[str]) -> bool:
    """Validate JSON data against JSON schemas."""
    tasks: dict[asyncio.Future, str] = {}

    for schema_filename in schema_filenames:
        schema_filepath = Path(schema_filename).resolve()

        task = asyncio.create_task(_async_validate_json_against_schemas_task(data, schema_filepath))
        tasks[task] = schema_filepath

    done, pending = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_EXCEPTION)

    for task in pending:
        task.cancel()

    for task in done:
        exception = task.exception()
        if exception:
            return False

    return True
