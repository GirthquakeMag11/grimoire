"""Utilities for handling mixed synchronous and asynchronous callables."""

from __future__ import annotations

import asyncio
import inspect
import threading
from collections import defaultdict
from collections.abc import AsyncIterator, Awaitable, Callable, Hashable, MutableMapping
from contextlib import asynccontextmanager
from typing import Any, ClassVar, TypeAlias

MaybeCoro: TypeAlias = Callable[..., Any] | Awaitable[Any]
EventName: TypeAlias = Hashable


def ensure_coroutine(obj: MaybeCoro, *args: Any, **kwargs: Any) -> Awaitable[Any]:
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
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop


class LoopOrganizer:
    """
    Descriptor providing access to a per-thread asyncio event loop.

    Retrieves an existing loop for the current thread, or locates/creates one
    if necessary, without starting or running it.
    """

    _reg_: ClassVar[MutableMapping[int, asyncio.AbstractEventLoop]] = {}
    _lock_: ClassVar[threading.RLock] = threading.RLock()

    def __get__(self, instance, owner):
        """Return the current thread's event loop when accessed via an instance."""
        if instance is None:
            return self
        return type(self).current()

    @classmethod
    def current(cls) -> asyncio.AbstractEventLoop:
        """
        Return the event loop associated with the current thread.

        If no valid loop is registered, attempt to retrieve an existing loop
        or create and register a new one.
        """
        thread_id = threading.get_ident()

        with cls._lock_:
            if not (loop := cls.get(thread_id)):
                cls._reg_[thread_id] = ensure_event_loop()
                loop = cls._reg_[thread_id]
            return loop

    @classmethod
    def get(cls, thread_id: int) -> asyncio.AbstractEventLoop | None:
        """Return the registered event loop for a thread, if valid."""
        loop = cls._reg_.get(thread_id)
        if loop is None or loop.is_closed():
            return None
        return loop


class QueueCoordinator:
    ...


class ConditionCoordinator:
    ...


class TaskCoordinator:
    ...


class EventCoordinator:
    def __init__(self) -> None:
        self.history: list[EventName] = []
        self.events: defaultdict[asyncio.Event] = defaultdict(asyncio.Event)
        self.waiters: defaultdict[int] = defaultdict(int)

    async def event(self, name: EventName) -> asyncio.Event:
        async with self.lock:
            return self.events[name]

    async def increment_waiter(self, name: EventName) -> None:
        async with self.lock:
            self.waiters[name] += 1

    async def decrement_waiter(self, name: EventName) -> None:
        async with self.lock:
            if name in self.waiters:
                self.waiters[name] -= 1
                if self.waiters[name] <= 0:
                    del self.waiters[name]
                    if name in self.events:
                        del self.events[name]

    async def set_event(self, name: EventName) -> None:
        async with self.lock:
            self.events[name].set()
            self.history.append(name)

    async def clear_event(self, name: EventName) -> None:
        async with self.lock:
            self.events[name].clear()

    async def remove_event(self, name: EventName) -> None:
        async with self.lock:
            self.events.pop(name)

    async def has_occurred(self, name: EventName) -> int:
        async with self.lock:
            return sum(1 for i in self.history if i == name)

    @asynccontextmanager
    async def incrementer(self, name: EventName) -> AsyncIterator[None]:
        try:
            await self.increment_waiter(name)
            yield None
        finally:
            await self.decrement_waiter(name)

    async def wait_event_occurs(self, name: EventName) -> None:
        if name not in self.history:
            await self.wait_next_event(name)

    async def wait_next_event(self, name: EventName) -> None:
        async with self.incrementer(name):
            event = await self.event(name)
            await event.wait()
