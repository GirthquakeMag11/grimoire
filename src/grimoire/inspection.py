from collections.abc import Iterator
from dataclasses import dataclass, field, InitVar
import types
import typing
from typing import (
    Any,
    get_type_hints,
    get_origin,
    get_args,
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


def decompose(obj: Any, _cache: dict[int, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Recursively decompose an object into nested dictionaries.

    Primitives become {'type': ..., 'value': ...}.
    Containers become {'type': ..., 'data': ...}.
    Complex objects become {'type': ..., 'attributes': {...}}.

    Circular references are handled by reusing the same dict for repeated objects.
    Exceptions raised when attempting to decompose attributes are incorporated into
        object data.
    """
    if _cache is None:
        _cache = {}

    obj_id = id(obj)
    obj_type = type(obj).__name__

    if obj is None or isinstance(obj, (bool, int, float, str, bytes)):
        return {"type": obj_type, "value": obj}

    if obj_id in _cache:
        return _cache[obj_id]

    result: dict[str, Any] = {"type": obj_type}
    _cache[obj_id] = result

    if isinstance(obj, (list, tuple)):
        result["data"] = [decompose(item, _cache) for item in obj]
        return result

    if isinstance(obj, dict):
        result["data"] = {str(k): decompose(v, _cache) for k, v in obj.items()}
        return result

    if isinstance(obj, (set, frozenset)):
        result["data"] = [decompose(item, _cache) for item in obj]
        return result

    attributes = {}
    for name, value in iter_attributes(obj):
        try:
            attributes[name] = decompose(value, _cache)
        except Exception as e:
            attributes[name] = {"type": type(e).__name__, "value": str(e)}

    result["attributes"] = attributes
    return result

