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
    if inspect.iscoroutinefunction(obj):
        return obj(*args, **kwargs)
    elif inspect.isawaitable(obj):
        return obj
    elif callable(obj):
        return asyncio.to_thread(obj, *args, **kwargs)

async def maybe_coroutine(obj: MaybeCoro, *args, **kwargs) -> Any:
    return await ensure_coroutine(obj, *args, **kwargs)

def current_thread() -> threading.Thread:
    return threading.current_thread()

def current_event_loop() -> asyncio.AbstractEventLoop | None:
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return None

def ensure_event_loop() -> asyncio.AbstractEventLoop:
    if not event_loop := current_event_loop():
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
    return event_loop

class EventLoopExecutor:

    def __init__(self, event_loop: Optional[asyncio.AbstractEventLoop] = None):
        self._event_loop = event_loop
        self._external_ev = bool(event_loop is not None)
        self._q = asyncio.Queue()

    async def _queue_consumer(self):
        ...

    async def __aenter__(self):
        if not self._event_loop:
            self._event_loop = ensure_event_loop()
        self._event_loop.run_until_complete(self._queue_consumer())

    async def __aexit__(self, exc_val, exc_tp, exc_tb):
        ...
