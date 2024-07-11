"""Uvicorn entrypoint module for FastAPI applications."""

import copy
import logging
from collections.abc import Callable
from typing import Any

from .config import load_config_file
from .logging import setup_logging

try:
    import uvicorn
    from uvicorn._types import ASGIApplication
    from uvicorn.config import LOGGING_CONFIG
except ImportError as e:
    msg = "Uvicorn module requires shinto['uvicorn'] or shinto['all'] extras."
    raise ImportError(msg) from e


def run_fastapi_app(
    app: ASGIApplication | Callable[..., Any] | str,
    host: str,
    port: int,
    reload: bool,
    logger: logging.Logger | None = None,
):
    """
    Run the uvicorn server with the given FastApi app.

    Args:
        app: FastAPI application path e.g. src.app:app or FastAPI instance.
        host: Host to run the server on.
        port: Port to run the server on.
        reload: Enable auto-reload.
        logger: Logger to use for the uvicorn server.

    """
    logger = logger or logging.root

    log_config = copy.deepcopy(LOGGING_CONFIG)
    for uvicorn_logger in log_config["loggers"]:
        log_config["loggers"][uvicorn_logger]["handlers"] = []
        log_config["loggers"][uvicorn_logger]["level"] = logger.level
        log_config["loggers"][uvicorn_logger]["propagate"] = True
    log_config["formatters"] = {}
    log_config["handlers"] = {}

    logging.info("Starting uvicorn server with log config: %s", log_config)

    uvicorn.run(app=app, host=host, port=port, log_config=log_config, reload=reload)


def run_fastapi_app_using_config(
    app: ASGIApplication | Callable[..., Any] | str,
    config_filename: str,
    start_element: list[str] | None = None,
):
    """
    Run the uvicorn server with the given config file.

    Args:
        app: FastAPI application path e.g. src.app:app or FastAPI instance.
        config_filename: Path to the config file.
        start_element: Path to the database connection parameters in the configuration file.
        Should be used if the connection parameters are not at the root level of the config file.

    The configuration file should have the following parameters:
        logging:
            application_name: Name of the application.
            loglevel: Log level.
            log_to_stdout: Log to stdout.
            log_to_file: Log to file.
            log_to_journald: Log to journald.
            log_filename: Log file name.
        uvicorn:
            host: Host to run the server on.
            port: Port to run the server on.
            reload: Enable auto-reload.

    """
    required_params = {
        "logging": {
            "application_name": None,
            "loglevel": None,
            "log_to_stdout": None,
            "log_to_file": None,
            "log_to_journald": None,
            "log_filename": None,
        },
        "uvicorn": {
            "host": None,
            "port": None,
            "reload": None,
        },
    }

    config = load_config_file(
        config_filename,
        required_params=required_params,
        start_element=start_element,
    )

    setup_logging(**config["logging"])

    run_fastapi_app(app, **config["uvicorn"])
