"""Test cases for the logging module."""

import logging
import os
import tempfile
import unittest

from uvicorn.config import LOGGING_CONFIG as DEFAULT_UVICORN_LOGGING_CONFIG

from shinto.logging import (
    SHINTO_LOG_DATEFMT,
    SHINTO_LOG_FORMAT,
    UVICORN_LOGGING_CONFIG,
    ShintoFormatter,
    setup_logging,
)


class TestLogging(unittest.TestCase):
    """Test the logging module."""

    temp_dir = None

    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        cls.temp_dir = tempfile.mkdtemp()

    def test_uvicorn_logging_config(self):
        """Test UVICORN_LOGGING_CONFIG dictionary."""
        self.assertEqual(
            len(UVICORN_LOGGING_CONFIG["loggers"]),
            len(DEFAULT_UVICORN_LOGGING_CONFIG["loggers"]),
        )

        for logger_config in UVICORN_LOGGING_CONFIG["loggers"].values():
            self.assertEqual(logger_config["level"], "INFO")

        for logger_config in UVICORN_LOGGING_CONFIG["loggers"].values():
            self.assertTrue(logger_config["propagate"])

    def test_shinto_formatter(self):
        """Test ShintoFormatter class."""
        formatter = ShintoFormatter(SHINTO_LOG_FORMAT, datefmt=SHINTO_LOG_DATEFMT)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test log message",
            args=None,
            exc_info=None,
        )
        log_contents = formatter.format(record)

        log_levelname = record.levelname
        log_name = record.name
        log_msg = record.getMessage()

        pattern = (
            r"time=\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}\+00:00 "
            r"pid=\d{6} "
            rf'name="{log_name}" '
            rf'level="{log_levelname}" '
            rf'msg="{log_msg}"'
        )
        self.assertRegex(log_contents, pattern)

    def test_setup_logging(self):
        """Test setup_logging function with default parameters."""
        setup_logging()
        logger = logging.getLogger()
        self.assertEqual(logger.level, logging.WARNING)
        self.assertTrue(isinstance(logger.handlers[0], logging.StreamHandler))
        self.assertEqual(len(logger.handlers), 1)

    def test_log_to_file(self):
        log_filename = os.path.join(self.temp_dir, "myapp.log")
        if os.path.isfile(log_filename):
            os.remove(log_filename)
        log_message = "Test log message"
        setup_logging(
            application_name="myapp",
            loglevel=logging.DEBUG,
            log_to_stdout=False,
            log_to_file=True,
            log_filename=log_filename,
        )

        logger = logging.getLogger("myapp")
        self.assertEqual(logger.level, logging.DEBUG)
        self.assertTrue(isinstance(logger.handlers[0], logging.FileHandler))
        self.assertEqual(len(logger.handlers), 1)
        self.assertTrue(os.path.isfile(log_filename))

        with open(log_filename) as log_file:
            self.assertEqual(log_file.read(), "")

        logging.info(log_message)
        with open(log_filename) as log_file:
            self.assertIn(log_message, log_file.read())

        try:
            raise ValueError("Test exception")
        except ValueError:
            logging.exception("Test exception")

        with open(log_filename) as log_file:
            self.assertIn('raise ValueError("Test exception")', log_file.read())


if __name__ == "__main__":
    unittest.main()
