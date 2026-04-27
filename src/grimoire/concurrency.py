from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any


async def achain(*iterables: Iterator[Any] | AsyncIterator[Any]) -> AsyncIterator[Any]:
    for iterable in iterables:
        if isinstance(iterable, AsyncIterator):
            async for item in iterable:
                yield item

        elif isinstance(iterable, Iterator):
            yield from iterable
