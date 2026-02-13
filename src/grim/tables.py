from __future__ import annotations

from typing import Any, Iterator, Optional, Tuple
from uuid import UUID, uuid4

from .attributes import iter_attributes


class Table:
    def __init__(self):
        self._data = {}

    def column(self, field: str) -> Iterator[Tuple[UUID, str, Any]]:
        for unique_id, item in self._data.items():
            if hasattr(item, field):
                yield (unique_id, field, getattr(item, field))

    def row(self, unique_id: UUID) -> Iterator[Tuple[UUID, str, Any]]:
        if unique_id in self._data:
            for field, value in iter_attributes(self._data[unique_id]):
                yield (unique_id, field, value)

    def add(self, item: Any, unique_id: Optional[UUID] = None):
        if not unique_id:
            unique_id = uuid4()
        self._data[unique_id] = item

    def discard(self, unique_id: UUID):
        self._data.pop(unique_id, None)
