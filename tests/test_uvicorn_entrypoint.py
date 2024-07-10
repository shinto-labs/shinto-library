"""Tests for uvicorn entrypoint module."""

import ast
import http.client
import logging
import threading
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


class TestUvicornEntrypoint(unittest.TestCase):
    """Tests for uvicorn entrypoint module."""

    def test_run_fastapi_app(self):
        """Test that the FastAPI app can be run."""
        server_thread = threading.Thread(
            target=run_fastapi_app, args=(app, "0.0.0.0", 40010, False), daemon=True
        )
        server_thread.start()
        self.assertTrue(server_thread.is_alive())

        conn = http.client.HTTPConnection("localhost", 40010)
        conn.request("GET", "/")
        response = conn.getresponse()
        response_data = ast.literal_eval(response.read().decode())
        conn.close()
        self.assertDictEqual(response_data, root_message)

    def test_logger_propagation(self):
        """Test that the loggers are set correctly."""
        loglevel = logging.INFO
        logging.root.setLevel(loglevel)
        server_thread = threading.Thread(
            target=run_fastapi_app, args=(app, "0.0.0.0", 40011, False), daemon=True
        )
        server_thread.start()
        self.assertTrue(server_thread.is_alive())

        conn = http.client.HTTPConnection("localhost", 40011)
        conn.request("GET", "/loggers")
        response = conn.getresponse()
        response_data = ast.literal_eval(response.read().decode())
        conn.close()
        for logger in response_data["loggers"]:
            if logger["name"] == "root":
                continue
            self.assertEqual(logger["level"], logging.getLevelName(loglevel))
            self.assertEqual(logger["propagate"], "True")
            self.assertListEqual(logger["handlers"], [])


if __name__ == "__main__":
    unittest.main()
