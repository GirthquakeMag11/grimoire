from __future__ import annotations

import collections.abc
from types import GetSetDescriptorType
from typing import Any, Iterator

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
        return not (field.startswith('_') or field.endswith('__'))

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
            for dm in ('__get__', '__set__', '__set_name__', '__delete__')
        ):
            return True
        return False

    def if_desc(cls):
        data = [name for name, item in dict(vars(cls)).items() if valid_attr_item(item)]
        yield from validate(*data)

    def if_annos(cls):
        yield from validate(
            *list(getattr(cls, '__annotations__', {}).keys())
            )

    def if_slots(cls):
        slots = getattr(cls, '__slots__', ())
        match slots:
            case str():
                yield from validate(slots)
            case collections.abc.Iterable():
                yield from validate(*slots)

    def if_dict(obj):
        if hasattr(obj, '__dict__'):
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

