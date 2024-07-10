"""Logging setup."""

import logging
import sys
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
            from systemd.journal import JournalHandler  # type: ignore

            journald_handler = JournalHandler()
            journald_handler.setFormatter(formatter)
            logger.addHandler(journald_handler)
        except ImportError:
            logger.error("Failed to import systemd.journal. Journal logging not available.")

    logging.root = logger
