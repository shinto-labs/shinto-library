"""Logging setup."""

import logging
import sys
import time
from importlib.util import find_spec

SHINTO_LOG_FORMAT = (
    "TIME=%(asctime)s.%(msecs)03d+00:00 PID=%(process)06d "
    'NAME="%(name)s" LEVEL="%(levelname)s" MSG="%(message)s"'
)
SHINTO_LOG_DATEFMT = "%Y-%m-%dT%H:%M:%S"

# Custom logging config based on uvicorn's default logging config
# from uvicorn.config import LOGGING_CONFIG  # noqa: ERA001
UVICORN_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {},
    "handlers": {},
    "loggers": {
        "uvicorn": {"level": "INFO", "handlers": [], "propagate": True},
        "uvicorn.error": {"level": "INFO", "handlers": [], "propagate": True},
        "uvicorn.access": {"level": "INFO", "handlers": [], "propagate": True},
    },
}


class ShintoFormatter(logging.Formatter):
    """Formatter for Shinto log messages."""

    def __init__(self, fmt: str, datefmt: str) -> None:
        """Initialize the formatter."""
        super().__init__(fmt, datefmt)
        self.converter = time.gmtime


def setup_logging(
    application_name: str | None = None,
    loglevel: str | int = logging.WARNING,
    log_to_stdout: bool = True,
    log_to_file: bool = True,
    log_to_journald: bool = False,
    log_filename: str | None = None,
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
                # systemd is not available on all platforms (including Windows)
                from systemd.journal import JournalHandler  # type: ignore[reportMissingImports]

            journald_handler = JournalHandler()
            journald_handler.setFormatter(formatter)
            logger.addHandler(journald_handler)
        except ImportError:
            logger.exception("Failed to import systemd.journal. Journal logging not available.")

    logging.root = logger
