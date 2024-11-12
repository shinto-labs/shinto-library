"""A wrapper to retry a method if it fails."""

from __future__ import annotations

import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable


class RetryError(Exception):
    """An exception raised when the maximum number of retries is reached."""


def retry(
    max_retries: int = 3,
    delay: int = 1,
    backoff: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[..., Any]:
    """
    Retry a method if it fails.

    Retries a method if it raises an exception specified in the `exceptions` tuple.
    The method is retried up to `max_retries` times with a delay of `delay` seconds between retries.
    The delay between retries is increased by a factor of `backoff`
    with a maximum delay of 3600 seconds.

    Args:
        max_retries: The maximum number of retries.
        delay: The delay between retries.
        backoff: The backoff factor to increase the delay between retries,
            rounded to the nearest second.
        exceptions: The exceptions to catch.

    Returns:
        The decorated method.

    Raises:
        ValueError: If the delay is less than 0 or the backoff factor is less than 1.
        RetryError: If the maximum number of retries is reached.

    Example:
        >>> @retry(max_retries=3, delay=1, backoff=1, exceptions=(Exception,))
        ... async def my_method():
        ...     return "Hello, World!"
        ... result = await my_method()
        ... result
        "Hello, World!"
        >>> def my_method():
        ...     return "Hello, World!"
        ... result = retry(max_retries=3, delay=1, backoff=1, exceptions=(Exception,))(my_method)()
        ... result
        "Hello, World!"

    """
    if delay < 0:
        raise ValueError("The delay must be greater than or equal to 0.")
    if backoff < 1.0:
        raise ValueError("The backoff factor must be greater than or equal to 1.0.")

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
                return await _async_retry_function(
                    func, max_retries, delay, backoff, exceptions, *args, **kwargs
                )

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            return _sync_retry_function(
                func, max_retries, delay, backoff, exceptions, *args, **kwargs
            )

        return sync_wrapper

    return decorator


def _sync_retry_function(
    func: Callable[..., Any],
    max_retries: int,
    delay: int,
    backoff: float,
    exceptions: tuple[type[Exception], ...],
    *args: Any,  # noqa: ANN401
    **kwargs: Any,  # noqa: ANN401
) -> Any:  # noqa: ANN401
    func_name = func.__name__ if hasattr(func, "__name__") else "function"
    for retry in range(max_retries):
        try:
            return func(*args, **kwargs)
        except exceptions:  # noqa: PERF203
            retry_msg = " No more retries."
            if retry < max_retries - 1:
                retry_msg = f" Retrying in {delay} seconds."
            logging.exception(
                "An exception occurred while running %s. On retry %d of %d.%s",
                func_name,
                retry + 1,
                max_retries,
                retry_msg,
            )
            if retry < max_retries - 1 and delay > 0:
                time.sleep(delay)
                delay = min(round(delay * backoff), 3600)
    raise RetryError(f"Failed to run {func_name} after {max_retries} retries.")


async def _async_retry_function(
    func: Callable[..., Any],
    max_retries: int,
    delay: int,
    backoff: float,
    exceptions: tuple[type[Exception], ...],
    *args: Any,  # noqa: ANN401
    **kwargs: Any,  # noqa: ANN401
) -> Any:  # noqa: ANN401
    func_name = func.__name__ if hasattr(func, "__name__") else "async function"
    for retry in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except exceptions:  # noqa: PERF203
            retry_msg = " No more retries."
            if retry < max_retries - 1:
                retry_msg = f" Retrying in {delay} seconds."
            logging.exception(
                "An exception occurred while running %s. On retry %d of %d.%s",
                func_name,
                retry + 1,
                max_retries,
                retry_msg,
            )
            if retry < max_retries - 1 and delay > 0:
                await asyncio.sleep(delay)
                delay = min(round(delay * backoff), 3600)
    raise RetryError(f"Failed to run {func_name} after {max_retries} retries.")
