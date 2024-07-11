"""Json schema validation functions."""

import asyncio
import json
import logging
import os

import jsonschema


def validate_json_against_schemas(data: object, schema_filenames: list[str]):
    """Validate JSON data against JSON schemas."""
    validate_ok = True

    for schema_filename in schema_filenames:
        schema_filename = os.path.abspath(schema_filename)

        with open(schema_filename, encoding="UTF-8") as file:
            schema = json.load(file)
            try:
                jsonschema.validate(data, schema)
            except jsonschema.SchemaError as e:
                logging.error("JSON schema error in %s: %s", schema_filename, str(e))
                validate_ok = False
            except jsonschema.ValidationError as e:
                logging.error("JSON validation error in %s: %s", schema_filename, str(e))
                validate_ok = False

    return validate_ok


async def async_validate_json_against_schemas(data: object, schema_filenames: list[str]):
    """Validate JSON data against JSON schemas."""
    validate_ok = True

    tasks: dict[asyncio.Future, str] = {}
    loop = asyncio.get_event_loop()

    for schema_filename in schema_filenames:
        schema_filename = os.path.abspath(schema_filename)

        with open(schema_filename, encoding="UTF-8") as file:
            schema = json.load(file)
            task = loop.run_in_executor(None, jsonschema.validate, data, schema)
            tasks[task] = schema_filename

    done, pending = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_EXCEPTION)

    for task in pending:
        task.cancel()

    for task in done:
        schema_filename = tasks[task]
        exception = task.exception()
        if exception:
            if isinstance(exception, jsonschema.SchemaError):
                logging.error("JSON schema error in %s: %s", schema_filename, str(exception))
            elif isinstance(exception, jsonschema.ValidationError):
                logging.error("JSON validation error in %s: %s", schema_filename, str(exception))
            validate_ok = False

    return validate_ok
