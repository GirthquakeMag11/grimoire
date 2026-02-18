from __future__ import annotations

from collections import UserDict
from typing import ClassVar, Hashable, Callable, Any, TypeAlias

Factory: TypeAlias = Callable[[None], Any]

class factorydict(UserDict):
    def __init__(self, default_factory: Factory | None = None, *, **key_factories: Factory):
        super().__init__()
        self._default_factory = default_factory
        self._key_factories = dict(key_factories)

    def __getitem__(self, key: Hashable) -> Any:
        if key not in self.data:
            if key in self._key_factories:
                self.data[key] = self._key_factories[key]()
            elif self._default_factory is not None:
                self.data[key] = self._default_factory()
        return self.data[key]

