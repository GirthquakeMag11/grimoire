from __future__ import annotations

from dataclasses import (
    dataclass,
    is_dataclass,
    field,
    Field,
    MISSING,
    _MISSING_TYPE as MissingType,
)
from functools import (
    cached_property,
    partial,
)
from inspect import (
    signature as inspect_signature,
    isclass as inspect_isclass,
    Parameter,
    Signature,
    _ParameterKind as ParameterKind,
)
from types import (
    MappingProxyType,
    UnionType,
)
from collections.abc import (
    Callable,
    Iterator,
)
from typing import (
    Any,
    Protocol,
    Annotated,
    Literal,
    runtime_checkable,
    get_type_hints,
    get_origin,
    get_args,
    TypeAliasType,
    TypedDict,
    Union,
)


def iter_fields(obj: Any) -> Iterator[str]:
    """Yield unique public field names discoverable from an object and its MRO.

    Names are collected from the instance dict first, then each class in the
    MRO via descriptors, annotations, slots, and remaining class dict keys,
    with duplicates removed.

    Respects encapsulation and avoids private namespaces.
    """
    seen: set[str] = set()

    def _is_public(name: str) -> bool:
        return not name.startswith("_")

    def _yield_new_public(*names: str) -> Iterator[str]:
        for name in names:
            if _is_public(name) and name not in seen:
                seen.add(name)
                yield name

    def _is_valid_descriptor(value: Any) -> bool:
        if isinstance(value, property):
            return not getattr(value, "__isabstractmethod__", False)
        has_get = callable(getattr(value, "__get__", None))
        has_set_del = callable(getattr(value, "__set__", None)) or callable(
            getattr(value, "__delete__", None)
        )
        return has_get and has_set_del

    def _from_dict(o: Any) -> Iterator[str]:
        yield from _yield_new_public(*getattr(o, "__dict__", {}).keys())

    def _from_class(cls: type) -> Iterator[str]:
        cls_vars = dict(vars(cls))
        yield from _yield_new_public(*(n for n, v in cls_vars.items() if _is_valid_descriptor(v)))
        yield from _yield_new_public(*getattr(cls, "__annotations__", {}))
        slots = getattr(cls, "__slots__", ())
        yield from _yield_new_public(*((slots,) if isinstance(slots, str) else slots))
        yield from _yield_new_public(*cls_vars)

    yield from _from_dict(obj)
    for cls in obj.__class__.__mro__:
        yield from _from_class(cls)


def iter_attributes(obj: Any) -> Iterator[tuple[str, Any]]:
    """Yield (name, value) pairs for public fields that can be read via getattr.

    Skips the "mro" attribute on type objects and ignores fields that raise
    AttributeError when accessed.
    """
    for field_name in iter_fields(obj):
        if field_name == "mro" and isinstance(obj, type):
            continue
        try:
            yield (field_name, getattr(obj, field_name))
        except AttributeError:
            continue


def create_parameter(name: str, kind: str, annotation: Any = MISSING, default: Any = MISSING) -> Parameter:
    p_kind: ParameterKind
    match kind.strip().casefold():
        case "positional_only" | "po":
            p_kind = ParameterKind.POSITIONAL_ONLY
        case "positional_or_keyword" | "pok":
            p_kind = ParameterKind.POSITIONAL_OR_KEYWORD
        case "var_positional" | "vp":
            p_kind = ParameterKind.VAR_POSITIONAL
        case "keyword_only" | "ko":
            p_kind = ParameterKind.KEYWORD_ONLY
        case "var_keyword" | "vk":
            p_kind = ParameterKind.VAR_KEYWORD
        case _:
            raise ValueError(kind)

    return Parameter(
        name,
        p_kind,
        annotation=annotation if annotation is not MISSING else Parameter.empty,
        default=default if default is not MISSING else Parameter.empty,
        )

def create_signature(*parameters: Parameter, return_annotation: Any = MISSING) -> Signature:
    return Signature(
        list(parameters),
        return_annotation=return_annotation if return_annotation is not MISSING else Parameter.empty,
    )


@dataclass
class ConstraintBase[T]:
    target_type: type[T] | MissingType = MISSING
    target_base: type[type[T]] | MissingType = MISSING
    max_val: T | MissingType = MISSING
    min_val: T | MissingType = MISSING
    is_val: T | MissingType = MISSING
    predicate: Callable[[T], bool] | MissingType = MISSING

    def __post_init__(self) -> None:
        if self.target_type is MISSING:
            if self.is_val is not MISSING:
                self.target_type = type(self.is_val)
            elif self.max_val is not MISSING:
                self.target_type = type(self.max_val)
            elif self.min_val is not MISSING:
                self.target_type = type(self.min_val)

    def __call__(self, val: Any) -> bool:
        if self.target_type is not MISSING:
            if not isinstance(val, self.target_type):
                return False
        if self.target_base is not MISSING:
            if not issubclass(val, self.target_base):
                return False
        if self.max_val is not MISSING:
            if val > self.max_val:
                return False
        if self.min_val is not MISSING:
            if val < self.min_val:
                return False
        if self.predicate is not MISSING:
            return self.predicate(val)
        return True


@dataclass
class TypeNode:
    _parent: Any
    target: Any

    def __repr__(self) -> str:
        template = "type {name}{type_params} = {value}"
        ...

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
    def origin(self) -> Any | None:
        return get_origin(self.inner_type)

    @cached_property
    def args(self) -> tuple[TypeNode, ...]:
        if self.is_literal:
            return ()
        return tuple(TypeNode(self, a) for a in get_args(self.inner_type) if a is not type(None))

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
            return (self.target.default is not Parameter.empty)
        elif self.is_field:
            return (self.target.default is not MISSING)

    @cached_property
    def default(self) -> Any:
        if self.has_default:
            return self.target.default
        return MISSING

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


@dataclass
class CallableNode:
    _parent: Any
    target: Any

    @cached_property
    def parameters(self) -> tuple[FieldNode, ...]:
        return tuple(FieldNode(self, value) for value in inspect_signature(self.target, eval_str=True).parameters)

    @cached_property
    def return_annotation(self) -> TypeNode | MissingType:
        if (anno := get_type_hints(self.target, include_extras=True).get("return", None)) is not None:
            return TypeNode(self, anno)
        return MISSING


@dataclass
class ParsedType:
    ...

@dataclass
class ParsedField:
    ...

@dataclass
class ParsedMethod:
    ...

@dataclass
class ParsedFunction:
    ...

@dataclass
class ParsedClass:
    ...

@dataclass
class ParsedInstance:
    ...

@dataclass
class GraphParse:
    ...

