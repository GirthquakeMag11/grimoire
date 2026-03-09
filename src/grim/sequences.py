from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    MutableMapping,
    MutableSequence,
)
from typing import (
    Self,
    cast,
    overload,
    runtime_checkable,
    Protocol
)

@runtime_checkable
class SupportsSorting(Protocol):
    def __lt__(self, other: object, /) -> bool: ...
    def __le__(self, other: object, /) -> bool: ...

class ContinuousSequence[K: SupportsSorting, V](MutableMapping[K, V]):
    def __init__(self) -> None:
        self._data: dict[K, V] = {}

    def __setitem__(self, key: K, value: V) -> None:
        self._data[key] = value

    def __getitem__(self, key: K) -> V:
        return self._data[key]

    def __delitem__(self, key: K) -> None:
        del self._data[key]

    def __iter__(self) -> Iterator[K]:
        return iter(sorted(self._data))

    def __len__(self) -> int:
        return len(self._data)

class DistinctSequence[T](MutableSequence[T]):
    def __init__(self, data: Iterable[T] = ()) -> None:
        self._data: list[T] = list(data)

    @overload
    def __getitem__(self, index: int) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> list[T]: ...
    def __getitem__(self, index: int | slice) -> T | list[T]:
        return self._data[index]

    @overload
    def __setitem__(self, index: int, value: T) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None: ...
    def __setitem__(self, index: int | slice, value: T | Iterable[T]) -> None:
        if isinstance(index, slice):
            if not isinstance(value, Iterable):
                raise TypeError(f"can only assign an iterable to a slice, not {type(value)}")
            self._data[index] = list(value)
        else:
            self._data[index] = cast(T, value)

    def __delitem__(self, index: int | slice) -> None:
        del self._data[index]

    def __len__(self) -> int:
        return len(self._data)

    def insert(self, index: int, value: T) -> None:
        self._data.insert(index, value)

    def __contains__(self, value: object) -> bool:
        return value in self._data

    def __iter__(self) -> Iterator[T]:
        return iter(self._data)

    def __reversed__(self) -> Iterator[T]:
        return reversed(self._data)

    def __iadd__(self, values: Iterable[T]) -> Self:
        self._data.extend(values)
        return self

    def append(self, value: T) -> None:
        self._data.append(value)

    def prepend(self, value: T) -> None:
        self._data.insert(0, value)

    def clear(self) -> None:
        self._data.clear()

    def reverse(self) -> None:
        self._data.reverse()

    def extend(self, values: Iterable[T]) -> None:
        self._data.extend(values)

    def pop(self, index: int = -1) -> T:
        return self._data.pop(index)

    def remove(self, value: T) -> None:
        self._data.remove(value)

    def index(
        self, value: T, start: int = 0, stop: int = 9223372036854775807
    ) -> int:  # sys.maxsize
        return self._data.index(value, start, stop)

    def count(self, value: T) -> int:
        return self._data.count(value)

    def iter_transitions(
        self, start: int = 0, stop: int = -1, step: int = 1
    ) -> Iterator[tuple[T, T]]:
        sample = self._data[slice(start, stop, step)]
        for i in range(len(sample) - 1):
            yield (sample[i], sample[i + 1])
