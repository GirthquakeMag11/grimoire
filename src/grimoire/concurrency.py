from __future__ import annotations

import asyncio
import inspect
from collections.abc import (
    Awaitable,
    Callable,
    Coroutine,
)
from dataclasses import (
    MISSING as MISSING,
)
from typing import (
    Any,
)

type Job[T] = (
    Callable[..., T]
    | Callable[[], Coroutine[Any, Any, T]]
    | Callable[..., Awaitable[T]]
    | Coroutine[Any, Any, T]
    | Awaitable[T]
)


def ensure_async[T](job: Job[T], *args: Any, **kwargs: Any) -> Awaitable[T]:
    if inspect.iscoroutinefunction(job):
        return job(*args, **kwargs)
    if inspect.isawaitable(job):
        return job
    if callable(job):
        return asyncio.to_thread(job, *args, **kwargs)  # type: ignore[arg-type]
    raise TypeError(f"Cannot coerce {type(job).__name__} into an awaitable")
