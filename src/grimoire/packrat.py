from __future__ import annotations

from pathlib import Path
import shutil
import hashlib
from typing import NamedTuple

class CanonPath(NamedTuple):
    string: str
    path: Path

def canon_path(path: str | Path) -> CanonPath:
    p = Path(path).resolve()
    return (str(p), p)

def copy_file(source_filepath: str | Path, destination_filepath: str | Path) -> None:
    src = canon_path(source_filepath)
    if not src.path.exists():
        return
    dest = canon_path(destination_filepath)
    ...
