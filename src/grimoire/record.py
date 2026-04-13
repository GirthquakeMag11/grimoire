from __future__ import annotations

from types import SimpleNamespace
from typing import Any
import inspect
from .inspection import tree_attrs


class Record:
    def __init__(self, obj: Any, loose_types: bool = False) -> None:
        self.id: int = id(obj)
        self.type: type = type(obj)
        self.data: dict[str, Any] = tree_attrs(obj, loose_types=loose_types)

    def __str__(self) -> str:
        lines: list[str] = []
        for k, v in self.data.items():
            lines.append(f"{k!s}=({str(v) if not inspect.isclass(v) else (f"{v.__module__}.{v.__name__}")})")
        return "\n".join(lines)

    def __repr__(self) -> str:
        head: str = f"RECORD(id={self.id!s}, class={self.type.__module__}.{self.type.__name__})"
        lines: list[str] = [
            head,
            f"{"-":-^{len(head)}}",
            str(self)
        ]
        return "\n".join(lines)
