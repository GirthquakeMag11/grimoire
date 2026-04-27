from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any, Final

IDENT_ESCAPES: Final[dict[int, str]] = str.maketrans({'"': '""', "\x00": ""})


class SQL(StrEnum):
    INSERT_INTO = "INSERT INTO {table} {keys} VALUES {placeholders}"
    REPLACE_INTO = "REPLACE INTO {table} {keys} VALUES {placeholders}"
    IGNORE_INTO = "INSERT OR IGNORE INTO {table} {keys} VALUES {placeholders}"
    DELETE_FROM_WHERE = "DELETE FROM {table} WHERE {keys} = {placeholders}"
    SELECT_FROM_WHERE = "SELECT * FROM {table} WHERE {keys} = {placeholders}"

    @staticmethod
    def ident_escape(name: str) -> str:
        return '"' + name.translate(IDENT_ESCAPES) + '"'

    def compose(self, table: str, key_values: Mapping[str, Any]) -> tuple[str, tuple[Any, ...]]:
        table: str = self.ident_escape(table)
        args: tuple[tuple[str, Any], ...] = tuple(key_values.items())
        keys: str = (
            f"({', '.join(self.ident_escape(arg[0]) for arg in args)})"
            if len(args) > 1
            else self.ident_escape(args[0])
        )
        placeholders: str = f"({', '.join('?' for _ in args)})" if len(args) > 1 else "?"
        values: tuple[Any, ...] = tuple(arg[1] for arg in args)
        return (self.format(table=table, keys=keys, placeholders=placeholders), values)
