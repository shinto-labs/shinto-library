from shinto import setup_logging
import logging

setup_logging(application_name="shinto-integration-tests")

def test_setup_logging():
    logger = logging.getLogger(__name__)
    logger.info("Test logging")
    assert logger.level == logging.INFO

if __name__ == "__main__":
    test_setup_logging()