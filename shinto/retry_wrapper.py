"""A wrapper to retry a method if it fails."""

from __future__ import annotations

import asyncio
import logging
import time
from functools import wraps
from typing import Any, Awaitable, Callable, Coroutine


class RetryError(Exception):
    """An exception raised when the maximum number of retries is reached."""


def _retry_internal(
    func: Callable[..., Any],
    fargs: tuple[Any, ...],
    fkwargs: dict[str, Any],
    max_tries: int | None,
    delay: float,
    exceptions: type[Exception] | tuple[type[Exception], ...],
    backoff: float,
    delay_increment: float,
    max_delay: float | None,
) -> Any:  # noqa: ANN401
    current_delay = min(delay, max_delay) if max_delay else delay
    tries = 0
    max_tries = max_tries or -1
    func_name = _get_function_name(func)

    while tries != max_tries:
        try:
            return func(*fargs, **fkwargs)
        except exceptions as e:
            tries += 1
            _log_exception(func_name, tries, max_tries, current_delay, e)

        if tries != max_tries:
            time.sleep(current_delay)
            current_delay = _next_delay(current_delay, backoff, delay_increment, max_delay)

    raise RetryError(f"Failed to run {func_name} after {tries} tries.")


async def _retry_internal_async(
    func: Callable[..., Any],
    fargs: tuple[Any, ...],
    fkwargs: dict[str, Any],
    max_tries: int | None,
    delay: float,
    exceptions: type[Exception] | tuple[type[Exception], ...],
    backoff: float,
    delay_increment: float,
    max_delay: float | None,
) -> Coroutine[Any, Any, Any]:
    current_delay = min(delay, max_delay) if max_delay else delay
    tries = 0
    max_tries = max_tries or -1
    func_name = _get_function_name(func)

    while tries != max_tries:
        try:
            return await func(*fargs, **fkwargs)
        except exceptions as e:
            tries += 1
            _log_exception(func_name, tries, max_tries, current_delay, e)

        if tries != max_tries:
            await asyncio.sleep(current_delay)
            current_delay = _next_delay(current_delay, backoff, delay_increment, max_delay)

    raise RetryError(f"Failed to run {func_name} after {tries} tries.")


def _function_isasync(func: Callable[..., Any]) -> bool:
    return asyncio.iscoroutinefunction(func)


def _get_function_name(func: Callable[..., Any]) -> str:
    return func.__name__ if hasattr(func, "__name__") else func.__class__.__name__


def _log_exception(func_name: str, tries: int, max_tries: int, delay: float, e: Exception) -> None:
    retry_msg = "" if tries == max_tries else f" Retrying in {delay} seconds."
    logging.error(
        "An exception occurred while running %s on attempt %s/%s.%s",
        func_name,
        tries,
        max_tries or "infinite",
        retry_msg,
        exc_info=e,
    )


def _next_delay(
    delay: float,
    backoff: float,
    delay_increment: float,
    max_delay: float | None,
) -> float:
    delay *= backoff
    delay += delay_increment
    if max_delay:
        delay = min(delay, max_delay)

    return delay


def retry(
    max_tries: int | None = None,
    delay: float = 0.0,
    exceptions: type[Exception] | tuple[type[Exception], ...] = Exception,
    backoff: float = 1.0,
    delay_increment: float = 0.0,
    max_delay: float | None = None,
) -> Callable[..., Callable[..., Any] | Awaitable[Any]]:
    """
    Retry a method if it fails.

    Retries a method if it raises an exception specified in the `exceptions` tuple.
    The method is attempted up to `max_tries` times with a delay of `delay` seconds between retries.
    The delay between retries is increased by a factor of `backoff`
    and incremented by `delay_increment` up to a maximum delay of `max_delay`.

    Args:
        max_tries: The maximum number of attempts. Default: None (infinite).
        delay: The delay between retries (in seconds). Default: 1.
        exceptions: The exception or a tuple of exceptions to catch. Default: Exception.
        backoff: Multiplier applied to the delay between retries. Default: 1 (no backoff).
        delay_increment: Value to add to the delay between retries. Default: 0.
        max_delay: The maximum delay between retries. Default: None (no maximum).

    Returns:
        The decorated method.

    Raises:
        ValueError: If invalid arguments are provided.
        RetryError: If the maximum number of retries is reached.

    Example:
        >>> @retry()
        ... async def my_method():
        ...     return "Hello, World!"
        ... result = await my_method()
        ... result
        "Hello, World!"

    """
    if max_tries and max_tries < 1:
        raise ValueError("The max_tries must be greater than or equal to 1 or None for infinite.")
    if delay < 0:
        raise ValueError("The delay must be greater than or equal to 0.")
    if backoff < 1.0:
        raise ValueError("The backoff factor must be greater than or equal to 1.0.")
    if delay_increment < 0:
        raise ValueError("The delay_increment must be greater than or equal to 0.")
    if max_delay and max_delay < 0:
        raise ValueError("The max_delay must be greater than or equal to 0.")

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if _function_isasync(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
                return await _retry_internal_async(
                    func,
                    args,
                    kwargs,
                    max_tries,
                    delay,
                    exceptions,
                    backoff,
                    delay_increment,
                    max_delay,
                )

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            return _retry_internal(
                func,
                args,
                kwargs,
                max_tries,
                delay,
                exceptions,
                backoff,
                delay_increment,
                max_delay,
            )

        return sync_wrapper

    return decorator


def retry_call(
    f: Callable[..., Any],
    fargs: tuple[Any, ...] | None = None,
    fkwargs: dict[str, Any] | None = None,
    max_tries: int | None = None,
    delay: float = 0.0,
    exceptions: type[Exception] | tuple[type[Exception], ...] = Exception,
    backoff: float = 1.0,
    delay_increment: float = 0.0,
    max_delay: float | None = None,
) -> Coroutine[Any, Any, Any] | Any:  # noqa: ANN401
    """
    Retry a method if it fails.

    Retries a method if it raises an exception specified in the `exceptions` tuple.
    The method is attempted up to `max_tries` times with a delay of `delay` seconds between retries.
    The delay between retries is increased by a factor of `backoff`
    and incremented by `delay_increment` up to a maximum delay of `max_delay`.

    Args:
        f: The method to retry.
        fargs: The arguments to pass to the method.
        fkwargs: The keyword arguments to pass to the method.
        max_tries: The maximum number of attempts. Default: None (infinite).
        delay: The delay between retries (in seconds). Default: 1.
        exceptions: The exception or a tuple of exceptions to catch. Default: Exception.
        backoff: Multiplier applied to the delay between retries. Default: 1 (no backoff).
        delay_increment: Value to add to the delay between retries. Default: 0.
        max_delay: The maximum delay between retries. Default: None (no maximum).

    Returns:
        The result of the method.

    Raises:
        ValueError: If invalid arguments are provided.
        RetryError: If the maximum number of retries is reached.

    Example:
        >>> async def my_method():
        ...     return "Hello, World!"
        ... result = await retry_call(my_method)
        ... result
        "Hello, World!"

    """
    args = fargs or []
    kwargs = fkwargs or {}
    func = retry(max_tries, delay, exceptions, backoff, delay_increment, max_delay)(f)
    return func(*args, **kwargs)
