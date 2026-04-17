from __future__ import annotations

from datetime import datetime
from uuid import UUID, uui4
from dataclasses import (
    dataclass,
    field,
    fields as dc_fields,
    Field,
    is_dataclass,
    make_dataclass
)

from functools import (
    cached_property
)

from typing import (
    overload,
    Callable,
    dataclass_transform,
    Annotated,
    Any,
)


@dataclass
class TypeNode:
    _raw: Any

    def __hash__(self) -> int:
        return hash(self._id)

    @cached_property
    def is_annotated(self) -> bool:
        return get_origin(self._raw) is Annotated

    @cached_property
    def is_generic(self) -> bool:
        return self.origin is not None and not self.is_literal and not self.is_union

    @cached_property
    def is_class(self) -> bool:
        return inspect.isclass(self.origin)

    @cached_property
    def is_primitive_class(self) -> bool:
        return bool(self.is_class and isinstance(self.origin, (bool, str, int, float, bytes, datetime, UUID)))

    @cached_property
    def is_data_class(self) -> bool:
        return bool(self.is_class and is_dataclass(self.origin))

    @cached_property
    def is_table_class(self) -> booL:
        return bool(self.is_data_class and hasattr(self.origin, "__table_spec__"))

    @cached_property
    def is_literal(self) -> bool:
        return self.origin is Literal

    @cached_property
    def is_optional(self) -> bool:
        return self.is_union and type(None) in self.union_values

    @cached_property
    def is_union(self) -> bool:
        return self.origin is typing.Union or self.origin is types.UnionType

    @cached_property
    def annotated_extras(self) -> tuple[Any, ...]:
        if self.is_annotated:
            return get_args(self._raw)[1:]
        return ()

    @cached_property
    def inner_type(self) -> Any:
        if self.is_annotated:
            return get_args(self._raw)[0]
        return self._raw

    @cached_property
    def origin(self) -> Any | None:
        return get_origin(self.inner_type)

    @cached_property
    def literal_values(self) -> tuple[Any, ...]:
        if self.is_literal:
            return get_args(self.inner_type)
        return ()

    @cached_property
    def union_values(self) -> tuple[Any, ...]:
        if self.is_union:
            return get_args(self.inner_type)
        return ()

    @cached_property
    def union_members(self) -> tuple[TypeNode, ...]:
        return (TypeNode(a) for a in self.union_values)

    @cached_property
    def children(self) -> tuple[TypeNode, ...]:
        if self.is_literal:
            return ()
        return tuple(TypeNode(a) for a in get_args(self.inner_type))

    @cached_property
    def index(self) -> list[TypeNode]:
        base = [self]
        if self.is_union:
            for node in self.union_members:
                base.extend(node.index)

        for child in self.children:
            base.extend(child.index)

        return base

    @cached_property
    def is_leaf(self) -> bool:
        return bool(len(self.children) == 0)

    @property
    def raw(self) -> Any:
        return self._raw

    @cached_property
    def primitive_sql_type(self) -> str | None:
        if self.is_primitive_class:
            return {
                bool: "BOOLEAN",
                str: "TEXT",
                int: "INTEGER",
                float: "REAL",
                bytes: "BLOB",
                datetime: "DATETIME",
                UUID: "UUID",
            }[self.origin]

@dataclass
class FieldNode:
    name: str
    _raw: Any
    _field: Field

    def __getitem__(self, index: int) -> TypeNode:
        return self.type.index[index]

    def __len__(self) -> int:
        return len(self.type.index)

    def __iter__(self) -> Iterator[TypeNode]:
        return iter(self.type.index)

    @cached_property
    def params(self) -> FieldParams:
        data: FieldParams = FieldParams(
            name=self.name,
            type=self.type._raw,
            init=self.init,
            repr=self.repr,
            hash=self.hash,
            compare=self.compare,
            kw_only=self.kw_only,
            doc=self.doc,
            metadata=self.metadata,
        )
        if self.has_default:
            data["default"] = self.default
        elif self.has_default_factory:
            data["default_factory"] = self.default_factory
        return data

    @cached_property
    def field_array_entry(self) -> tuple[str, Any, Field]:
        return (self.name, self.type.raw, field(**self.params))

    @cached_property
    def default(self) -> Any:
        if self._field.default is MISSING:
            raise AttributeError(f"Field {self._name} does not have a default value")
        return self._field.default

    @cached_property
    def has_default(self) -> bool:
        return self._field.default is not MISSING

    @cached_property
    def default_factory(self) -> Callable[[], Any]:
        if self._field.default_factory is MISSING:
            raise AttributeError(f"Field {self._name} does not have a default value factory")
        return self._field.default_factory

    @cached_property
    def has_default_factory(self) -> bool:
        return self._field.default_factory is not MISSING

    @cached_property
    def init(self) -> bool:
        return self._field.init

    @cached_property
    def repr(self) -> bool:
        return self._field.repr

    @cached_property
    def compare(self) -> bool:
        return self._field.compare

    @cached_property
    def hash(self) -> bool:
        if self._field.hash is None:
            return self.compare
        return self.field.hash

    @cached_property
    def kw_only(self) -> bool:
        return self._field.kw_only

    @cached_property
    def metadata(self) -> dict[Any, Any]:
        return dict(self._field.metadata)

    @cached_property
    def type(self) -> TypeNode:
        return TypeNode(self._raw)


