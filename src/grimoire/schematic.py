from enum import Enum
from typing import Final

class MissingType(Enum):
    MISSING = object()

MISSING: Final[MissingType] = MissingType.MISSING

class Field:
    def __init__(
        self,
        type: Any,

        default: Any = MISSING,
        default_factory: Callable[[], Any] | MissingType = MISSING,
        compare: bool | MissingType = MISSING,
        equate: bool | MissingType = MISSING,
        hashed: bool | MissingType = MISSING,

        required: bool | MissingType = MISSING,
        optional: bool | MissingType = MISSING,
        readonly: bool | MissingType = MISSING,

        **extra_data: Any,
    ) -> None:
        self.type: Any = type
        self.default: Any = default

        self.default: Any = default
        self.default_factory: Callable[[], Any] | MissingType = default_factory
        self.compare: bool | MissingType = compare
        self.equate: bool | MissingType = equate
        self.hashed: bool | MissingType = hashed

        self.required: bool | MissingType = required
        self.optional: bool | MissingType = optional
        self.readonly: bool | MissingType = readonly

        self.extra_data: dict[str, Any] = dict(extra_data)
