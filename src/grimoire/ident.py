from __future__ import annotations

import re
from typing import (
    Final,
    NewType,
)

VALID_IDENT: Final[re.Pattern] = re.compile(r"^[a-z_][a-z0-9_]*$")

Identifier: type[str] = NewType("Identifier", str)

def ident(name: str | Identifier) -> Identifier:
    """Validate and return a safe SQL identifier."""
    cleaned = name.strip().casefold()
    if not VALID_IDENT.match(cleaned):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return Identifier(cleaned)