@dataclass
class ClassNode[T]:
    target: type[T]
    globalns: dict[str, Any] | None = None

    def __getitem__(self, name: str) -> FieldNode:
        try:
            return self.field_entries[name]
        except KeyError:
            raise KeyError(f"{self.target.__name__!r} has no field {name!r}") from None

    def __len__(self) -> int:
        return len(self.field_entries)

    def __iter__(self) -> Iterator[tuple[str, FieldNode]]:
        return iter(self.field_entries.items())

    @cached_property
    def resolved_hints(self) -> dict[str, Any]:
        return get_type_hints(self.target, globalns=self.globalns, include_extras=True)

    @cached_property
    def field_entries(self) -> dict[str, FieldNode]:
        res = {}
        for f in dc_fields(self.target):
            res[f.name] = FieldNode(
                name=f.name,
                _raw=self.resolved_hints[f.name],
                _field=f,
            )
        return res


@dataclass
class JunctionTable[A, B]:
    ...


@dataclass
class ModelTable[T]:
    ...


@dataclass
class ColumnSpec:
    node: FieldNode

    @cached_property
    def primary_key(self) -> bool:
        return self.node.metadata.get("PRIMARY_KEY", False)

    @cached_property
    def autoincrement(self) -> bool:
        return self.node.metadata.get("AUTOINCREMENT", False)

    @cached_property
    def not_null(self) -> bool:
        return self.node.metadata.get("NOT_NULL", False)

    @cached_property
    def unique_values(self) -> bool:
        return self.node.metadata.get("UNIQUE_VALUES", False)


@dataclass
class TableSpec[T]:
    node: ClassNode[T]

    @staticmethod
    def create_table(name: str) -> str:
        return f"CREATE TABLE {ident(name)}" + "({table_params})"

    @staticmethod
    def create_table_if_not_exists(name: str) -> str:
        return f"CREATE TABLE IF NOT EXISTS {ident(name)}" + "({table_params})"

    @staticmethod
    def create_and_attach(dataclass: type) -> None:
        table_spec = TableSpec(node=ClassNode(target=dataclass))
        setattr(dataclass, "__table_spec__", table_spec)
        return dataclass

@overload
def tableclass[T](cls: type[T], /) -> type[T]: ...

@overload
def tableclass[T](
    *,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = False,
    match_args: bool = True,
    kw_only: bool = False,
    slots: bool = False,
    weakref_slot: bool = False,
) -> Callable[[type[T]], type[T]]: ...

@dataclass_transform(field_specifiers=(field, Field))
def tableclass[T](
    cls: type[T] | None = None,
    /,
    *,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = False,
    match_args: bool = True,
    kw_only: bool = False,
    slots: bool = False,
    weakref_slot: bool = False,
) -> type[T] | Callable[[type[T]], type[T]]:

    def wrap(cls: type[T]) -> type[T]:
        new: type = (
            dataclass(
                cls,
                init=init,
                repr=repr,
                eq=eq,
                order=order,
                unsafe_hash=unsafe_hash,
                frozen=frozen,
                match_args=match_args,
                kw_only=kw_only,
                slots=slots,
                weakref_slot=weakref_slot
        ))
        return TableSpec.create_and_attach(new)

    if cls is not None:
        return wrap(cls)
    return wrap
