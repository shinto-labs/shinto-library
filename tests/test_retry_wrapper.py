"""Tests for the retry wrapper module."""

import unittest
from unittest.mock import AsyncMock, MagicMock, call, patch

from shinto.retry_wrapper import RetryError, retry


class TestRetryDecorator(unittest.TestCase):
    """Test the retry decorator."""

    @patch("shinto.retry_wrapper.time.sleep", return_value=None)
    def test_sync_retry_success(self, mock_sleep: MagicMock):
        """Test a successful sync method."""
        mock_func = MagicMock(return_value="Mock Function Result")

        decorated_func = retry(max_retries=3, delay=1, backoff=1, exceptions=(Exception,))(
            mock_func
        )
        result = decorated_func()
        self.assertEqual(result, "Mock Function Result")
        mock_sleep.assert_not_called()

    @patch("shinto.retry_wrapper.time.sleep", return_value=None)
    def test_sync_retry_success_fail_once(self, mock_sleep: MagicMock):
        """Test a successful sync method that fails once."""
        mock_func = MagicMock(
            side_effect=[Exception("Mock Function Exception"), "Mock Function Result"],
            __name__="mock_func",
        )

        decorated_func = retry(max_retries=3, delay=1, backoff=1, exceptions=(Exception,))(
            mock_func
        )
        result = decorated_func()
        self.assertEqual(result, "Mock Function Result")
        mock_sleep.assert_called_once_with(1)

    @patch("shinto.retry_wrapper.time.sleep", return_value=None)
    def test_sync_retry_exception(self, mock_sleep: MagicMock):
        """Test a sync method that always raises an exception."""
        mock_func = MagicMock(side_effect=Exception("Mock Function Exception"))

        decorated_func = retry(max_retries=3, delay=1, backoff=1, exceptions=(Exception,))(
            mock_func
        )
        with self.assertRaises(RetryError):
            decorated_func()
        mock_func.assert_has_calls([call] * 3)
        mock_sleep.assert_has_calls([call(1)] * 2)

    @patch("shinto.retry_wrapper.time.sleep", return_value=None)
    def test_sync_retry_with_exception_backoff(self, mock_sleep: MagicMock):
        """Test a sync method that always raises an exception and uses a backoff factor."""
        mock_func = MagicMock(side_effect=Exception("Mock Function Exception"))

        decorated_func = retry(max_retries=3, delay=1, backoff=2, exceptions=(Exception,))(
            mock_func
        )
        with self.assertRaises(RetryError):
            decorated_func()
        mock_func.assert_has_calls([call] * 3)
        mock_sleep.assert_has_calls([call(1), call(2)])

    @patch("shinto.retry_wrapper.time.sleep", return_value=None)
    def test_sync_retry_unhandled_error(self, mock_sleep: MagicMock):
        """Test a sync method that always raises a KeyError."""
        mock_func = MagicMock(side_effect=ValueError("Mock Function KeyError"))

        decorated_func = retry(max_retries=3, delay=1, backoff=1, exceptions=(KeyError,))(mock_func)
        with self.assertRaises(ValueError):
            decorated_func()
        mock_func.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("shinto.retry_wrapper.time.sleep", return_value=None)
    def test_sync_retry_decorator_approach(self, mock_sleep: MagicMock):
        """Test the retry decorator approach."""

        @retry(max_retries=3, delay=1, backoff=1, exceptions=(Exception,))
        def my_method() -> str:
            """Hello world mock method."""
            return "Hello, World!"

        result = my_method()
        self.assertEqual(result, "Hello, World!")
        mock_sleep.assert_not_called()

    @patch("shinto.retry_wrapper.time.sleep", return_value=None)
    def test_sync_retry_decorator_approach_exception(self, mock_sleep: MagicMock):
        """Test the retry decorator approach with an exception."""

        @retry(max_retries=3, delay=1, backoff=1, exceptions=(Exception,))
        def my_method() -> str:
            """Hello world mock method."""
            raise KeyError("Mock Exception")

        with self.assertRaises(RetryError):
            my_method()
        mock_sleep.assert_has_calls([call(1)] * 2)

    @patch("shinto.retry_wrapper.time.sleep", return_value=None)
    def test_sync_retry_decorator_approach_with_params(self, mock_sleep: MagicMock):
        """Test the retry decorator with a function that takes parameters."""

        @retry(max_retries=3, delay=1, backoff=1, exceptions=(Exception,))
        def my_method(param: int) -> str:
            """Hello world mock method."""
            return f"Hello, World! {param}"

        result = my_method(1)
        self.assertEqual(result, "Hello, World! 1")
        mock_sleep.assert_not_called()

    @patch("shinto.retry_wrapper.time.sleep", return_value=None)
    def test_sync_retry_invalid_delay(self, mock_sleep: MagicMock):
        """Test the retry decorator with an invalid delay."""
        with self.assertRaises(ValueError):

            @retry(max_retries=3, delay=-1, backoff=1, exceptions=(Exception,))
            def my_method() -> str:
                """Hello world mock method."""
                return "Hello, World!"

        mock_sleep.assert_not_called()

    @patch("shinto.retry_wrapper.time.sleep", return_value=None)
    def test_sync_retry_invalid_backoff(self, mock_sleep: MagicMock):
        """Test the retry decorator with an invalid backoff."""
        with self.assertRaises(ValueError):

            @retry(max_retries=3, delay=1, backoff=0, exceptions=(Exception,))
            def my_method() -> str:
                """Hello world mock method."""
                return "Hello, World!"

        mock_sleep.assert_not_called()


