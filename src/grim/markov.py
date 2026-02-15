"""Simple Markov chain implementation for sequence analysis."""

from __future__ import annotations

import collections.abc
from dataclasses import InitVar, dataclass, field
from typing import Hashable, Iterable, Sequence, TypeVar

T = TypeVar("T", bound=Hashable)


def m_transitions(seq: Sequence[T]) -> dict[T, dict[T, int]]:
    """Count transitions between consecutive items."""
    transitions: dict[T, dict[T, int]] = {}

    for i in range(len(seq) - 1):
        head, tail = seq[i], seq[i + 1]
        transitions.setdefault(head, {}).setdefault(tail, 0)
        transitions[head][tail] += 1

    return transitions


def m_probabilities(transitions: dict[T, dict[T, int]]) -> dict[T, dict[T, float]]:
    """Convert transition counts to probabilities."""
    probabilities: dict[T, dict[T, float]] = {}

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
class Markov[T: Hashable]:
    """Immutable Markov chain with precomputed transitions and probabilities."""

    data: InitVar[Iterable[T]]

    values: tuple[T, ...] = field(init=False)
    transitions: dict[T, dict[T, int]] = field(init=False)
    probabilities: dict[T, dict[T, float]] = field(init=False)

    def __post_init__(self, data: Iterable[T]) -> None:
        object.__setattr__(self, "values", tuple(data))
        object.__setattr__(self, "transitions", m_transitions(self.values))
        object.__setattr__(self, "probabilities", m_probabilities(self.transitions))

    def __getitem__(self, key: T) -> dict[T, int]:
        return self.probabilities.get(key, {})

    def __add__(self, other) -> Markov | NotImplemented:
        """Concatenate with another markov instance or iterable."""
        if isinstance(other, type(self)):
            other_values = other.values
        elif isinstance(other, collections.abc.Iterable):
            other_values = other
        else:
            return NotImplemented
        return type(self)([*self.values, *other_values])
