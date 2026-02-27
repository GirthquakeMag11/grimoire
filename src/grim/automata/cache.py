from __future__ import annotations

import asyncio
from collections.abc import Callable, Hashable
from dataclasses import field
from typing import Any, TypeAlias

_omit_ = object()

Factory: TypeAlias = Callable[[], Any]


class AsyncCache:
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    data: dict[Hashable, Any] = field(default_factory=dict)

    async def store(self, key: Hashable, value: Any, replace_ok: bool = True) -> None:
        async with self.lock:
            if key not in self.data or replace_ok is True:
                self.data[key] = value
            elif key in self.data and replace_ok is False:
                raise KeyError(
                    f"{type(self).__name__} instance (ID:{id(self)}) already contains cached item with key '{key!s}'"
                )

    async def get(self, key: Hashable, default: Any | None = None, set_default: bool = False) -> Any | None:
        async with self.lock:
            if set_default is True:
                return self.data.setdefault(key, default)
            else:
                return self.data.get(key, default)


class _CachedMixin:
    cache: AsyncCache = field(default_factory=AsyncCache)
