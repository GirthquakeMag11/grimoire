from __future__ import annotations

from sys import (
    _getframe as get_frame,
    _getframemodulename as get_frame_module_name,
)
from annotationlib import (
    Format,
)
from enum import (
    Enum,
    IntEnum,
)
from dataclasses import (
    dataclass,
    is_dataclass,
    field,
    Field,
    MISSING as MISSING,
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
    getattr_static,
)
from types import (
    MappingProxyType,
    UnionType,
    FunctionType,
    LambdaType,
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
    Final,
    NamedTuple,
    _TypedDictMeta,
    _caller,
)


class MissingTypeAnnotationError(BaseException):
    def __init__(self, type_name: str, *field_names: str) -> None:
        super().__init__(
            f"{type_name!s} is missing type annotation for field(s): {", ".join(fn for fn in field_names)}"
            )


def is_lambdafunc(obj: Any) -> bool:
    return (type(obj) is LambdaType) and (getattr(obj, "__name__", None) == "<lambda>")


def is_namedfunc(obj: Any) -> bool:
    return (type(obj) is FunctionType) and (getattr(obj, "__name__", "<lambda>") != "<lambda>")


def iter_fields[T](obj: T) -> Iterator[str]:
    """Yield unique public field names discoverable from an object and its MRO.

    Names are collected from the instance dict first, then each class in the
    MRO via descriptors, annotations, slots, and remaining class dict keys,
    with duplicates removed.

    Respects encapsulation and avoids private namespaces.
    """
    seen: set[str] = set()
    objtype: type[T] = obj if inspect_isclass(obj) else type(obj)

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
    for cls in objtype.__mro__:
        yield from _from_class(cls)


def iter_attributes(obj: Any, *, static: bool = False) -> Iterator[tuple[str, Any]]:
    """Yield (name, value) pairs for public fields that can be read via getattr.

    Skips the "mro" attribute on type objects.
    """
    getter = getattr_static if static is True else getattr
    for field_name in iter_fields(obj):
        if field_name == "mro" and isinstance(obj, type):
            continue
        yield (field_name, getter(obj, field_name, MISSING))


def iter_annotations[T](obj: T | type[T], *, strict: bool = True) -> Iterator[tuple[str, Any]]:
    target: type[T] = obj if inspect_isclass(obj) else type(obj)
    hints: dict[str, Any] = {}
    try:
        hints = get_type_hints(target, include_extras=True)
    except TypeError as e:
        if "does not have annotations" in str(e) and strict is True:
            raise MissingTypeAnnotationError(type(obj), *iter_fields(obj)) from None

    for field_name in iter_fields(obj):
        if field_name == "mro" and isinstance(obj, type):
            continue
        if field_name not in hints and strict is True:
            raise MissingTypeAnnotationError(type(obj), field_name)

        yield (field_name, hints.get(field_name, Any))


def get_module_name[T](obj: T) -> str:
    objtype: type[T] = obj if inspect_isclass(obj) else type(obj)
    return objtype.__module__


def get_type_name[T](obj: T | type[T]) -> str:
    if is_lambdafunc(obj):
        return "lambda"
    objtype: type[T] = obj if inspect_isclass(obj) else type(obj)
    return objtype.__name__


def caller_module_name(*, depth: int = 1, default: str = "__main__") -> str:
    try:
        return get_frame_module_name(depth + 1) or default
    except AttributeError:
        pass
    try:
        return get_frame(depth + 1).f_globals.get("__name__", default)
    except (AttributeError, ValueError):
        pass
    return default


def model_typeddict[T](obj: T, total: bool = False, strict: bool = True, type_name: str | None = None, mod_name: str | None = None) -> type[dict]:
    ns: dict[str, Any] = {
        "__annotations__": dict(iter_annotations(obj, strict=strict)),
        "__module__": mod_name if mod_name is not None else caller_module_name(default=get_module_name(obj))
    }

    tn: str = type_name if type_name is not None else get_type_name(obj)
    td: dict[str, Any] = _TypedDictMeta(tn, (), ns, total=total)
    object.__setattr__(td, "__orig_bases__", (TypedDict,))
    return td


"""
def parameter_typeddict[T](obj: T, total: bool = False, strict: bool = True, typename: str | None = None, modname: str | None = None) -> type[dict]:
    ns: dict[str, Any] = {
        "__annotations__": {},
        "__module__": modname if modname is not None else caller_module_name(default=get_module_name(obj))
    }
    tn: str | None = typename if typename is not None else get_type_name(obj)
    sig: dict[str, Parameter] = dict(inspect_signature(obj, eval_str=True, annotation_format=Format.FORWARDREF).parameters)
"""


class SchematicFlags(IntEnum):
    """
    Schematic flags are used to indicate a particular parameter
    for multiple schematic fields at once.

    For example:

    @schematic(total=False)
    class Example:
        x: int
        y: str = field(required=True)
        z: bool = field(required=True)

    Has the same effect as:

    @schematic(total=False)
    class Example:
        x: int
        _: SchematicFlags.REQUIRED
        y: str
        z: bool

    """
    REQUIRED = 0
    NOT_REQUIRED = 1
    OPTIONAL = 2
