from __future__ import annotations

import re
import unicodedata
from collections import UserString
from typing import Any, Literal, Optional


def normalstr(data: Any | str) -> str:
    return unicodedata.normalize("NFC", str(data))


class UtilityString(UserString):
    def compile(self) -> re.Pattern:
        if hasattr(self, "_compiled"):
            self._compiled: re.Pattern = re.compile(self.data)
        return self._compiled

    def normalize(
        self, form: Literal["NFC", "NFD", "NFKC", "NFKD"] = "NFC"
    ) -> UtilityString:
        f_attr = f"_normal_{form}"
        if not hasattr(self, f_attr):
            setattr(self, f_attr, unicodedata.normalize(form, self.data))
        return getattr(self, f_attr)

    def surroundedwith(self, front: str, back: Optional[str] = None) -> bool:
        return self.startswith(front) and self.endswith(
            back if back is not None else front
        )
