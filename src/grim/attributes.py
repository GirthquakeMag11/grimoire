from __future__ import annotations

import collections.abc
from uuid import uuid4, UUID
from types import GetSetDescriptorType
from typing import Any, Callable, Dict, Iterator, List

from .utilities import update_dict, update_list


def nested_field(field: str) -> List[str]:
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
            next_layer = getattr(current_layer, f)
            current_layer = next_layer
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
        nonlocal getter
        nonlocal outer_args
        nonlocal outer_kwargs

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
        return not (field.startswith("_") or field.endswith("__"))

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
            yield from if_annos(cls)
            yield from if_slots(cls)
            yield from if_dict(cls)

    yield from if_dict(obj)
    yield from walk_mro(obj)


def iter_attributes(obj: Any) -> Iterator[str, Any]:
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

def to_dict(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, (collections.abc.Mapping, collections.abc.Iterable)):
        try:
            return dict(obj, type=type(obj).__name__)
        except TypeError:
            return dict(enumerate(obj), type=type(obj).__name__)
    elif isinstance(obj, (str, bool, int, complex, bytes, type(None))):
        return {"type": type(obj).__name__, "value": obj}
    return dict(iter_attributes(obj), type=type(obj).__name__)


def walk(obj: Any, *keys: str) -> List[Dict[str, Any]]:
    layers = [to_dict(obj)]
    for key in keys:
        layers.append(to_dict(layers[-1].setdefault(key, {})))
    return layers

