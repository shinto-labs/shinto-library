"""Test cases for the logging module."""

import logging
import tempfile
import unittest
from pathlib import Path

from shinto.logging import (
    UVICORN_LOGGING_CONFIG,
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

        # Store the initial logging configuration
        cls.startup_logging = {
            **logging.Logger.manager.loggerDict,
            "root": logging.root,
        }

    def tearDown(self) -> None:
        """Tear down the test method."""
        # Reset the logging configuration
        for logger_name in logging.Logger.manager.loggerDict.copy():
            if logger_name not in self.startup_logging:
                logger = logging.getLogger(logger_name)
                for handler in logger.handlers:
                    handler.close()
                logger.handlers.clear()

                if logger_name == logging.root.name:
                    # Reset the root logger
                    logging.Logger.manager.loggerDict.pop(logger_name)
                    logging.root = logging.RootLogger(self.startup_logging["root"].level)
                    logging.Logger.root = self.startup_logging["root"]
                    logging.Logger.manager.root = logging.root
                else:
                    logger.manager.loggerDict.pop(logger_name)

    def test_uvicorn_logging_config(self):
        """Test UVICORN_LOGGING_CONFIG dictionary."""
        for logger_config in UVICORN_LOGGING_CONFIG["loggers"].values():
            self.assertEqual(logger_config["level"], "INFO")

        for logger_config in UVICORN_LOGGING_CONFIG["loggers"].values():
            self.assertTrue(logger_config["propagate"])

    def test_setup_logging(self):
        """Test setup_logging function with default parameters."""
        setup_logging()
        logger = logging.getLogger()
        self.assertEqual(logger.level, logging.WARNING)
        self.assertTrue(isinstance(logger.handlers[0], logging.StreamHandler))
        self.assertEqual(len(logger.handlers), 1)

    def test_log_to_file(self):
        """Test setup_logging function with log_to_file=True."""
        log_filename = Path(self.temp_dir) / "myapp.log"
        if Path(log_filename).is_file():
            Path(log_filename).unlink()
        log_message = "Test log message"
        setup_logging(
            application_name="myapp",
            loglevel=logging.INFO,
            log_to_stdout=False,
            log_to_file=True,
            log_filename=log_filename,
        )

        logger = logging.root
        self.assertEqual(logger.level, logging.INFO)
        self.assertTrue(isinstance(logger.handlers[0], logging.FileHandler))
        self.assertEqual(len(logger.handlers), 1)
        self.assertTrue(Path(log_filename).is_file())

        with Path(log_filename).open() as log_file:
            self.assertEqual(log_file.read(), "")

        logging.info(log_message)
        pattern = (
            r"time=\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}\+00:00 "
            r"pid=\d{6} "
            r'name="myapp" '
            r'logger_name="root" '
            r'level="INFO" '
            rf'msg="{log_message}"'
        )
        with Path(log_filename).open() as log_file:
            file_content = log_file.read()
            self.assertIn(log_message, file_content)
            self.assertRegex(file_content, pattern)

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
