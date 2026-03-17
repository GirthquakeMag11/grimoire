from collections import UserDict
from collections.abc import Hashable, Mapping
from types import MappingProxyType
from typing import Any

from .inspection import iter_attributes

_MISSING = object()


def column[K, V](
    data: Mapping[K, V],
    name: str,
    *,
    fill_value: Any = _MISSING,
) -> MappingProxyType[K, Any]:
    if fill_value is _MISSING:
        result = {key: getattr(value, name) for key, value in data.items() if hasattr(value, name)}
    else:
        result = {key: getattr(value, name, fill_value) for key, value in data.items()}
    return MappingProxyType(result)


def row[K, V](data: Mapping[K, V], key: K) -> MappingProxyType[str, V]:
    return MappingProxyType(dict(iter_attributes(data[key])))


class Table[K: Hashable, V](UserDict[K, V]):
    def __init__(self, fill_value: Any = _MISSING) -> None:
        if fill_value is not _MISSING:
            self._fill_value: Any = fill_value
        super().__init__()

    def set_fill_value(self, value: Any) -> None:
        setattr(self, "_fill_value", value)

    def clear_fill_value(self) -> None:
        if hasattr(self, "_fill_value"):
            delattr(self, "_fill_value")

    def column(self, name: str, *, fill_value: Any = _MISSING) -> MappingProxyType[K, Any]:
        if fill_value is _MISSING and hasattr(self, "_fill_value"):
            fill_value = self._fill_value
        return column(data=self.data, name=name, fill_value=fill_value)

    def row(self, key: K) -> MappingProxyType[str, V]:
        return row(data=self.data, key=key)
