from collections.abc import Hashable, Mapping
from typing import Any

from .inspection import dict_attributes


class Column:
    def __init__(self, table: Mapping[Hashable, Any], name: str) -> None:
        self.name: str = name
        self.data: dict[Hashable, Any] = {
            key: getattr(value, name) for key, value in table.items() if hasattr(value, name)
        }


class Row:
    def __init__(self, table: Mapping[Hashable, Any], key: Hashable) -> None:
        self.key: Hashable = key
        self.data: dict[str, Any] = dict_attributes(table[key])
