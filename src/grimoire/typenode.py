from dataclasses import (
    dataclass,
    is_dataclass,
)
from functools import (
    cached_property,
)
from inspect import (
    isclass as inspect_isclass,
)
from types import (
    TypeAliasType,
    UnionType,
)
from typing import (
    Annotated,
    Any,
    Literal,
    NotRequired,
    ReadOnly,
    Required,
    Union,
    get_args,
    get_origin,
)


@dataclass
class TypeNode:
    _parent: Any
    target: Any

    @cached_property
    def name(self) -> str | None:
        if self.is_class or self.is_type_alias:
            return self.target.__name__
        return None

    @cached_property
    def is_generic(self) -> bool:
        return self.origin is not None and not self.is_literal and not self.is_union

    @cached_property
    def type_params(self) -> tuple[Any, ...]:
        if self.is_type_alias:
            return self.target.__type_params__
        return ()

    @cached_property
    def is_type_alias(self) -> bool:
        return isinstance(self.target, TypeAliasType)

    @cached_property
    def is_class(self) -> bool:
        return inspect_isclass(self.origin)

    @cached_property
    def is_dataclass(self) -> bool:
        return isinstance(self.target, type) and is_dataclass(self.target)

    @cached_property
    def is_optional(self) -> bool:
        return self.is_union and type(None) in self.union_values

    @cached_property
    def option_values(self) -> tuple[Any, ...]:
        if self.is_optional:
            return tuple(arg for arg in self.union_values if arg is not type(None))
        return ()

    @cached_property
    def is_union(self) -> bool:
        return self.origin is Union or self.origin is UnionType

    @cached_property
    def union_values(self) -> tuple[Any, ...]:
        if self.is_union:
            return get_args(self.inner_type)
        return ()

    @cached_property
    def inner_type(self) -> Any:
        if self.is_annotated:
            return get_args(self.target)[0]
        elif self.is_type_alias:
            return self.target.__value__
        return self.target

    @cached_property
    def is_annotated(self) -> bool:
        return get_origin(self.target) is Annotated

    @cached_property
    def annotated_extras(self) -> tuple[Any, ...]:
        if self.is_annotated:
            return get_args(self._raw)[1:]
        return ()

    @cached_property
    def is_literal(self) -> bool:
        return self.origin is Literal

    @cached_property
    def literal_values(self) -> tuple[Any, ...]:
        if self.is_literal:
            return get_args(self.inner_type)
        return ()

    @cached_property
    def is_readonly(self) -> bool:
        return self.origin is ReadOnly

    @cached_property
    def is_required(self) -> bool:
        return self.origin is Required

    @cached_property
    def is_not_required(self) -> bool:
        return self.origin is NotRequired

    @cached_property
    def origin(self) -> Any | None:
        return get_origin(self.inner_type)

    @cached_property
    def args(self) -> tuple[TypeNode, ...]:
        if self.is_literal:
            return ()
        return tuple(TypeNode(self, a) for a in get_args(self.inner_type) if a is not type(None))
