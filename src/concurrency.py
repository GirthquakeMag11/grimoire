from __future__ import annotations

import asyncio
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
