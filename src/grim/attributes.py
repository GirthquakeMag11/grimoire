"""Utilities for introspecting and accessing object attributes."""

from __future__ import annotations

import collections.abc
import inspect
from types import GetSetDescriptorType
from typing import Any, Callable, Iterator, Literal

from .utilities import update_dict, update_list


def nested_field(field: str) -> list[str]:
    """Convert a nested attribute name to a list of individual names.
    Example:
        "widget.information.name" -> ["widget", "information", "name"]
    """
    return [f.strip() for f in field.split(".") if f.strip()]


def attrgetter(field: str) -> Callable[[Any], Any]:
    """Create a function that will accept any object and attempt to
    return what the 'field' parameter resolves to.

    Accepts nested fields.
    """
    fields = nested_field(field)

    def getter(obj: Any):
        nonlocal fields
        current_layer = obj
        for f in fields:
            current_layer = getattr(current_layer, f)
        return current_layer

    return getter


def methodcaller(
    name: str, *outer_args: Any, **outer_kwargs: Any
) -> Callable[[Any], Any]:
    """Create a function that will accept any object and attempt to
    return the result of the method 'name' resolves to.

    Parameters provided will be passed along to the created function
    but can be overridden by any parameters passed directly into it
    along with the object.

    Accepts nested fields.
    """
    getter = attrgetter(name)

    def caller(obj: Any, *inner_args: Any, **inner_kwargs: Any) -> Any:
        args = update_list(outer_args, inner_args)
        kwargs = update_dict(outer_kwargs, inner_kwargs)
        method = getter(obj)

        return method(*args, **kwargs)

    return caller


def iter_fields(obj: Any) -> Iterator[str]:
    """Yield unique public field names discoverable from an object and its MRO.

    Names are collected from instance dict, then each class in the MRO via
    annotations, slots, and class dict keys, with duplicates removed.
    """
    seen = set()

    def is_new(field):
        nonlocal seen
        if field not in seen:
            seen.add(field)
            return True
        return False

    def is_public(field):
        return not (
            field.startswith("_") or (field.startswith("__") and field.endswith("__"))
        )

    def validate(*fields):
        for f in fields:
            if is_new(f) and is_public(f):
                yield f

    def valid_attr_item(item):
        if isinstance(item, property) and not getattr(
            item, "__isabstractmethod__", False
        ):
            return True
        if isinstance(item, GetSetDescriptorType):
            return True
        if any(
            hasattr(item, dm)
            for dm in ("__get__", "__set__", "__set_name__", "__delete__")
        ):
            return True
        return False

    def if_desc(cls):
        data = [name for name, item in dict(vars(cls)).items() if valid_attr_item(item)]
        yield from validate(*data)

    def if_annos(cls):
        yield from validate(*list(getattr(cls, "__annotations__", {}).keys()))

    def if_slots(cls):
        slots = getattr(cls, "__slots__", ())
        match slots:
            case str():
                yield from validate(slots)
            case collections.abc.Iterable():
                yield from validate(*slots)

    def if_dict(obj):
        if hasattr(obj, "__dict__"):
            yield from validate(*list(obj.__dict__.keys()))

    def walk_mro(obj):
        for cls in obj.__class__.__mro__:
            yield from if_desc(cls)
            yield from if_annos(cls)
            yield from if_slots(cls)
            yield from if_dict(cls)

    yield from if_dict(obj)
    yield from walk_mro(obj)


def iter_attributes(obj: Any) -> Iterator[tuple[str, Any]]:
    """Yield (name, value) pairs for public fields that can be read via getattr.

    Skips the "mro" attribute on type objects and ignores fields that raise
    AttributeError when accessed.
    """
    for field in iter_fields(obj):
        if field == "mro" and isinstance(obj, type):
            continue
        try:
            yield (field, getattr(obj, field))
        except AttributeError:
            continue


def classify_attribute(
    obj: Any, field: str
) -> Literal["dict", "slots", "property", "descriptor"] | None:
    """Classify how an attribute is stored on an object."""
    if field in getattr(obj, "__dict__", {}):
        return "dict"
    if field in getattr(type(obj), "__slots__", ()):
        return "slots"
    raw = inspect.getattr_static(obj, field)
    if isinstance(raw, property):
        return "property"
    if any(
        hasattr(raw, dm) for dm in ("__get__", "__set__", "__set_name__", "__delete__")
    ):
        return "descriptor"
    return None


def obj_data(obj: Any) -> dict[str, Any]:
    """Extract all public attribute names and values as a dictionary."""
    return dict(iter_attributes(obj))


def obj_metadata(obj: Any) -> dict[str, Any]:
    """Extract type, module, and id metadata from an object."""
    return {
        "type": type(obj).__name__,
        "module": type(obj).__module__,
        "id": id(obj),
    }


def decompose(obj: Any, _seen: set[int] | None = None) -> dict[str, Any]:
    """Recursively decompose an object into nested dictionaries.

    Primitives become {'type': ..., 'value': ...}.
    Containers become {'type': ..., 'data': ...}.
    Complex objects become {'type': ..., 'attributes': {...}}.

    Handles circular references by tracking object ids.
    """
    if _seen is None:
        _seen = set()

    obj_id = id(obj)
    obj_type = type(obj).__name__

    # Handle circular references
    if obj_id in _seen:
        return {"type": obj_type, "circular_reference": True, "id": obj_id}

    # Primitives
    if obj is None or isinstance(obj, (bool, int, float, str, bytes)):
        return {"type": obj_type, "value": obj}

    # Mark as seen for circular reference detection
    _seen.add(obj_id)

    try:
        # Lists and tuples
        if isinstance(obj, (list, tuple)):
            data = [decompose(item, _seen) for item in obj]
            return {"type": obj_type, "data": data}

        # Dictionaries
        if isinstance(obj, dict):
            data = {str(k): decompose(v, _seen) for k, v in obj.items()}
            return {"type": obj_type, "data": data}

        # Sets and frozensets
        if isinstance(obj, (set, frozenset)):
            data = [decompose(item, _seen) for item in obj]
            return {"type": obj_type, "data": data}

        # Complex objects - decompose attributes
        attributes = {}
        for name, value in iter_attributes(obj):
            try:
                attributes[name] = decompose(value, _seen)
            except Exception:
                # Skip attributes that cause issues during decomposition
                attributes[name] = {"type": "error", "value": "<undecomposable>"}

        return {"type": obj_type, "attributes": attributes}

    finally:
        # Remove from seen set on the way back up
        _seen.discard(obj_id)