class TestRetryDecoratorAsync(unittest.IsolatedAsyncioTestCase):
    """Test the retry decorator with async methods."""

    @patch("shinto.retry_wrapper.asyncio.sleep", return_value=None)
    async def test_async_retry_success(self, mock_sleep: AsyncMock):
        """Test a successful sync method."""
        mock_func = AsyncMock(return_value="Mock Function Result")

        decorated_func = retry(max_retries=3, delay=1, backoff=1, exceptions=(Exception,))(
            mock_func
        )
        result = await decorated_func()
        self.assertEqual(result, "Mock Function Result")
        mock_sleep.assert_not_called()

    @patch("shinto.retry_wrapper.asyncio.sleep", return_value=None)
    async def test_async_retry_success_fail_once(self, mock_sleep: AsyncMock):
        """Test a successful async method that fails once."""
        mock_func = AsyncMock(
            side_effect=[Exception("Mock Function Exception"), "Mock Function Result"],
            __name__="mock_func",
        )

        decorated_func = retry(max_retries=3, delay=1, backoff=1, exceptions=(Exception,))(
            mock_func
        )
        result = await decorated_func()
        self.assertEqual(result, "Mock Function Result")
        mock_sleep.assert_called_once_with(1)

    @patch("shinto.retry_wrapper.asyncio.sleep", return_value=None)
    async def test_async_retry_exception(self, mock_sleep: AsyncMock):
        """Test an async method that always raises an exception."""
        mock_func = AsyncMock(side_effect=Exception("Mock Function Exception"))

        decorated_func = retry(max_retries=3, delay=1, backoff=1, exceptions=(Exception,))(
            mock_func
        )
        with self.assertRaises(RetryError):
            await decorated_func()
        mock_func.assert_has_calls([call] * 3)
        mock_sleep.assert_has_calls([call(1)] * 2)

    @patch("shinto.retry_wrapper.asyncio.sleep", return_value=None)
    async def test_async_retry_with_exception_backoff(self, mock_sleep: AsyncMock):
        """Test an async method that always raises an exception and uses a backoff factor."""
        mock_func = AsyncMock(side_effect=Exception("Mock Function Exception"))

        decorated_func = retry(max_retries=3, delay=1, backoff=2, exceptions=(Exception,))(
            mock_func
        )
        with self.assertRaises(RetryError):
            await decorated_func()
        mock_func.assert_has_calls([call] * 3)
        mock_sleep.assert_has_calls([call(1), call(2)])

    @patch("shinto.retry_wrapper.asyncio.sleep", return_value=None)
    async def test_async_retry_unhandled_error(self, mock_sleep: AsyncMock):
        """Test an async method that always raises a ValueError."""
        mock_func = AsyncMock(side_effect=ValueError("Mock Function KeyError"))

        decorated_func = retry(max_retries=3, delay=1, backoff=1, exceptions=(KeyError,))(mock_func)
        with self.assertRaises(ValueError):
            await decorated_func()
        mock_func.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("shinto.retry_wrapper.asyncio.sleep", return_value=None)
    async def test_async_retry_decorator_approach(self, mock_sleep: AsyncMock):
        """Test the retry decorator approach with an async method."""

        @retry(max_retries=3, delay=1, backoff=1, exceptions=(Exception,))
        async def my_method() -> str:
            """Hello world mock method."""
            return "Hello, World!"

        result = await my_method()
        self.assertEqual(result, "Hello, World!")
        mock_sleep.assert_not_called()

    @patch("shinto.retry_wrapper.asyncio.sleep", return_value=None)
    async def test_async_retry_decorator_approach_exception(self, mock_sleep: AsyncMock):
        """Test the retry decorator approach with an async method that raises an exception."""

        @retry(max_retries=3, delay=1, backoff=1, exceptions=(Exception,))
        async def my_method() -> str:
            """Hello world mock method."""
            raise KeyError("Mock Exception")

        with self.assertRaises(RetryError):
            await my_method()
        mock_sleep.assert_has_calls([call(1)] * 2)

    @patch("shinto.retry_wrapper.asyncio.sleep", return_value=None)
    async def test_async_retry_decorator_approach_with_params(self, mock_sleep: AsyncMock):
        """Test the retry decorator with an async function that takes parameters."""

        @retry(max_retries=3, delay=1, backoff=1, exceptions=(Exception,))
        async def my_method(param: int) -> str:
            """Hello world mock method."""
            return f"Hello, World! {param}"

        result = await my_method(1)
        self.assertEqual(result, "Hello, World! 1")
        mock_sleep.assert_not_called()

    @patch("shinto.retry_wrapper.asyncio.sleep", return_value=None)
    async def test_async_retry_invalid_delay(self, mock_sleep: AsyncMock):
        """Test the retry decorator with an invalid delay."""
        with self.assertRaises(ValueError):

            @retry(max_retries=3, delay=-1, backoff=1, exceptions=(Exception,))
            async def my_method() -> str:
                """Hello world mock method."""
                return "Hello, World!"

        mock_sleep.assert_not_called()

    @patch("shinto.retry_wrapper.asyncio.sleep", return_value=None)
    async def test_async_retry_invalid_backoff(self, mock_sleep: AsyncMock):
        """Test the retry decorator with an invalid backoff."""
        with self.assertRaises(ValueError):

            @retry(max_retries=3, delay=1, backoff=0, exceptions=(Exception,))
            async def my_method() -> str:
                """Hello world mock method."""
                return "Hello, World!"

        mock_sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
