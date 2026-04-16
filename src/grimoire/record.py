from __future__ import annotations

from enum import StrEnum
import re
import sqlite3 as sql
from pathlib import Path
from typing import get_type_hints, get_origin, get_args

sql.register_adapter(bool, lambda v: int(v))
sql.register_converter("BOOLEAN", lambda v: bool(int(v)))
sql.register_adapter(datetime, lambda v: v.isoformat())
sql.register_converter("DATETIME", lambda v: datetime.fromisoformat(v.decode()))
sql.register_adapter(UUID, str)
sql.register_converter("UUID", UUID)

def _path(p: str | Path) -> Path:
    return Path(p).resolve()

class DatabaseController:
    def __init__(self, path: str | Path) -> None:
        self.con: sql.Connection = sql.connect(
            _path(path),
            detect_types=sql.PARSE_DECLTYPES,
            autocommit=False,
        )
        self.con.row_factory = sql.Row
        self.con.execute("PRAGMA foreign_keys = ON")
