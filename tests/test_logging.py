"""Test cases for the logging module."""

import logging
import unittest

from shinto.logging import setup_logging


class TestLogging(unittest.TestCase):
    """Test the logging module."""

    def test_setup_logging(self):
        """Test setup_logging function with default parameters."""
        setup_logging()
        logger = logging.getLogger()
        self.assertEqual(logger.level, logging.WARNING)
        self.assertTrue(isinstance(logger.handlers[0], logging.StreamHandler))
        self.assertEqual(len(logger.handlers), 1)

        # Test setup_logging function with custom parameters
        setup_logging(
            application_name="myapp",
            loglevel=logging.DEBUG,
            log_to_stdout=False,
            log_to_file=True,
            log_filename="app.log",
        )
        logger = logging.getLogger("myapp")
        self.assertEqual(logger.level, logging.DEBUG)
        self.assertTrue(isinstance(logger.handlers[0], logging.FileHandler))
        self.assertEqual(len(logger.handlers), 1)


if __name__ == "__main__":
    unittest.main()
