"""Logging setup."""

from __future__ import annotations

import logging
import logging.config
import re
import sys

SHINTO_LOG_FORMAT = (
    "time=%(asctime)s.%(msecs)03d+00:00 pid=%(process)06d "
    'name="%(application_name)s" logger_name="%(name)s" level="%(levelname)s" msg="%(message)s"'
)
SHINTO_LOG_DATEFMT = "%Y-%m-%dT%H:%M:%S"


class _ShintoFormatter(logging.Formatter):
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

        # Lowercase the log level name
        record.levelname = record.levelname.lower()

        # Call the superclass format method to perform standard formatting
        return super().format(record)


def setup_logging(
    application_name: str | None = None,
    loglevel: str | int = logging.WARNING,
    log_to_stdout: bool = True,
    log_to_file: bool = True,
    log_to_journald: bool = False,
    log_filename: str | None = None,
    setup_uvicorn_logging: bool = False,
):
    """
    Set up logging for the application.

    If log_to_file is True, log_filename must be provided in order to log to a file.

    Args:
        application_name (str | None): The "name" to display in the logs. Defaults to sys.argv[0].
        loglevel (str | int): The log level to use. Defaults to logging.WARNING.
        log_to_stdout (bool): Whether to log to stdout. Defaults to True.
        log_to_file (bool): Whether to log to a file. Defaults to True.
        log_to_journald (bool): Whether to log to journald. Defaults to False.
        log_filename (str | None): The filename to log to. Defaults to None.
        setup_uvicorn_logging (bool): Whether to setup uvicorn logging. Defaults to False.

    Example:
        >>> setup_logging(application_name="myapp", loglevel=logging.INFO)

    """
    if not application_name:
        application_name = sys.argv[0]

    root_logger = logging.root
    root_logger.setLevel(loglevel)

    formatter = _ShintoFormatter(SHINTO_LOG_FORMAT, datefmt=SHINTO_LOG_DATEFMT)

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
    # systemd is not available on all platforms (including Windows)
    if log_to_journald:  # pragma: no cover
        from systemd.journal import JournalHandler  # pyright: ignore[reportMissingImports]  # noqa: F401, I001, PLC0415, RUF100

        journald_handler = JournalHandler()
        journald_handler.setFormatter(formatter)
        root_logger.addHandler(journald_handler)

    # Update the log record factory to include the application name
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

    # Setup uvicorn logging if requested
    if setup_uvicorn_logging:
        # Custom uvicorn logging config with propagate set to True.
        # Default uvicorn log config: from uvicorn.config import LOGGING_CONFIG
        loglevel = logging.getLevelName(loglevel) if not isinstance(loglevel, str) else loglevel
        uvicorn_logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {},
            "handlers": {},
            "loggers": {
                "uvicorn": {"level": loglevel, "handlers": [], "propagate": True},
                "uvicorn.error": {"level": loglevel, "handlers": [], "propagate": True},
                "uvicorn.access": {"level": loglevel, "handlers": [], "propagate": True},
            },
        }
        logging.config.dictConfig(uvicorn_logging_config)
