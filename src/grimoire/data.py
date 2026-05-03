from __future__ import annotations

from annotationlib import (
    Format,
)
from collections.abc import (
    Callable,
    Iterable,
    Iterator,
)
from dataclasses import (
    MISSING as MISSING,
)
from inspect import (
    Parameter,
    Signature,
    getattr_static,
)
from inspect import (
    isclass as inspect_isclass,
)
from inspect import (
    signature as inspect_signature,
)
from sys import (
    _getframe as get_frame,
)
from sys import (
    _getframemodulename as get_frame_module_name,
)
from types import (
    FunctionType,
    LambdaType,
    MethodType,
)
from typing import (  # type: ignore[attr-defined]
    Any,
    TypedDict,
    _TypedDictMeta,
    cast,
    get_type_hints,
)

from .typenode import TypeNode


class MissingTypeAnnotationError(BaseException):
    def __init__(self, type_name: str, *field_names: str) -> None:
        super().__init__(
            f"{type_name!s} is missing type annotation for field(s): {', '.join(fn for fn in field_names)}"
        )


def is_lambdafunc(obj: Any) -> bool:
    return (type(obj) is LambdaType) and (getattr(obj, "__name__", None) == "<lambda>")


def is_namedfunc(obj: Any) -> bool:
    return (type(obj) is FunctionType) and (getattr(obj, "__name__", "<lambda>") != "<lambda>")


def get_module_name[T](obj: T) -> str:
    objtype: type[T] = obj if inspect_isclass(obj) else type(obj)
    return objtype.__module__


def get_type_name[T](obj: T | type[T]) -> str:
    if is_lambdafunc(obj):
        return "lambda"
    objtype: type[T] = obj if inspect_isclass(obj) else type(obj)  # type: ignore[assignment]
    return objtype.__name__


def caller_module_name(*, depth: int = 1, default: str = "__main__") -> str:
    try:
        return get_frame_module_name(depth + 1) or default
    except AttributeError:
        pass
    try:
        return str(get_frame(depth + 1).f_globals.get("__name__", default))
    except AttributeError, ValueError:
        pass
    return default


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


def iter_type_annotations[T](obj: T | type[T], *, strict: bool = True) -> Iterator[tuple[str, Any]]:
    target: type[T] = obj if inspect_isclass(obj) else type(obj)  # type: ignore[assignment]
    hints: dict[str, Any] = {}
    try:
        hints = get_type_hints(target, include_extras=True)
    except TypeError as e:
        if "does not have annotations" in str(e) and strict is True:
            raise MissingTypeAnnotationError(get_type_name(obj), *iter_fields(obj)) from None

    for field_name in iter_fields(obj):
        if field_name == "mro" and isinstance(obj, type):
            continue
        if field_name not in hints and strict is True:
            raise MissingTypeAnnotationError(get_type_name(obj), field_name)

        yield (field_name, hints.get(field_name, Any))


def iter_parameter_annotations(
    obj: Callable[..., Any], *, strict: bool = True
) -> Iterator[tuple[str, Any]]:
    sig: Signature = inspect_signature(obj, eval_str=True, annotation_format=Format.FORWARDREF)
    params: dict[str, Any] = dict(sig.parameters)
    for name, param in params.items():
        if param.annotation is Parameter.empty:
            if strict is True:
                raise MissingTypeAnnotationError(get_type_name(obj), name)
            else:
                yield (name, Any)
        else:
            yield (name, param.annotation)


def construct_typeddict(
    name: str,
    module: str,
    annotations: dict[str, Any],
    total: bool = False,
    required_keys: Iterable[str] = (),
    optional_keys: Iterable[str] = (),
    readonly_keys: Iterable[str] = (),
) -> type[dict[str, Any]]:
    return cast(
        type[dict[str, Any]],
        _TypedDictMeta(
            name,
            (),
            {
                "__annotations__": annotations,
                "__module__": module,
                "__orig_bases__": (TypedDict,),
                "__total__": total,
                "__required_keys__": frozenset(required_keys),
                "__optional_keys__": frozenset(optional_keys),
                "__readonly_keys__": frozenset(readonly_keys),
            },
        ),
    )


def typeddict_from(
    obj: Any,
    *,
    total: bool = False,
    type_name: str | None = None,
    module_name: str | None = None,
) -> type[dict[str, Any]]:
    if inspect_isclass(obj):
        annotations = dict(iter_type_annotations(obj, strict=False))
    elif isinstance(obj, (FunctionType, MethodType, LambdaType)):
        annotations = dict(iter_parameter_annotations(obj, strict=False))
    else:
        return typeddict_from(type(obj), total=total, type_name=type_name, module_name=module_name)

    name = type_name if type_name is not None else get_type_name(obj)
    module = (
        module_name if module_name is not None else caller_module_name(default=get_module_name(obj))
    )
    typenodes = {name: TypeNode(anno) for name, anno in annotations.items()}

    required: set[str] = set()
    optional: set[str] = set()
    readonly: set[str] = set()

    for name, node in typenodes.items():
        if node.is_required:
            required.add(name)
        if node.is_optional:
            optional.add(name)
        if node.is_readonly:
            readonly.add(name)

    return construct_typeddict(name, module, annotations, total, required, optional, readonly)
