from __future__ import annotations

import importlib.util
import types
from pathlib import Path
from typing import Optional, TypeAlias, Union

Module: TypeAlias = types.ModuleType


def import_module_from_path(
    module_path: Union[str, Path], module_name: Optional[str] = None
) -> Module:
    module_path = Path(module_path).resolve()
    if not module_name:
        module_name = str(module_path.name)
    if module_path.is_file():
        spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    elif module_path.is_dir():
        init_file = module_path / "__init__.py"
        if not init_file.is_file():
            raise FileNotFoundError(
                f"Directory '{module_path}' is not a valid package (missing __init__.py)"
            )
        spec = importlib.util.spec_from_file_location(
            module_name, str(init_file), submodule_search_locations=[str(module_path)]
        )
    else:
        raise FileNotFoundError(f"No such file or directory: {module_path!s}")

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not create import spec for {module_name!r} at {module_path!s}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
