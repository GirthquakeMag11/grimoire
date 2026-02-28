from __future__ import annotations

import inspect
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from types import GetSetDescriptorType
<<<<<<<< HEAD:draft/grim/inspections.py
from typing import Any, TypeAlias, Union, get_args, get_origin
========
from typing import Any, Callable, Iterator, Union, get_args, get_origin
>>>>>>>> alt:draft/grim/attributes.py

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


def methodcaller(name: str, *outer_args: Any, **outer_kwargs: Any) -> Callable[[Any], Any]:
    """Create a function that will accept any object and attempt to
    return the result of the method 'name' resolves to.

    Parameters provided will be passed along to the created function
    but can be overridden by any parameters passed directly into it
    along with the object.

    Accepts nested fields.
    """
    getter = attrgetter(name)

    def caller(obj: Any, *inner_args: Any, **inner_kwargs: Any) -> Any:
        args = update_list(list(outer_args), inner_args)
        kwargs = update_dict(outer_kwargs, inner_kwargs)
        method = getter(obj)

        return method(*args, **kwargs)

    return caller


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
        if isinstance(value, GetSetDescriptorType):
            return True
        return any(hasattr(value, dm) for dm in ("__get__", "__set__", "__set_name__", "__delete__"))

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


def classify_attribute(obj: Any, field: str) -> str:
    """Classify how an attribute is stored on an object."""
    if field in getattr(obj, "__dict__", {}):
        return "__dict__"
    if field in getattr(type(obj), "__slots__", ()):
        return "__slots__"
    raw = inspect.getattr_static(obj, field)
    if isinstance(raw, property):
        return "_property_"
    if any(hasattr(raw, dm) for dm in ("__get__", "__set__", "__set_name__", "__delete__")):
        return "_descriptor_"
    return None


def field_is_optional(obj: Any, field: str) -> bool:
    hints = inspect.get_type_hints(obj)
    field_anno = hints.get(field)
    field_origin = get_origin(field_anno)
    if field_origin is Union:
        field_args = get_args(field_anno)
        return len(field_args) == 2 and None in field_args
    return False
<<<<<<<< HEAD:draft/grim/inspections.py


@dataclass
class TypeNode:
    hint: Any
    origin: Any
    args: tuple
    children: list[TypeNode] = field(default_factory=list)

    @property
    def is_leaf(self):
        return not self.children


TypeHint: TypeAlias = Any


def build_type_tree(hint: TypeHint) -> TypeNode:
    origin = get_origin(hint)
    args = get_args(hint)
    node = TypeNode(hint=hint, origin=origin, args=args)
    for arg in args:
        node.children.append(build_type_tree(arg))
    return node


def collect_type_leaves(node: TypeNode) -> list[TypeHint]:
    if node.is_leaf:
        return [node.hint]
    return [leaf for child in node.children for leaf in collect_type_leaves(child)]


def contains_type(node: TypeNode, target: TypeHint) -> bool:
    if node.hint is target:
        return True
    return any(contains_type(child, target) for child in node.children)
========
>>>>>>>> alt:draft/grim/attributes.py
