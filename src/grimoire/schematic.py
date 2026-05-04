from enum import Enum
from typing import Final, Any
from collections.abc import MutableMapping, Mapping, Iterable, Iterator
import types
from .typenode import TypeNode
from .data import construct_typeddict


class MissingType(Enum):
    MISSING = object()

MISSING: Final[MissingType] = MissingType.MISSING


class Field:
    def __init__(
        self,
        annotation: Any,
        default: Any = MISSING,
        default_factory: Callable[[], Any] | MissingType = MISSING
    ) -> None:
        self.annotation: Any = annotation
        self.type: TypeNode = TypeNode(annotation)
        self.default: Any = default
        self.default_factory: Callable[[], Any] | MissingType = default_factory

    @property
    def required(self) -> bool:
        return self.type.is_required

    @property
    def not_required(self) -> bool:
        return self.type.is_not_required

    @property
    def optional(self) -> bool:
        return self.type.is_optional

    @property
    def readonly(self) -> bool:
        return self.type.is_readonly

    @property
    def has_default(self) -> bool:
        return self.default is not MISSING

    @property
    def has_default_factory(self) -> bool:
        return self.default_factory is not MISSING


class Schematic:
    def __init__(
        self,
        name: str,
        module: str,
        total: bool,
        fields: dict[str, Field],
    ) -> None:
        self.name: str = name
        self.module: str = module
        self.total: bool = total
        self.fields: dict[str, Field] = fields
        self.defaults: dict[str, Any] = {}
        self.default_factories: dict[str, Callable[[], Any]] = {}

        required: set[str] = set()
        optional: set[str] = set()
        readonly: set[str] = set()

        for field_name, field in self.fields.items():
            if field.has_default:
                self.defaults[field_name] = field.default
            elif field.has_default_factory:
                self.defaults[field_name] = field.default_factory

            if field.required or (total is True and not field.not_required):
                required.add(field_name)
            if field.optional:
                optional.add(field_name)
            if field.readonly:
                readonly.add(field_name)

        self.spec: type[dict[str, Any]] = (
            construct_typeddict(
                name=f"{self.name}Spec",
                module=self.module,
                annotation={f_name: f.type.annotation for f_name, f in self.fields.items()},
                total=self.total,
                required_keys=required,
                optional_keys=optional,
                readonly_keys=readonly,
            )
        )

    @property
    def annotations(self) -> dict[str, Any]:
        return self.spec.__annotations__

    @property
    def required(self) -> frozenset[str]:
        return self.spec.__required_keys__

    @property
    def optional(self) -> frozenset[str]:
        return self.spec.__optional_keys__

    @property
    def readonly(self) -> frozenset[str]:
        return self.spec.__readonly_keys__
