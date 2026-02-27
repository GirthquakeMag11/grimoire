from __future__ import annotations

import re
from collections.abc import (
    Iterator,
)
from enum import Enum
from typing import (
    Callable,
    Self,
)


class ReEnum(Enum):
    """Enum whose values are compiled regular expression patterns."""

    def __new__(cls, pattern: str) -> Self:
        compiled: re.Pattern[str] = re.compile(pattern)
        obj = object.__new__(cls)
        obj._value_ = compiled
        return obj

    def match(self, value: str) -> re.Match | None:
        """Match the pattern at the start of the string."""
        return self.value.match(value)

    def search(self, value: str, start: int = 0) -> re.Match | None:
        """Search the string for the first occurrence of the pattern."""
        return self.value.search(value, start)

    def fullmatch(self, value: str) -> re.Match | None:
        """Match the pattern against the entire string."""
        return self.value.fullmatch(value)

    def finditer(self, value: str) -> Iterator[re.Match]:
        """Yield match objects for all non-overlapping matches."""
        yield from self.value.finditer(value)

    def sub(self, value: str, repl: str | Callable[[re.Match[str]], str], count: int = 0) -> str:
        """Replace matches in the string and return the result."""
        return self.value.sub(repl=repl, string=value, count=count)

    def findall(self, value: str) -> list[str] | list[tuple[str, ...]]:
        """Return all non-overlapping matches in the string."""
        return self.value.findall(value)

    @property
    def groups(self) -> int:
        """Number of capturing groups in the pattern."""
        return self.value.groups

    @property
    def group_index(self) -> dict[str, int]:
        """Mapping of named group names to group numbers."""
        return self.value.groupindex

    @property
    def pattern(self) -> str:
        """The original pattern string."""
        return self.value.pattern

    @staticmethod
    def escape(value: str) -> str:
        """Escape special regex characters in a string."""
        return re.escape(value)
