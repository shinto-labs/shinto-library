"""Tests for uvicorn entrypoint module."""

import unittest

from shinto.uvicorn_entrypoint import run_fastapi_app


class TestUvicornEntrypoint(unittest.TestCase):
    """Tests for uvicorn entrypoint module."""

    def test_run_fastapi_app(self):
        """Test run_fastapi_app function."""
        run_fastapi_app("test_app", "localhost", 8000, False)
