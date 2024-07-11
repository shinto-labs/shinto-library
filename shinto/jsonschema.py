"""Json schema validation functions."""

import asyncio
import json
import logging
from pathlib import Path

import anyio
import jsonschema


def validate_json_against_schemas(data: object, schema_filenames: list[str]) -> bool:
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


async def async_validate_json_against_schemas(data: object, schema_filenames: list[str]) -> bool:
    """Validate JSON data against JSON schemas."""
    tasks: dict[asyncio.Future, str] = {}
    loop = asyncio.get_event_loop()

    for schema_filename in schema_filenames:
        schema_filepath = Path(schema_filename).resolve()

        async with await anyio.open_file(schema_filepath, encoding="UTF-8") as file:
            schema = json.loads(await file.read())
            task = loop.run_in_executor(None, jsonschema.validate, data, schema)
            tasks[task] = schema_filepath

    done, pending = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_EXCEPTION)

    for task in pending:
        task.cancel()

    for task in done:
        schema_filepath = tasks[task]
        try:
            exception = task.exception()
            if exception:
                raise exception
        except jsonschema.SchemaError:
            logging.exception("JSON schema error in %s", schema_filepath)
            return False
        except jsonschema.ValidationError:
            logging.exception("JSON validation error in %s", schema_filepath)
            return False

    return True
