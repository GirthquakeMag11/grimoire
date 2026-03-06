from collections.abc import Hashable, MutableMapping
from types import MappingProxyType
from typing import Any
from uuid import UUID, uuid4

from .inspection import dict_attributes

_MISSING = object()


class Table[K: Hashable, V](MutableMapping[K, V]):
    def __init__(self) -> None:
        self.data: dict[K, V] = {}

    def set(self, key: K, value: V) -> K:
        self.data[key] = value
        return key

    def add(self, value: V) -> K:
        new_id = uuid4()
        self.set(new_id, value)
        return new_id

    def pop(self, key: K, default: Any | None = None) -> V | Any | None:
        return self.data.get(key, default)

    def column(self, name: str, *, fill_value: Any = _MISSING) -> MappingProxyType[K, V]:
        if fill_value is _MISSING:
            data = {
                key: getattr(value, name)
                for key, value in self.data.items()
                if hasattr(value, name)
            }
        else:
            data = {key: getattr(value, name, fill_value) for key, value in self.data.items()}
        return MappingProxyType(data)

    def row(self, key: K) -> MappingProxyType[str, V]:
        return MappingProxyType(dict_attributes(self.data[key]))
