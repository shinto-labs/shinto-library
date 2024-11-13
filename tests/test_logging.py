"""Test cases for the logging module."""

import json
import logging
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

from shinto.logging import setup_logging


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

    @classmethod
    def tearDownClass(cls):
        """Tear down the test class."""
        logging.root.setLevel(logging.CRITICAL)

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

    def test_setup_logging(self):
        """Test setup_logging function with default parameters."""
        setup_logging()
        logger = logging.getLogger()
        self.assertEqual(logger.level, logging.WARNING)
        self.assertTrue(isinstance(logger.handlers[0], logging.StreamHandler))
        self.assertEqual(len(logger.handlers), 1)

    @patch("shinto.logging.sys.stdout", new_callable=StringIO)
    def test_log_to_stdout(self, mock_stdout: MagicMock):
        """Test setup_logging log message."""
        setup_logging("myapp")
        log_message = "Test log message"
        logging.warning(log_message)
        output = mock_stdout.getvalue().strip()
        self.assertIn(log_message, output)
        pattern = (
            r"time=\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}\+00:00 "
            r"pid=\d{6} "
            r'name="myapp" '
            r'logger_name="root" '
            r'level="warning" '
            rf'msg="{log_message}"'
        )
        self.assertRegex(output, pattern)

    @patch("shinto.logging.sys.stdout", new_callable=StringIO)
    def test_log_to_stdout_double_quotes(self, mock_stdout: MagicMock):
        """Test setup_logging log message with double quotes."""
        setup_logging()
        log_message = 'Test log message "with double quotes"'
        logging.warning(log_message)
        output = mock_stdout.getvalue().strip()
        escaped_log_message = log_message.replace('"', r"\"")
        self.assertIn(escaped_log_message, output)

    @patch("shinto.logging.sys.stdout", new_callable=StringIO)
    def test_log_to_stdout_escaped_double_quotes(self, mock_stdout: MagicMock):
        """Test setup_logging log message with escaped double quotes."""
        setup_logging()
        log_message = 'Test log message \\"with double quotes\\"'
        logging.warning(log_message)
        output = mock_stdout.getvalue().strip()
        self.assertIn(log_message, output)

    @patch("shinto.logging.sys.stdout", new_callable=StringIO)
    def test_log_to_stdout_json_dump(self, mock_stdout: MagicMock):
        """Test setup_logging log message with JSON dump."""
        setup_logging()
        log_message = json.dumps('Test log message "with double quotes"')[1:-1]
        logging.warning(log_message)
        output = mock_stdout.getvalue().strip()
        self.assertIn(log_message, output)

    @patch("shinto.logging.sys.stdout", new_callable=StringIO)
    def test_log_to_stdout_non_root_logger(self, mock_stdout: MagicMock):
        """Test setup_logging log message with escaped double quotes."""
        setup_logging()
        logger = logging.getLogger("test_logger")
        logger.propagate = True
        log_message = 'Test log message "with double quotes"'
        logger.warning(log_message)
        output = mock_stdout.getvalue().strip()
        escaped_log_message = log_message.replace('"', r"\"")
        self.assertIn(escaped_log_message, output)

    def test_log_to_file(self):
        """Test setup_logging function with log_to_file=True."""
        log_filename = Path(self.temp_dir) / "myapp.log"
        if log_filename.is_file():
            log_filename.unlink()
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
        self.assertTrue(log_filename.is_file())

        with log_filename.open() as log_file:
            self.assertEqual(log_file.read(), "")

        logging.info(log_message)
        with log_filename.open() as log_file:
            file_content = log_file.read()
            self.assertIn(log_message, file_content)

        def test_raise_value_error():
            msg = "Test exception"
            raise ValueError(msg)

        try:
            test_raise_value_error()
        except ValueError:
            logging.exception("Test exception")

        with log_filename.open() as log_file:
            self.assertIn("raise ValueError(msg)", log_file.read())

    def test_log_to_file_bytes(self):
        """Test setup_logging log message with bytes."""
        log_filename = Path(self.temp_dir) / "myapp2.log"
        setup_logging(
            application_name="myapp2",
            loglevel=logging.INFO,
            log_to_stdout=False,
            log_to_file=True,
            log_filename=log_filename,
        )
        log_message = json.dumps({"key": "value"}).encode()
        logging.info("Bytes: %s", log_message)
        with log_filename.open() as log_file:
            self.assertIn('msg="Bytes: b\'{\\"key\\": \\"value\\"}\'"', log_file.read())

    def test_uvicorn_logging(self):
        """Test setup_logging function with setup_uvicorn_logging=True."""
        setup_logging(setup_uvicorn_logging=True)
        logger = logging.getLogger()
        self.assertEqual(logger.level, logging.WARNING)
        self.assertTrue(isinstance(logger.handlers[0], logging.StreamHandler))
        self.assertEqual(len(logger.handlers), 1)
        for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
            uvicorn_logger = logging.getLogger(logger_name)
            self.assertEqual(uvicorn_logger.level, logging.WARNING)
            self.assertTrue(uvicorn_logger.propagate)
            self.assertEqual(len(uvicorn_logger.handlers), 0)


if __name__ == "__main__":
    unittest.main()
