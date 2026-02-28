from __future__ import annotations

from collections.abc import Hashable, Iterable, Iterator
from typing import NamedTuple, TypeAlias
from uuid import UUID, uuid4


class State(NamedTuple):
    key: Hashable
    uuid: UUID

    @property
    def name(self) -> str:
        return str(self.key)


def state(key: Hashable) -> State:
    if isinstance(key, State):
        return key
    return State(key=key, uuid=uuid4())


class Transition(NamedTuple):
    head: State
    tail: State
    uuid: UUID


def transition(head: Hashable | State, tail: Hashable | State) -> Transition:
    head, tail = state(head), state(tail)
    return Transition(head=head, tail=tail, uuid=uuid4())


StateVar: TypeAlias = State | Transition


class StateTransitionChain:
    __slots__ = ("_states", "_transitions", "__weakref__")

    def __init__(self, *keys: Hashable) -> None:
        self._states: list[StateVar] = []
        self._transitions: list[StateVar] = []
        if keys:
            self.extend(keys)

    def append(self, key: Hashable) -> None:
        self._states.append(state(key))
        if len(self._states) > 1:
            self._transitions.append(transition(self._states[-2], self._states[-1]))

    def extend(self, itr: Iterable[Hashable]) -> None:
        for key in itr:
            self.append(key)

    def states(self) -> Iterator[StateVar]:
        yield from self._states

    def transitions(self) -> Iterator[StateVar]:
        yield from self._transitions
