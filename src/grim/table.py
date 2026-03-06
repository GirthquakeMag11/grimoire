from collections.abc import Hashable, Mapping
from types import MappingProxyType
from typing import Any

from .inspection import dict_attributes

_MISSING = object()


def column(
    data: Mapping[Hashable, Any], name: str, *, fill_value: Any = _MISSING
) -> MappingProxyType[Hashable, Any]:
    if fill_value is _MISSING:
        data = {key: getattr(value, name) for key, value in data.items() if hasattr(value, name)}
    else:
        data = {key: getattr(value, name, fill_value) for key, value in data.items()}
    return MappingProxyType(data)


def row(data: Mapping[Hashable, Any], key: Hashable) -> MappingProxyType[str, Any]:
    return MappingProxyType(dict_attributes(data[key]))
