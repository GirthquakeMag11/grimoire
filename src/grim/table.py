from collections import UserDict
from collections.abc import Hashable
from dataclasses import dataclass, field

from .inspection import iter_attributes

@dataclass
class Column:
    name: str
    data: dict[Hashable, Any]

@dataclass
class Row:
    key: Hashable
    data: dict[str, Any]

class Table(UserDict):

    def row(self, key: Hashable):
        return Row(key, dict(iter_attributes(self.data[key])))

    def column(self, name: str):
        return Column(name, dict({u_id: getattr(item, name) for u_id, item in self.data.items() if hasattr(item, name)}))
