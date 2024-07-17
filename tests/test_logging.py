"""Test cases for the logging module."""

import logging
import tempfile
import unittest
from pathlib import Path

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
    startup_logging = None

    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        cls.temp_dir = tempfile.mkdtemp()

        cls.startup_logging = {
            **logging.Logger.manager.loggerDict,
            "root": logging.root,
        }

    @classmethod
    def tearDownClass(cls):
        """Tear down the test class."""
        # Reset the logging configuration
        for logger_name in logging.Logger.manager.loggerDict.copy():
            if logger_name not in cls.startup_logging:
                logger = logging.getLogger(logger_name)
                for handler in logger.handlers:
                    handler.close()
                logger.handlers.clear()

                if logger_name == logging.root.name:
                    # Reset the root logger
                    logging.Logger.manager.loggerDict.pop(logger_name)
                    logging.root = logging.RootLogger(cls.startup_logging["root"].level)
                    logging.Logger.root = cls.startup_logging["root"]
                    logging.Logger.manager.root = logging.root
                else:
                    logger.manager.loggerDict.pop(logger_name)

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
            r"TIME=\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}\+00:00 "
            r"PID=\d{6} "
            rf'NAME="{log_name}" '
            rf'LEVEL="{log_levelname}" '
            rf'MSG="{log_msg}"'
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
        log_filename = Path(self.temp_dir) / "myapp.log"
        if Path(log_filename).is_file():
            Path(log_filename).unlink()
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
        self.assertTrue(Path(log_filename).is_file())

        with Path(log_filename).open() as log_file:
            self.assertEqual(log_file.read(), "")

        logging.info(log_message)
        with Path(log_filename).open() as log_file:
            self.assertIn(log_message, log_file.read())

        def test_raise_value_error():
            msg = "Test exception"
            raise ValueError(msg)

        try:
            test_raise_value_error()
        except ValueError:
            logging.exception("Test exception")

        with Path(log_filename).open() as log_file:
            self.assertIn("raise ValueError(msg)", log_file.read())


if __name__ == "__main__":
    unittest.main()
