"""Tests for uvicorn entrypoint module."""

import ast
import http.client
import logging
import threading
import time
import unittest

from fastapi import FastAPI
from uvicorn.config import LOGGING_CONFIG

from shinto.uvicorn_entrypoint import run_fastapi_app

app = FastAPI()

root_message = {"Hello": "World"}


@app.get("/")
def root():
    """Root endpoint."""
    return root_message


@app.get("/loggers")
def logger():
    """Loggers endpoint."""
    loggers = [logging.getLogger(logger) for logger in [None, *LOGGING_CONFIG["loggers"].keys()]]
    return {
        "loggers": [
            {
                "name": logger.name if logger.name != logging.root.name else "root",
                "level": logging.getLevelName(logger.level),
                "propagate": str(logger.propagate),
                "parent": logger.parent.name if logger.parent else "None",
                "handlers": [str(handler.name) for handler in logger.handlers],
            }
            for logger in loggers
        ]
    }


def wait_for_server_to_start(host, port, timeout=5):
    """Wait for the server to start by attempting to connect within a timeout period."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            conn = http.client.HTTPConnection(host, port)
            conn.request("HEAD", "/")
            conn.close()
            return True
        except ConnectionRefusedError:
            time.sleep(0.2)
    return False


class TestUvicornEntrypoint(unittest.TestCase):
    """Tests for uvicorn entrypoint module."""

    server_thread = None
    loglevel: int = None
    port: int = None

    @classmethod
    def setUpClass(cls):
        """Set up the FastAPI app server in a separate thread and ensure it's ready."""
        cls.loglevel = logging.INFO
        cls.port = 40010
        logging.root.setLevel(cls.loglevel)
        cls.server_thread = threading.Thread(
            target=run_fastapi_app, args=(app, "0.0.0.0", cls.port, False), daemon=True
        )
        cls.server_thread.start()
        if not wait_for_server_to_start("localhost", cls.port):
            raise Exception("Failed to start the FastAPI server.")

    def test_run_fastapi_app(self):
        """Test that the FastAPI app can be run."""
        conn = http.client.HTTPConnection("localhost", self.port)
        conn.request("GET", "/")
        response = conn.getresponse()
        response_data = ast.literal_eval(response.read().decode())
        conn.close()
        self.assertDictEqual(response_data, root_message)

    def test_logger_propagation(self):
        """Test that the loggers are set correctly."""
        conn = http.client.HTTPConnection("localhost", self.port)
        conn.request("GET", "/loggers")
        response = conn.getresponse()
        response_data = ast.literal_eval(response.read().decode())
        conn.close()
        for logger in response_data["loggers"]:
            if logger["name"] == "root":
                continue
            self.assertEqual(logger["level"], logging.getLevelName(self.loglevel))
            self.assertEqual(logger["propagate"], "True")
            self.assertListEqual(logger["handlers"], [])


if __name__ == "__main__":
    unittest.main()
