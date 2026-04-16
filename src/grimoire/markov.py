from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator, Hashable
from dataclasses import dataclass
from typing import Any, Final, Literal
from enum import Enum, auto


class SequenceBumperType(Enum):
    START = auto()
    END = auto()

    def __str__(self) -> str:
        return f"SEQUENCE_{self.name!s}"

    def __hash__(self) -> int:
        return hash((type(self).__name__, self.name, self.value))

type StartT = Literal[SequenceBumperType.START]
type EndT = Literal[SequenceBumperType.END]

START: Final[StartT] = SequenceBumperType.START
END: Final[EndT] = SequenceBumperType.END

@dataclass(frozen=True, slots=True)
class SequenceTransition[T: Hashable]:
    head: T | StartT
    tail: T | EndT

    def __getitem__(self, key: int | slice) -> T | StartT | EndT:
        return (self.head, self.tail)[key]

    def __iter__(self) -> Iterator[T | StartT | EndT]:
        return iter((self.head, self.tail))

def iter_transitions[T: Hashable](data: Iterable[T]) -> Iterator[SequenceTransition[T]]:
    data_iter: Iterator[T] = iter(data)
    head: T | SequenceBumperType = SequenceBumperType.START

    for item in data_iter:
        yield SequenceTransition(head, item)
        head = item

    yield SequenceTransition(head, SequenceBumperType.END)
