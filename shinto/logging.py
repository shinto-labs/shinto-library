"""Logging setup."""

import logging
import sys
from importlib.util import find_spec
from typing import Union

SHINTO_LOG_FORMAT = (
    "%(asctime)s.%(msecs)03d - [%(process)06d] %(name)s - %(levelname)s - %(message)s"
)
SHINTO_LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    application_name: str = None,
    loglevel: Union[str, int] = logging.WARNING,
    log_to_stdout: bool = True,
    log_to_file: bool = True,
    log_to_journald: bool = False,
    log_filename: str = None,
):
    """Set up logging, format etc."""
    if not application_name:
        application_name = sys.argv[0]

    # Create a logger
    logger = logging.getLogger(application_name)
    logger.setLevel(loglevel)

    # Formatter for log messages
    formatter = logging.Formatter(SHINTO_LOG_FORMAT, datefmt=SHINTO_LOG_DATEFMT)

    # Remove any existing handlers to avoid duplication
    for handler in logger.handlers:
        logger.removeHandler(handler)

    # Setup stdout logging if requested
    if log_to_stdout:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)

    # Setup file logging if requested
    if log_to_file and log_filename:
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Setup journald logging if requested
    if log_to_journald:
        try:
            if find_spec("JournalHandler") is None:
                from systemd.journal import JournalHandler  # noqa: F401 I001

            journald_handler = JournalHandler()
            journald_handler.setFormatter(formatter)
            logger.addHandler(journald_handler)
        except ImportError:
            logger.error("Failed to import systemd.journal. Journal logging not available.")

    logging.root = logger

def generate_uvicorn_log_config(
    loglevel: Union[str, int] = logging.WARNING,
    log_to_stdout: bool = True,
    log_to_file: bool = True,
    log_to_journald: bool = False,
    log_filename: str = None,
) -> dict:
    """Generate logging configuration for uvicorn.

    Args:
        loglevel: Log level for the logger.
        Can be specified as a string (e.g., "info", "warning")
        or as an integer (e.g. logging.INFO, logging.WARNING).
        See Uvicorn LOG_LEVELS for more details.
        log_to_stdout: Should logs be written to stdout.
        log_to_file: Should logs be written to a file.
        log_to_journald: Should logs be written to journald.
        log_filename: If provided, and log_to_file is True, logs will be written to this file.

    Returns:
        Logging configuration for Uvicorn.

    """
    formatters = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": SHINTO_LOG_FORMAT,
            "datefmt": SHINTO_LOG_DATEFMT,
        },
    }
    handlers = {}
    loggers = {
        "uvicorn": {"handlers": [], "level": loglevel, "propagate": False},
        "uvicorn.error": {"handlers": [], "level": loglevel, "propagate": False},
        "uvicorn.access": {"handlers": [], "level": loglevel, "propagate": False},
    }

    if log_to_stdout:
        handlers.update(
            {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                }
            }
        )
        loggers["uvicorn"]["handlers"].append("default")
        loggers["uvicorn.error"]["handlers"].append("default")
        handlers.update(
            {
                "access": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                }
            }
        )
        loggers["uvicorn.access"]["handlers"].append("access")

    if log_to_file and log_filename:
        handlers.update(
            {
                "file": {
                    "formatter": "default",
                    "class": "logging.FileHandler",
                    "filename": log_filename,
                }
            }
        )
        for logger_value in loggers.values():
            logger_value["handlers"].append("file")

    if log_to_journald:
        try:
            if find_spec("JournalHandler") is None:
                from systemd.journal import JournalHandler  # noqa: F401 I001
            handlers.update(
                {
                    "journald": {
                        "formatter": "default",
                        "class": "systemd.journal.JournalHandler",
                    }
                }
            )
            for logger_value in loggers.values():
                logger_value["handlers"].append("journald")
        except ImportError:
            loggers["uvicorn"]["level"] = "ERROR"
            loggers["uvicorn.error"]["level"] = "ERROR"
            loggers["uvicorn.access"]["level"] = "ERROR"
            loggers["uvicorn"]["handlers"] = []
            loggers["uvicorn.error"]["handlers"] = []
            loggers["uvicorn.access"]["handlers"] = []

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        "loggers": loggers,
    }
