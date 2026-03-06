"""
Row, column, and table containers for attribute-oriented structured data access.

Classes:
    Column                  `Mapping[Hashable, Any]`    Per-attribute view across all table entries.
    Row                     `Mapping[str, Any]`         Per-entry view of all attributes for one key.
    Table                   `UserDict[Hashable, Any]`   Hashable-keyed store of arbitrary value objects.

Table interface
---------------
Attributes:
    data                    `dict[Hashable, Any]`       Underlying mutable dict inherited from `UserDict`.

Methods:
    column(`name`)          `Column`                    Column view of the named attribute across all entries.
    row(`key`)              `Row`                       Row view of all attributes for the entry at `key`.

Column access (via `.column(`name`)`):
    .name                   `str`                       Name of the attribute this column represents.
    .data                   `MappingProxyType`          Immutable mapping of row keys to attribute values.
    [`key`]                 `Any`                       Attribute value for the entry at `key`.

Row access (via `.row(`key`)`):
    .key                    `Hashable`                  The table key identifying this row.
    .data                   `MappingProxyType[str, Any]` Immutable mapping of attribute names to values.
    [`name`]                `Any`                       Value of the named attribute for this row.
"""

from collections import UserDict
from collections.abc import Hashable, ItemsView, Iterator, KeysView, Mapping, ValuesView
from types import MappingProxyType
from typing import Any
from uuid import uuid4

from .inspection import dict_attributes

_MISSING = object()


class Column(Mapping[Hashable, Any]):
    def __init__(
        self, table: Mapping[Hashable, Any], name: str, *, fill_value: Any = _MISSING
    ) -> None:
        self.name = name
        if fill_value is _MISSING:
            data = {
                key: getattr(value, name) for key, value in table.items() if hasattr(value, name)
            }
        else:
            data = {key: getattr(value, name, fill_value) for key, value in table.items()}
        self.data = MappingProxyType(data)

    def __getitem__(self, key: Hashable) -> Any:
        return self.data[key]

    def __iter__(self) -> Iterator[Hashable]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def keys(self) -> KeysView[Hashable]:
        return self.data.keys()

    def values(self) -> ValuesView[Any]:
        return self.data.values()

    def items(self) -> ItemsView[Hashable, Any]:
        return self.data.items()


class Row(Mapping[str, Any]):
    def __init__(self, table: Mapping[Hashable, Any], key: Hashable) -> None:
        self.key: Hashable = key
        self.data: MappingProxyType[str, Any] = MappingProxyType(dict_attributes(table[key]))

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def keys(self) -> KeysView[str]:
        return self.data.keys()

    def values(self) -> ValuesView[Any]:
        return self.data.values()

    def items(self) -> ItemsView[str, Any]:
        return self.data.items()


class Table(UserDict[Hashable, Any]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        for arg in args:
            self.data[uuid4()] = arg
        for kw, arg in kwargs.items():
            self.data[kw] = arg

    def column(self, name: str, *, fill_value: Any = _MISSING) -> Column:
        return Column(self, name, fill_value=fill_value)

    def row(self, key: Hashable) -> Row:
        return Row(self, key)
