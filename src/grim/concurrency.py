from __future__ import annotations

import asyncio
import threading
import concurrent.futures
import inspect
from typing import (
    Any,
    Union,
    Callable,
    Coroutine,
    Awaitable,
    TypeAlias,
    )


MaybeCoro: TypeAlias = Union[Callable, Coroutine, Awaitable]

def ensure_coroutine(obj: MaybeCoro, *args, **kwargs) -> Awaitable:
    """Coerce 'obj' into an awaitable, invoking or wrapping it as needed
    and return it.

    *args and **kwargs are passed into 'obj' if appropriate.
    """
    if inspect.iscoroutinefunction(obj):
        return obj(*args, **kwargs)
    elif inspect.isawaitable(obj):
        return obj
    elif callable(obj):
        return asyncio.to_thread(obj, *args, **kwargs)

async def maybe_coroutine(obj: MaybeCoro, *args, **kwargs) -> Any:
    """Await an object that may be synchronous or asynchronous and return result."""
    return await ensure_coroutine(obj, *args, **kwargs)

def current_thread() -> threading.Thread:
    """Return the current thread object."""
    return threading.current_thread()

def current_event_loop() -> asyncio.AbstractEventLoop | None:
    """Return the running event loop for the current thread, if any."""
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return None

def ensure_event_loop() -> asyncio.AbstractEventLoop:
    """Ensure an event loop is set for the current thread and return it."""
    if not event_loop := current_event_loop():
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
    return event_loop
