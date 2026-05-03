from __future__ import annotations

from dataclasses import (
    _MISSING_TYPE as MissingType,
)
from dataclasses import (
    MISSING as MISSING,
)
from dataclasses import (
    Field,
    dataclass,
)
from functools import cached_property
from inspect import (
    Parameter,
)
from inspect import (
    _ParameterKind as ParameterKind,
)
from typing import (  # type: ignore[attr-defined]
    Any,
)

from .typenode import TypeNode


@dataclass
class FieldNode:
    _parent: Any
    target: Any

    @cached_property
    def name(self) -> str | None:
        if self.is_param or self.is_field:
            return self.target.name
        return None

    @cached_property
    def has_default(self) -> bool:
        if self.is_param:
            return self.target.default is not Parameter.empty
        elif self.is_field:
            return self.target.default is not MISSING

    @cached_property
    def default(self) -> Any:
        if self.has_default:
            return self.target.default
        return MISSING

    @cached_property
    def has_default_factory(self) -> bool:
        if self.is_field:
            return self.target.default_factory is not MISSING
        return False

    @cached_property
    def is_param(self) -> bool:
        return isinstance(self.target, Parameter)

    @cached_property
    def is_field(self) -> bool:
        return isinstance(self.target, Field)

    @cached_property
    def type(self) -> TypeNode | MissingType:
        if self.is_param:
            if self.target.annotation is Parameter.empty:
                return MISSING
            return TypeNode(self, self.target.annotation)
        elif self.is_field:
            return TypeNode(self, self.target.type)

    @cached_property
    def var_positional(self) -> bool:
        if self.is_param:
            return self.target.kind is ParameterKind.VAR_POSITIONAL
        return False

    @cached_property
    def var_keyword(self) -> bool:
        if self.is_param:
            return self.target.kind is ParameterKind.VAR_KEYWORD
        return False

    @cached_property
    def positional_only(self) -> bool:
        if self.is_param:
            return self.target.kind is ParameterKind.POSITIONAL_ONLY
        return False

    @cached_property
    def positional_or_keyword(self) -> bool | None:
        if self.is_param:
            return self.target.kind is ParameterKind.POSITIONAL_OR_KEYWORD
        elif self.is_field:
            return self.target.kw_only is not True
        return None

    @cached_property
    def keyword_only(self) -> bool | None:
        if self.is_param:
            return self.target.kind is ParameterKind.KEYWORD_ONLY
        elif self.is_field:
            return self.target.kw_only is True
        return None
