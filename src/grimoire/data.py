from __future__ import annotations

import inspect
import types
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from typing import (
    Any,
    get_type_hints,
)


def utcnow() -> datetime:
    return datetime.now(UTC)


def compose_signature(obj: Callable[[...], ...]) -> dict[str, Any]:
    signature: dict[str, Any] = {}
    hints: dict[str, Any] = get_type_hints(obj)

    if "return" in hints:
        signature["return"] = hints["return"]

    for idx, (keyword, param) in enumerate(inspect.signature(obj).parameters.items()):
        parameter = {}

        if param.kind is inspect.Parameter.VAR_KEYWORD:
            parameter["unpack"] = dict

        if param.kind is inspect.Parameter.VAR_POSITIONAL:
            parameter["unpack"] = tuple

        if param.kind in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
            parameter["position"] = None

        if param.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.VAR_POSITIONAL,
        ):
            parameter["position"] = idx

        if param.default is not inspect.Parameter.empty:
            parameter["default"] = param.default

        if keyword in hints:
            parameter["annotation"] = hints.get(keyword)

        if parameter:
            signature.setdefault("parameters", {})[keyword] = parameter

    return signature


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


<<<<<<< Updated upstream
=======
def copy_namespace(obj: Any) -> types.SimpleNamespace:
    return types.SimpleNamespace(iter_attributes(obj))
>>>>>>> Stashed changes
