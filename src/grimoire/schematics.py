from __future__ import annotations

from collections.abc import (
    Callable,
)
from typing import (
    Any,
    ClassVar,
    Final,
    Required,
    NotRequired,
    TypedDict,
    Unpack,
)
from enum import Enum


class MissingType(Enum):
    MISSING = object()

MISSING: Final[MissingType] = MissingType.MISSING

class Field:
    required: bool = True
    optional: bool = False
    default: Any = MISSING
    default_factory: Callable[[], Any] = MISSING


class SchematicParameters(TypedDict, total=False):
    total: bool
    """a boolean indicated whether all items are required by default or not"""
    closed: bool
    """a boolean indicating whether any attributes beyond those specified may
    be assigned to an entity"""


def schematic[T](cls: type[T], **params: Unpack[SchematicParameters]) -> type[T]:
    

# --- Example for drafting ---


@schematic(total=True, closed=True)
class ExampleSchema:
    name:
