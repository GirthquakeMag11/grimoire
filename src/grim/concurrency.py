"""Utilities for handling mixed synchronous and asynchronous callables."""

from __future__ import annotations

import asyncio
import inspect
import threading
from collections.abc import Awaitable, Callable
from typing import Any, TypeAlias

MaybeCoro: TypeAlias = Callable[..., Any] | Awaitable[Any]


def ensure_coroutine(
    obj: MaybeCoro, *args: Any, **kwargs: Any
) -> Awaitable[Any]:
    """Coerce an object into an awaitable.

    Handles three cases:
    - Coroutine functions: invoked with args/kwargs
    - Awaitables: returned as-is (args/kwargs ignored)
    - Callables: wrapped with asyncio.to_thread for async execution

    Args:
        obj: A coroutine function, awaitable, or callable
        *args: Positional arguments to pass if obj is callable
        **kwargs: Keyword arguments to pass if obj is callable

    Returns:
        An awaitable that can be used with `await`

    Raises:
        TypeError: If obj is not a coroutine function, awaitable, or callable
    """
    if inspect.iscoroutinefunction(obj):
        return obj(*args, **kwargs)
    elif inspect.isawaitable(obj):
        return obj
    elif callable(obj):
        return asyncio.to_thread(obj, *args, **kwargs)
    else:
        raise TypeError(
            f"Expected coroutine function, awaitable, or callable, got {type(obj)}"
        )


async def maybe_coroutine(obj: MaybeCoro, *args: Any, **kwargs: Any) -> Any:
    """Await an object that may be synchronous or asynchronous.

    Convenience wrapper around ensure_coroutine that immediately awaits
    the result.

    Args:
        obj: A coroutine function, awaitable, or callable
        *args: Positional arguments to pass if obj is callable
        **kwargs: Keyword arguments to pass if obj is callable

    Returns:
        The result of awaiting the coroutine
    """
    return await ensure_coroutine(obj, *args, **kwargs)


def current_thread() -> threading.Thread:
    """Return the current thread object.

    Returns:
        The Thread object representing the current thread
    """
    return threading.current_thread()


def current_event_loop() -> asyncio.AbstractEventLoop | None:
    """Return the running event loop for the current thread, if any.

    Returns:
        The running event loop, or None if no loop is running
    """
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return None


def ensure_event_loop() -> asyncio.AbstractEventLoop:
    """Ensure an event loop exists for the current thread.

    If no event loop is currently running, creates a new one and sets it
    as the event loop for the current thread.

    Returns:
        The running or newly created event loop
    """
    if not (event_loop := current_event_loop()):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
    return event_loop
