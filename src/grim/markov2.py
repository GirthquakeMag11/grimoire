from __future__ import annotations

from typing import NamedTuple, TypeVar

T = TypeVar("T", bound=Hashable)

def Markov[T]:
    def __init__(self):
        self._data = []
        self._probabilities = {}
        self._transitions = {}

    def _add_transition(self, head: T, tail: T) -> None:
        self._transitions.setdefault(head, {}).setdefault(tail, 0)
        self._transitions[head][tail] += 1

    def _rem_transition(self, head: T, tail: T) -> None:
        if head in self._transitions:
            if tail in self._transitions[head]:
                self._transitions[head][tail] -= 1
                if self._transitions[head][tail] <= 0:
                    del self._transitions[head][tail]
            if sum(self._transitions[head].values()) <= 0:
                del self._transitions[head]

    def append(self, item: T) -> None:
        self._data.append(item)
        if len(self._data) >= 2:
            last = self._data[-2]
            new_pair = (last, item)
            self._add_transition(*new_pair)

    def remove(self, item: T) -> None:
        index = self._data.index(item)
        self.pop(index)

    def pop(self, index: int) -> T:
        item = self._data.pop(index)

        if len(self._data) >= 1:
            prev_item = self._data[index - 1]
            self._rem_transition(prev_item, item)

        if len(self._data) > index:
            next_item = self._data[index + 1]
            self._rem_transition(item, next_item)

        return item
