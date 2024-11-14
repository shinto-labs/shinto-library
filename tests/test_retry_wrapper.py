"""Tests for the retry wrapper module."""

import unittest
from unittest.mock import AsyncMock, MagicMock, call, patch

from shinto.retry_wrapper import retry, retry_call


class TestRetry(unittest.TestCase):
    """Test the retry decorator in sync and async contexts."""

    def test_retry_call_invalid_max_tries(self):
        """Test the retry decorator with an invalid max tries."""
        mock_func = MagicMock(return_value="Hello, World!")

        with self.assertRaises(ValueError):
            retry_call(mock_func, max_tries=-1)

    def test_retry_call_invalid_delay(self):
        """Test the retry decorator with an invalid delay."""
        mock_func = MagicMock(return_value="Hello, World!")

        with self.assertRaises(ValueError):
            retry_call(mock_func, delay=-1)

    def test_retry_call_invalid_backoff(self):
        """Test the retry decorator with an invalid backoff."""
        mock_func = MagicMock(return_value="Hello, World!")

        with self.assertRaises(ValueError):
            retry_call(mock_func, backoff=0)

    def test_retry_call_invalid_increment_delay(self):
        """Test the retry decorator with an invalid delay increment."""
        mock_func = MagicMock(return_value="Hello, World!")

        with self.assertRaises(ValueError):
            retry_call(mock_func, delay_increment=-1)

    def test_retry_call_invalid_max_delay(self):
        """Test the retry decorator with an invalid max delay."""
        mock_func = MagicMock(return_value="Hello, World!")

        with self.assertRaises(ValueError):
            retry_call(mock_func, max_delay=-1)


class TestRetrySync(unittest.TestCase):
    """Test the retry decorator."""

    @patch("shinto.retry_wrapper.time.sleep")
    def test_retry_success(self, mock_sleep: MagicMock):
        """Test a successful method."""

        @retry()
        def my_method() -> str:
            """Hello world mock method."""
            return "Hello, World!"

        result = my_method()
        self.assertEqual(result, "Hello, World!")
        mock_sleep.assert_not_called()

    @patch("shinto.retry_wrapper.time.sleep")
    def test_retry_call_success(self, mock_sleep: MagicMock):
        """Test a successful method."""
        mock_func = MagicMock(return_value="Mock Function Result")

        result = retry_call(mock_func)
        self.assertEqual(result, "Mock Function Result")
        mock_sleep.assert_not_called()

    @patch("shinto.retry_wrapper.time.sleep")
    def test_retry_call_success_fail_once(self, mock_sleep: MagicMock):
        """Test a successful method that fails once."""
        mock_func = MagicMock(
            side_effect=[Exception("Mock Function Exception"), "Mock Function Result"],
            __name__="mock_func",
        )

        result = retry_call(mock_func)
        self.assertEqual(result, "Mock Function Result")
        mock_sleep.assert_called_once()

    @patch("shinto.retry_wrapper.time.sleep")
    def test_retry_call_exception(self, mock_sleep: MagicMock):
        """Test a method that always raises an exception."""
        mock_func = MagicMock(side_effect=ValueError("Mock Function Exception"))

        with self.assertRaises(ValueError):
            retry_call(mock_func, max_tries=3)
        mock_func.assert_has_calls([call] * 3)
        mock_sleep.assert_has_calls([call(0.0)] * 2)

    @patch("shinto.retry_wrapper.time.sleep")
    def test_retry_call_unhandled_error(self, mock_sleep: MagicMock):
        """Test a method that always raises a ValueError."""
        mock_func = MagicMock(side_effect=ValueError("Mock Function KeyError"))

        with self.assertRaises(ValueError):
            retry_call(mock_func, max_tries=3, delay=1, exceptions=(KeyError,))
        mock_func.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("shinto.retry_wrapper.time.sleep")
    def test_valid_max_delay(self, mock_sleep: MagicMock):
        """Test a method with a valid max delay."""
        mock_func = MagicMock(
            side_effect=[Exception("Mock Function Exception"), "Mock Function Result"],
            __name__="mock_func",
        )

        result = retry_call(mock_func, delay=2.0, max_delay=1)
        self.assertEqual(result, "Mock Function Result")
        mock_sleep.assert_called_once_with(1.0)


class TestRetryAsync(unittest.IsolatedAsyncioTestCase):
    """Test the retry decorator with async methods."""

    @patch("shinto.retry_wrapper.asyncio.sleep", return_value=None)
    async def test_async_retry_success(self, mock_sleep: AsyncMock):
        """Test a successful method."""

        @retry()
        async def my_method() -> str:
            """Hello world mock method."""
            return "Hello, World!"

        result = await my_method()
        self.assertEqual(result, "Hello, World!")
        mock_sleep.assert_not_called()

    @patch("shinto.retry_wrapper.asyncio.sleep", return_value=None)
    async def test_async_retry_call_success(self, mock_sleep: AsyncMock):
        """Test a successful method."""
        mock_func = AsyncMock(return_value="Mock Function Result")

        result = await retry_call(mock_func)
        self.assertEqual(result, "Mock Function Result")
        mock_sleep.assert_not_called()

    @patch("shinto.retry_wrapper.asyncio.sleep", return_value=None)
    async def test_async_retry_call_success_fail_once(self, mock_sleep: AsyncMock):
        """Test a successful async method that fails once."""
        mock_func = AsyncMock(
            side_effect=[Exception("Mock Function Exception"), "Mock Function Result"],
            __name__="mock_func",
        )

        result = await retry_call(mock_func)
        self.assertEqual(result, "Mock Function Result")
        mock_sleep.assert_called_once()

    @patch("shinto.retry_wrapper.asyncio.sleep", return_value=None)
    async def test_async_retry_call_exception(self, mock_sleep: AsyncMock):
        """Test an async method that always raises an exception."""
        mock_func = AsyncMock(side_effect=ValueError("Mock Function Exception"))

        decorated_func = retry(max_tries=3)(mock_func)
        with self.assertRaises(ValueError):
            await decorated_func()
        mock_func.assert_has_calls([call] * 3)
        mock_sleep.assert_has_calls([call(0.0)] * 2)

    @patch("shinto.retry_wrapper.asyncio.sleep", return_value=None)
    async def test_async_retry_call_unhandled_error(self, mock_sleep: AsyncMock):
        """Test an async method that always raises a ValueError."""
        mock_func = AsyncMock(side_effect=ValueError("Mock Function KeyError"))

        with self.assertRaises(ValueError):
            await retry_call(mock_func, max_tries=3, delay=1, exceptions=(KeyError,))
        mock_func.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("shinto.retry_wrapper.asyncio.sleep", return_value=None)
    async def test_valid_max_delay(self, mock_sleep: AsyncMock):
        """Test an async method with a valid max delay."""
        mock_func = AsyncMock(
            side_effect=[Exception("Mock Function Exception"), "Mock Function Result"],
            __name__="mock_func",
        )

        result = await retry_call(mock_func, delay=2.0, max_delay=1)
        self.assertEqual(result, "Mock Function Result")
        mock_sleep.assert_called_once_with(1.0)


if __name__ == "__main__":
    unittest.main()
