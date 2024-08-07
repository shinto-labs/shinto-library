"""Logging setup."""

import logging
import re
import sys
from importlib.util import find_spec

# Custom uvicorn logging config with propagate set to True.
# Default uvicorn log config: from uvicorn.config import LOGGING_CONFIG
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


SHINTO_LOG_FORMAT = (
    "time=%(asctime)s.%(msecs)03d+00:00 pid=%(process)06d "
    'name="%(application_name)s" logger_name="%(name)s" level="%(levelname)s" msg="%(message)s"'
)
SHINTO_LOG_DATEFMT = "%Y-%m-%dT%H:%M:%S"


class ShintoFormatter(logging.Formatter):
    """Custom log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log records, escaping double quotes.

        This method ensures that any double quotes in the log message are properly escaped.

        Args:
            record (logging.LogRecord): The log record to be formatted.

        Returns:
            str: The formatted log message with escaped double quotes.

        """
        # Retrieve the log message from the record
        message = record.getMessage()

        # Check for double quotes that are not already escaped
        if re.search(r'(?<!\\)"', message):
            # Escape all double quotes by another backslash
            message = message.replace('"', r"\"")

        # Update the log record with the modified message
        record.msg = message
        record.args = None

        # Call the superclass format method to perform standard formatting
        return super().format(record)


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

    # Get the root logger
    root_logger = logging.root

    # Set the log level
    root_logger.setLevel(loglevel)

    # Formatter for log messages
    formatter = ShintoFormatter(SHINTO_LOG_FORMAT, datefmt=SHINTO_LOG_DATEFMT)

    # Remove any existing handlers to avoid duplication
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

    # Setup stdout logging if requested
    if log_to_stdout:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        root_logger.addHandler(stdout_handler)

    # Setup file logging if requested
    if log_to_file and log_filename:
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Setup journald logging if requested
    if log_to_journald:
        try:
            if find_spec("JournalHandler") is None:
                # systemd is not available on all platforms (including Windows)
                from systemd.journal import JournalHandler  # type: ignore[reportMissingImports]

            journald_handler = JournalHandler()
            journald_handler.setFormatter(formatter)
            root_logger.addHandler(journald_handler)
        except ImportError:
            root_logger.exception(
                "Failed to import systemd.journal. Journal logging not available."
            )

    existing_record_factory = logging.getLogRecordFactory()

    def shinto_record_factory(*args: tuple, **kwargs: dict) -> logging.LogRecord:
        """
        Update log records after they are created.

        To make sure all loggers even loggers that are propagated have the desired properties,
        we use a log record factory to update the log record after it is created.
        """
        record = existing_record_factory(*args, **kwargs)

        record.application_name = application_name

        return record

    logging.setLogRecordFactory(shinto_record_factory)
