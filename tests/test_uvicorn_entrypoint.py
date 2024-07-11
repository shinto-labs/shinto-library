"""Tests for uvicorn entrypoint module."""

import ast
import http.client
import logging
import tempfile
import threading
import time
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from uvicorn.config import LOGGING_CONFIG

from shinto.uvicorn_entrypoint import run_fastapi_app_using_config

app = FastAPI()

root_message = {"Hello": "World"}


class UvicornServerError:
    """Uvicorn server error for test case."""

    def __init__():
        """Raise error."""
        msg = "Failed to start the FastAPI server."
        super().__init__(msg)


@app.get("/")
def root() -> JSONResponse:
    """Root endpoint."""
    return root_message


@app.get("/loggers")
def logger() -> JSONResponse:
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
        ],
    }


def wait_for_server_to_start(host: str, port: int, timeout: int = 5) -> bool:
    """Wait for the server to start by attempting to connect within a timeout period."""
    server_up = threading.Event()

    def check_server():
        while not server_up.is_set():
            try:
                conn = http.client.HTTPConnection(host, port)
                conn.request("HEAD", "/")
                conn.close()
                server_up.set()
            except ConnectionRefusedError:
                time.sleep(0.2)

    thread = threading.Thread(target=check_server)
    thread.start()
    server_up.wait(timeout)
    return server_up.is_set()


class TestUvicornEntrypoint(unittest.TestCase):
    """Tests for uvicorn entrypoint module."""

    port: int = None
    loglevel: int = None
    tempdir: str = None

    @classmethod
    def setUpClass(cls):
        """Set up the FastAPI app server in a separate thread and ensure it's ready."""
        cls.tempdir = tempfile.mkdtemp()
        cls.loglevel = logging.INFO
        logging.root.setLevel(cls.loglevel)

        cls.port = 40010
        host = "0.0.0.0"  # noqa: S104
        tempdir = tempfile.mkdtemp()
        config = {
            "logging": {
                "application_name": "TestApp",
                "loglevel": cls.loglevel,
                "log_to_stdout": True,
                "log_to_file": False,
                "log_to_journald": False,
                "log_filename": None,
            },
            "uvicorn": {
                "host": host,
                "port": cls.port,
                "reload": False,
            },
        }
        filepath = Path(tempdir) / "config.yaml"
        with Path(filepath).open("w") as file:
            file.write(str(config))
        server_thread_using_config = threading.Thread(
            target=run_fastapi_app_using_config,
            args=(app, filepath),
            daemon=True,
        )
        server_thread_using_config.start()
        if not wait_for_server_to_start("localhost", cls.port):
            raise UvicornServerError

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
