from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from typing import Dict, Iterable, Sequence, Tuple, TypeVar

T = TypeVar("T")


def m_transitions(seq: Sequence[T]) -> Dict[T, Dict[T, int]]:
    transitions: Dict[T, Dict[T, int]] = {}

    for i in range(len(seq) - 1):
        head, tail = seq[i], seq[i + 1]
        transitions.setdefault(head, {}).setdefault(tail, 0)
        transitions[head][tail] += 1

    return transitions


def m_probabilities(transitions: Dict[T, Dict[T, int]]) -> Dict[T, Dict[T, float]]:
    probabilities: Dict[T, Dict[T, float]] = {}

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
class markov[T]:
    data: InitVar[Iterable[T]]

    values: Tuple[T] = field(init=False)
    transitions: Dict[T, Dict[T, int]] = field(init=False)
    probabilities: Dict[T, Dict[T, float]] = field(init=False)

    def __post_init__(self, data: Iterable[T]) -> None:
        object.__setattr__(self, "values", tuple(data))
        object.__setattr__(self, "transitions", m_transitions(self.values))
        object.__setattr__(self, "probabilities", m_probabilities(self.transitions))
