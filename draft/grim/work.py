from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .concurrency import MaybeCoro


class Work[T]:
    class PositionalView:
        def __init__(self, work: Work) -> None:
            self._work: Work = work

        def __iter__(self) -> Iterator[Any]:
            yield from self._work._args

        def __getitem__(self, index: int) -> Any:
            return self._work._args[index]

        def __setitem__(self, index: int, value: Any) -> None:
            self._work._args[index] = value

    class KeywordView:
        def __init__(self, work: Work) -> None:
            self._work: Work = work

        def __iter__(self) -> Iterator[str, Any]:
            yield from self._work._kwargs.items()

        def __getitem__(self, key: str) -> Any:
            return self._work._kwargs[key]

        def __setitem__(self, key: str, value: Any) -> None:
            self._work._kwargs[key] = value

    def __init__(self, job: MaybeCoro, *args: Any, **kwargs: Any):
        self._job: MaybeCoro = job
        self._args: list[Any] = [*args]
        self._kwargs: dict[str, Any] = {**kwargs}

    def args(self) -> PositionalView:
        return Work.PositionalView(self)

    def kwargs(self) -> KeywordView:
        return Work.KeywordView(self)
