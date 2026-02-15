from __future__ import annotations

import re
import unicodedata
from collections import UserString
from dataclasses import dataclass, field, InitVar
from typing import Any, Optional, Sequence, Protocol

def surroundedwith(string: str, start: str, end: Optional[str] = None) -> bool:
    """Return a boolean representing whether 'string' argument starts with
    'start' substring and ends with 'end' substring.

    If end is not provided, 'start' is used in its place.
    """
    return string.startswith(start) and string.endswith(
        end if end is not None else start
    )


def normalstr(data: Any | str) -> str:
    return unicodedata.normalize("NFC", str(data))


@dataclass
class PatternMatch:
    ...


class PatternString:

    def __init__(self, string: str):
        if not isinstance(string, str):
            raise TypeError(type(string).__name__)
        self._raw = string
        self._normal = None
        self._pat = None

    @property
    def raw(self) -> str:
        return self._raw

    @property
    def normal(self) -> str:
        if self._normal is None:
            self._normal = normalstr(self.raw)
        return self._normal

    @property
    def pattern(self) -> re.Pattern:
        if self._pat is None:
            self._pat = re.compile(self.normal)
        return self._pat

    @staticmethod
    def maketrans(*args, **kwargs):
        return str.maketrans(*args, **kwargs)

    def translate(self, *args, **kwargs) -> PatternString:
        return PatternString(self.raw.translate(*args, **kwargs))

    def capitalize(self) -> PatternString:
        return PatternString(self.raw.capitalize())

    def casefold(self) -> PatternString:
        return PatternString(self.raw.casefold())

    def center(self, *args, **kwargs) -> PatternString:
        return PatternString(self.raw.center(*args, **kwargs))

    def count(self, *args, **kwargs) -> int:
        self.raw.count(*args, **kwargs)

    def encode(self, *args, **kwargs) -> bytes:
        return self.raw.encode(*args, **kwargs)

    def endswith(self, *args, **kwargs) -> bool:
        return self.raw.endswith(*args, **kwargs)

    def expandtabs(self, *args, **kwargs) -> PatternString:
        return PatternString(self.raw.expandtabs(*args, **kwargs))

    def find(self, *args, **kwargs) -> int:
        return self.raw.find(*args, **kwargs)

    def format(self, *args, **kwargs) -> PatternString:
        return PatternString(self.raw.format(*args, **kwargs))

    def format_map(self, *args, **kwargs) -> PatternString:
        return PatternString(self.raw.format_map(*args, **kwargs))

    def index(self, *args, **kwargs) -> int:
        return self.raw.index(*args, **kwargs)

    def isalnum(self) -> bool:
        return self.raw.isalnum()

    def isalpha(self) -> bool:
        return self.raw.isalpha()

    def isascii(self) -> bool:
        return self.raw.isascii()

    def isdecimal(self) -> bool:
        return self.raw.isdecimal()

    def isdigit(self) -> bool:
        return self.raw.isdigit()

    def isidentifier(self) -> bool:
        return self.raw.isidentifier()

    def islower(self) -> bool:
        return self.raw.islower()

    def isnumeric(self) -> bool:
        return self.raw.isnumeric()

    def isprintable(self) -> bool:
        return self.raw.isprintable()

    def isspace(self) -> bool:
        return self.raw.isspace()

    def istitle(self) -> bool:
        return self.raw.istitle()

    def isupper(self) -> bool:
        return self.raw.isupper()

    def join(self, *args, **kwargs) -> PatternString:
        return PatternString(self.raw.join(*args, **kwargs))

    def ljust(self, *args, **kwargs) -> PatternString:
        return PatternString(self.raw.ljust(*args, **kwargs))

    def lower(self) -> PatternString:
        return PatternString(self.raw.lower())

    def lstrip(self, *args, **kwargs) -> PatternString:
        return PatternString(self.raw.lstrip())

    def partition(self, *args, **kwargs) -> tuple[PatternString]:
        return (PatternString(part) for part in self.raw.partition(*args, **kwargs))

    def removeprefix(self, *args, **kwargs) -> PatternString:
        return PatternString(self.raw.removeprefix(*args, **kwargs))

    def removesuffix(self, *args, **kwargs) -> PatternString:
        return PatternString(self.raw.removesuffix(*args, **kwargs))

    def replace(self, *args, **kwargs) -> PatternString:
        return PatternString(self.raw.removeprefix(*args, **kwargs))

    def rfind(self, *args, **kwargs) -> int:
        return self.raw.rfind(*args, **kwargs)

    def rindex(self, *args, **kwargs) -> int:
        return self.raw.rindex(*args, **kwargs)

    def rjust(self, *args, **kwargs) -> PatternString:
        return PatternString(self.raw.rjust(*args, **kwargs))

    def rpartition(self, *args, **kwargs) -> tuple[PatternString]:
        return (PatternString(part) for part in self.raw.rpartition(*args, **kwargs))

    def rsplit(self, *args, **kwargs) -> list[PatternString]:
        return [PatternString(part) for part in self.raw.rsplit(*args, **kwargs)]

    def rstrip(self, *args, **kwargs) -> PatternString:
        return PatternString(self.raw.rstrip(*args, **kwargs))

    def split(self, *args, **kwargs) -> list[PatternString]:
        return [PatternString(part) for part in self.raw.split(*args, **kwargs)]

    def splitlines(self, *args, **kwargs) -> list[PatternString]:
        return [PatternString(part) for part in self.raw.splitlines(*args, **kwargs)]

    def startswith(self, *args, **kwargs) -> bool:
        return self.raw.startswith(*args, **kwargs)

    def strip(self, *args, **kwargs) -> PatternString:
        return PatternString(self.raw.strip(*args, **kwargs))

    def swapcase(self) -> PatternString:
        return PatternString(self.raw.swapcase())

    def title(self) -> PatternString:
        return PatternString(self.raw.title())

    def upper(self) -> PatternString:
        return PatternString(self.raw.upper())

    def zfill(self, *args, **kwargs) -> PatternString:
        return PatternString(self.raw.zfill(*args, **kwargs))
