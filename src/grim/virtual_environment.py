from __future__ import annotations

import configparser
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple


class VenvReport(NamedTuple):
    """
    - confident: False means the file structure looks wrong or uncertain —
                    prompt the user to wipe and reinstall

    - executable_ok: False means the files look fine but the Python won't run —
                        should also prompt a wipe

    - missing_packages: packages that need to be installed regardless
    """

    confident: bool
    executable_ok: bool
    missing_packages: set[str]


def _get_python_executable(venv_path: Path) -> Path:
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def check_venv_files(venv_path: Path) -> bool:
    venv_path = Path(venv_path).resolve()
    cfg_path = venv_path / "pyvenv.cfg"

    if not cfg_path.is_file() or not _get_python_executable(venv_path).is_file():
        return False

    try:
        contents = "[venv]\n" + cfg_path.read_text()
        config = configparser.ConfigParser()
        config.read_string(contents)
        return "home" in config["venv"] and "version" in config["venv"]
    except Exception:
        return False


def check_venv_executable(venv_path: Path) -> bool:
    try:
        subprocess.run(
            [
                str(_get_python_executable(Path(venv_path).resolve())),
                "-c",
                "import sys",
            ],
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_venv_packages(venv_path: Path, *packages: str) -> set[str]:
    if not packages:
        return set()

    try:
        result = subprocess.run(
            [
                _get_python_executable(Path(venv_path).resolve()),
                "-m",
                "pip",
                "show",
                *packages,
            ],
            capture_output=True,
            text=True,
        )
        found = {
            line.split(":", 1)[1].strip().lower()
            for line in result.stdout.splitlines()
            if line.startswith("Name:")
        }
        return {pkg for pkg in packages if pkg.lower() not in found}
    except FileNotFoundError:
        return set(packages)


def validate_venv(venv_path: Path, *required_packages: str) -> VenvReport:
    venv_path = Path(venv_path).resolve()
    if not check_venv_files(venv_path):
        return VenvReport(False, False, set(required_packages))
    if not check_venv_executable(venv_path):
        return VenvReport(True, False, set(required_packages))

    missing_packages = check_venv_packages(venv_path, *required_packages)
    return VenvReport(True, True, missing_packages)
