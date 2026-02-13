from __future__ import annotations

from typing import Dict, Sequence, TypeVar

T = TypeVar("T")


def markov_chain(seq: Sequence[T]) -> Dict[T, Dict[T, float]]:
    transitions = {}
    probabilities = {}

    for i in range(len(seq) - 1):
        head, tail = seq[i], seq[i + 1]
        transitions.setdefault(head, {}).setdefault(tail, 0)
        transitions[head][tail] += 1

    for current_head_item, tail_transition_counts in transitions.items():
        total = sum([count for count in tail_transition_counts.values()])

        probabilities[current_head_item] = {}
        for (
            current_tail_item,
            current_transition_count,
        ) in tail_transition_counts.items():
            probabilities[current_head_item][current_tail_item] = (
                current_transition_count / total
            )

    return probabilities
