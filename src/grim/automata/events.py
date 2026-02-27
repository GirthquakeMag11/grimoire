from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., object])

SyncCallback = Callable[..., object]
AsyncCallback = Callable[..., Coroutine[Any, Any, object]]


class EventCallbackEmitter:
    def __init__(self) -> None:
        self._callbacks: defaultdict[str, set[SyncCallback | AsyncCallback]] = defaultdict(set)

    def add_callback(self, name: str, fn: SyncCallback | AsyncCallback) -> None:
        self._callbacks[name].add(fn)

    def remove_callback(self, name: str, fn: SyncCallback | AsyncCallback) -> None:
        self._callbacks[name].discard(fn)

    async def emit(self, name: str, *args: Any, **kwargs: Any) -> None:
        async with asyncio.TaskGroup() as tg:
            for cb in self._callbacks[name]:
                if asyncio.iscoroutinefunction(cb):
                    tg.create_task(cb(*args, **kwargs))
                elif callable(cb):
                    cb(*args, **kwargs)


class BinaryEvent:
    def __init__(self, name: str | None = None) -> None:
        self._name: str | None = name
        self._positive: asyncio.Event = asyncio.Event()
        self._negative: asyncio.Event = asyncio.Event()
        self._negative.set()

    def set(self) -> None:
        self._negative.clear()
        self._positive.set()

    def clear(self) -> None:
        self._positive.clear()
        self._negative.set()

    async def wait_set(self) -> None:
        if not self._positive.is_set():
            await self._positive.wait()

    async def wait_clear(self) -> None:
        if not self._negative.is_set():
            await self._negative.wait()
