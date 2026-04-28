from __future__ import annotations

import inspect
from datetime import datetime
from collections.abc import (
    Callable,
    Iterator,
)
from dataclasses import (
    dataclass,
    field,
    InitVar,
)
from functools import (
    cached_property,
)
from typing import (
    Any,
    get_type_hints,
    get_origin,
    get_args,
    Annotated,
    Literal,
)


@dataclass
class TypeNode:
    parent: FieldNode | ParameterNode | TypeNode
    _raw: Any

    @cached_property
    def is_annotated(self) -> bool:
        return get_origin(self._raw) is Annotated

    @cached_property
    def is_generic(self) -> bool:
        return self.origin is not None and not self.is_literal and not self.is_union

    @cached_property
    def is_class(self) -> bool:
        return inspect.isclass(self.origin)

    @cached_property
    def is_primitive_class(self) -> bool:
        return bool(self.is_class and isinstance(self.origin, (bool, str, int, float, bytes, datetime)))

    @cached_property
    def is_literal(self) -> bool:
        return self.origin is Literal

    @cached_property
    def is_optional(self) -> bool:
        return self.is_union and type(None) in self.union_values

    @cached_property
    def is_union(self) -> bool:
        return self.origin is typing.Union or self.origin is types.UnionType

    @cached_property
    def annotated_extras(self) -> tuple[Any, ...]:
        if self.is_annotated:
            return get_args(self._raw)[1:]
        return ()

    @cached_property
    def inner_type(self) -> Any:
        if self.is_annotated:
            return get_args(self._raw)[0]
        return self._raw

    @cached_property
    def origin(self) -> Any | None:
        return get_origin(self.inner_type)

    @cached_property
    def literal_values(self) -> tuple[Any, ...]:
        if self.is_literal:
            return get_args(self.inner_type)
        return ()

    @cached_property
    def union_values(self) -> tuple[Any, ...]:
        if self.is_union:
            return get_args(self.inner_type)
        return ()

    @cached_property
    def union_members(self) -> tuple[TypeNode, ...]:
        return (TypeNode(a) for a in self.union_values)

    @cached_property
    def children(self) -> tuple[TypeNode, ...]:
        if self.is_literal:
            return ()
        return tuple(TypeNode(a) for a in get_args(self.inner_type))


@dataclass
class ParameterNode:
    owner: SignatureNode
    position: int | None
    keyword: str | None
    is_unpack: bool
    unpack_type: type[dict] | type[tuple] | None
    is_return: bool
    type: TypeNode | None


@dataclass
class SignatureNode:
    owner: CallableNode
    parameters: tuple[ParameterNode, ...]


@dataclass
class FieldNode:

@dataclass
class CallableNode:
