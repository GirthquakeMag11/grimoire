"""String utilities with performance caching for expensive operations."""

from __future__ import annotations

import re
import unicodedata
from collections import UserString
from typing import Literal


class UtilityString(UserString):
    def compile(self) -> re.Pattern[str]:
        """Compile this string as a regex pattern, memoizing the result.

        Useful when the same pattern will be used multiple times - the
        compiled Pattern object is cached after the first call.
        """
        if not hasattr(self, "_compiled"):
            self._compiled: re.Pattern[str] = re.compile(self.data)
        return self._compiled

    def normalize(
        self, form: Literal["NFC", "NFD", "NFKC", "NFKD"] = "NFC"
    ) -> UtilityString:
        """Return a Unicode-normalized version, caching results per normalization form.

        Each normalization form (NFC, NFD, NFKC, NFKD) is cached independently,
        so repeated calls with the same form are instant.
        """
        attr_name = f"_normal_{form}"
        if not hasattr(self, attr_name):
            normalized = unicodedata.normalize(form, self.data)
            setattr(self, attr_name, UtilityString(normalized))
        return getattr(self, attr_name)

    def surroundedwith(self, front: str, back: str | None = None) -> bool:
        """Check if string starts with front and ends with back.

        If back is None, uses front for both checks (e.g., checking if a string
        is wrapped in asterisks: "*text*").
        """
        return self.startswith(front) and self.endswith(
            back if back is not None else front
        )

    def __repr__(self) -> str:
        """Return unambiguous string representation for debugging."""
        return f"{self.__class__.__name__}({self.data!r})"
