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


def iter_annotations(obj: Any) -> Iterator[tuple[str, Any]]:
    hints = get_type_hints(obj, include_extras=True, eval_str=True)
    for field_name in iter_fields(obj):
        if field_name == "mro" and isinstance(obj, type):
            continue
        if field_name in hints:
            yield (field_name, hints[field_name])

