"""Simple Markov chain implementation for sequence analysis."""

from __future__ import annotations

import collections.abc.Sequence as AbstractSequence
from contextlib import contextmanager
from dataclasses import InitVar, dataclass, field
from typing import Hashable, Iterable, Iterator, Sequence, TypeAlias, TypeVar

T = TypeVar("T", bound=Hashable)

Transitions: TypeAlias = dict[T, dict[T, int]]
Probabilities: TypeAlias = dict[T, dict[T, float]]


def m_transitions(seq: Sequence[T]) -> Transitions[T]:
    """Count transitions between consecutive items."""
    transitions: dict[T, dict[T, int]] = {}

    for i in range(len(seq) - 1):
        head, tail = seq[i], seq[i + 1]
        transitions.setdefault(head, {}).setdefault(tail, 0)
        transitions[head][tail] += 1

    return transitions


def m_probabilities(seq: Sequence[T]) -> Probabilities[T]:
    """Convert transition counts to probabilities."""
    probabilities: dict[T, dict[T, float]] = {}

    transitions = m_transitions(seq)
    for current_head_item, tail_transition_counts in transitions.items():
        total_transitions = sum(tail_transition_counts.values())
        probabilities[current_head_item] = {}

        for (
            current_tail_item,
            current_transition_count,
        ) in tail_transition_counts.items():
            calculated_probability = current_transition_count / total_transitions
            probabilities[current_head_item][current_tail_item] = calculated_probability

    return probabilities


@dataclass(slots=True, frozen=True)
class MarkovChain[T: Hashable]:
    """Immutable Markov chain with precomputed transitions and probabilities."""

    data: InitVar[Iterable[T]]

    values: tuple[T, ...] = field(init=False)
    transitions: Transitions[T] = field(init=False)
    probabilities: Probabilities[T] = field(init=False)

    def __add__(self, other: MarkovChain[T]) -> MarkovChain[T]:
        if isinstance(other, MarkovChain):
            return MarkovChain([*self.values, *other.values])

    def __post_init__(self, data: Iterable[T]) -> None:
        object.__setattr__(self, "values", tuple(data))
        object.__setattr__(self, "transitions", m_transitions(self.values))
        object.__setattr__(self, "probabilities", m_probabilities(self.transitions))

    def __iter__(self) -> Iterator[T]:
        yield from self.values


class MarkovSequence[T](AbstractSequence):
    def __init__(self, *args: T):
        self._data: list[T] = []
        self._transitions: Transitions[T] = {}
        self._probabilities: Probabilities[T] = {}
        self.extend(args)

    def _mark(self) -> int:
        return len(self._data) - 1

    @contextmanager
    def _marker(self):
        try:
            before = len(self)
            yield None
        finally:
            after = len(self)
            if before < after:



    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[T]:
        yield from self._data

    def __contains__(self, item: Any) -> bool:
        return bool(item in self._data)

    def append(self, item: T) -> None:
        with self._marker():
            self._data.append(item)

    def insert(self, index: int, item: T) -> None:
        with self._marker():
            self._data.insert(index, item)

    def extend(self, iterable: Iterable[T]) -> None:
        with self._marker():
            self._data.extend(iterable)
