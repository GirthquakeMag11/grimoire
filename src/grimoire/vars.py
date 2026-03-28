from __future__ import annotations

import threading


class TypeErr(TypeError):
    def __init__(self, expected: type, val: object) -> None:
        super().__init__(f"Expected type '{expected.__name__}', got type '{type(val).__name__}'")


class TextVar:
    __slots__ = ("_value", "_read_only", "_lock")

    def __init__(self, value: str = "", read_only: bool = False) -> None:
        self._value: str = value
        self._read_only: bool = read_only
        self._lock: threading.RLock = threading.RLock()

    def set(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeErr(str, value)
        if self._read_only is True:
            raise AttributeError(f"TextVar {id(self)} is ready only")
        with self._lock:
            self._value = value

    def clear(self) -> None:
        if self._read_only is True:
            raise AttributeError(f"TextVar {id(self)} is ready only")
        with self._lock:
            self._value = ""

    def get(self) -> str:
        with self._lock:
            return self._value

    def length(self) -> int:
        with self._lock:
            return len(self._value)

    def chars(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._value) if len(self._value) > 0 else ()

    def lines(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._value.splitlines()) if len(self._value) > 0 else ()

    def __hash__(self) -> int:
        return hash(self._value)
