"""
Logging setup
"""
import logging
import sys


SHINTO_LOG_FORMAT = '%(asctime)s.%(msecs)03d - [%(process)06d] %(name)s - %(levelname)s - %(message)s'
SHINTO_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'


def setup_logging(
        application_name: str = None,
        loglevel: str = logging.WARNING,
        log_to_stdout: bool = True,
        log_to_file: bool = True,
        log_filename: str = None):
    """
    Setup logging, format etc.
    """
    if not application_name:
        application_name = sys.argv[0]

    # Create a logger
    logger = logging.getLogger(application_name)
    logger.setLevel(loglevel)

    # Formatter for log messages
    formatter = logging.Formatter(SHINTO_LOG_FORMAT, datefmt=SHINTO_LOG_DATEFMT)

    # Remove any existing handlers to avoid duplication (if you need to reconfigure the logging)
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

    logging.root = logger


def setup_uvicorn_log_config(
        loglevel: str = logging.WARNING,
        log_to_stdout: bool = True,
        log_to_file: bool = True,
        log_filename: str = None):
    """
    Setup logging for uvicorn
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
        handlers.update({"default": {"formatter": "default",
                        "class": "logging.StreamHandler", "stream": "ext://sys.stderr"}})
        loggers["uvicorn"]["handlers"].append("default")
        loggers["uvicorn.error"]["handlers"].append("default")
        handlers.update({"access": {"formatter": "default",
                        "class": "logging.StreamHandler", "stream": "ext://sys.stdout"}})
        loggers["uvicorn.access"]["handlers"].append("access")
    if log_to_file and log_filename:
        handlers.update(
            {"file": {"formatter": "default", "class": "logging.FileHandler", "filename": log_filename}})
        loggers["uvicorn"]["handlers"].append("file")
        loggers["uvicorn.error"]["handlers"].append("file")
        loggers["uvicorn.access"]["handlers"].append("file")
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        "loggers": loggers,
    }
