from __future__ import annotations

from pathlib import Path
import hashlib
import shutil

def ensure_path(path: str | Path) -> Path:
    """Coerce 'path' into Path instance and resolve it."""
    return Path(path).resolve(strict=False)

def ensure_path_string(path: str | Path) -> str:
    """Resolve 'path' then ensure it is a string."""
    return str(ensure_path(path))

def path_exists(path: str | Path) -> bool:
    try:
        Path(path).resolve(strict=True)
        return True
    except FileNotFoundError:
        return False

def path_is_file(path: str | Path) -> bool:
    try:
        return Path(path).resolve(strict=True).is_file()
    except FileNotFoundError:
        return False

def path_is_dir(path: str | Path) -> bool:
    try:
        return Path(path).resolve(strict=True).is_dir()
    except FileNotFoundError:
        return False
