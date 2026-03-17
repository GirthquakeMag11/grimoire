import inspect
from collections.abc import Iterator
from typing import Any, Union, get_args, get_origin, get_type_hints


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
        has_get = callable(getattr(class_raw, "__get__", None))
        has_set_del = callable(getattr(class_raw, "__set__", None)) or callable(getattr(class_raw, "__delete__", None))
        return (has_get and has_set_del)

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


def classify_field(obj: object, field: str) -> Literal["dict", "slots", "property", "data_descriptor", "non_data_descriptor"]:
    """
    Classify how an attribute is stored or resolved on an object.

    Mirrors Python's attribute lookup priority:
        data descriptors  >  instance __dict__ / slots  >  non-data descriptors

    Returns:
        "dict"                  – stored in the instance's __dict__
        "slots"                 – stored via a __slots__ member (anywhere in the MRO)
        "property"              – a property descriptor on the class
        "data_descriptor"       – descriptor with __get__ and __set__ or __delete__
        "non_data_descriptor"   – descriptor with only __get__

    Raises:
        AttributeError: if the field does not exist on the object at all.
        ValueError:     if the field exists but has no recognised storage kind
                        (e.g. a plain class variable with no descriptor protocol).
    """
    _MISSING = object()

    cls = type(obj)
    class_raw: object = _MISSING
    in_slots: bool = False

    for _class in cls.__mro__:
        if class_raw is _MISSING and field in _class.__dict__:
            class_raw = _class.__dict__[field]
        if not in_slots and field in getattr(_class, "__slots__", ()):
            in_slots = True
        if class_raw is not _MISSING and in_slots:
            break

    if class_raw is not _MISSING:
        if isinstance(class_raw, property):
            return "property"

        has_get = callable(getattr(class_raw, "__get__", None))
        has_set_del = callable(getattr(class_raw, "__set__", None)) or callable(getattr(class_raw, "__delete__", None))
        if has_get and has_set_del:
            return "data_descriptor"

    if field in getattr(obj, "__dict__", {}):
        return "dict"

    if in_slots is True:
        return True

    if class_raw is not _MISSING and callable(getattr(class_raw, "__get__", None)):
        return "non_data_descriptor"

    if class_raw is _MISSING:
        raise AttributeError(
            f"{cls.__name__!r} object has no attribute {field!r}"
        )

    raise ValueError(
        f"field {field!r} on {cls.__name__!r} has no recognised storage kind "
        f"(raw type: {type(class_raw).__name__!r})"
    )


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
