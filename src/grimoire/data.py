from __future__ import annotations

import inspect
import re
import sqlite3 as sql
import types
import typing
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from functools import cached_property
from pathlib import Path
from uuid import UUID
from dataclasses import (
    MISSING,
    Field,
    dataclass,
    fields as dc_fields,
    is_dataclass,
    field,
)
from typing import (
    Annotated,
    Any,
    Final,
    Literal,
    NewType,
    get_args,
    get_origin,
    get_type_hints,
    TypedDict,
    Required,
    NotRequired,
    overload,
    dataclass_transform,
)

sql.register_adapter(bool, lambda v: int(v))
sql.register_converter("BOOLEAN", lambda v: bool(int(v)))
sql.register_adapter(datetime, lambda v: v.isoformat())
sql.register_converter("DATETIME", lambda v: datetime.fromisoformat(v.decode()))
sql.register_adapter(UUID, str)
sql.register_converter("UUID", UUID)

VALID_IDENT: Final[re.Pattern] = re.compile(r"^[a-z_][a-z0-9_]*$")

Identifier: type[str] = NewType("Identifier", str)

type Primitive = bool | str | int | float | bytes | datetime | UUID


def _path(p: str | Path) -> Path:
    return Path(p).resolve()


def utcnow() -> datetime:
    return datetime.now(UTC)


def ident(name: str | Identifier) -> Identifier:
    """Validate and return a safe SQL identifier."""
    cleaned = name.strip().casefold()
    if not VALID_IDENT.match(cleaned):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return Identifier(cleaned)


def compose_signature(obj: Callable[[...], ...]) -> dict[str, Any]:
    signature: dict[str, Any] = {}
    hints: dict[str, Any] = get_type_hints(obj)

    if "return" in hints:
        signature["return"] = hints["return"]

    for idx, (keyword, param) in enumerate(inspect.signature(obj).parameters.items()):
        parameter = {}

        if param.kind is inspect.Parameter.VAR_KEYWORD:
            parameter["unpack"] = dict

        if param.kind is inspect.Parameter.VAR_POSITIONAL:
            parameter["unpack"] = tuple

        if param.kind in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
            parameter["position"] = None

        if param.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.VAR_POSITIONAL,
        ):
            parameter["position"] = idx

        if param.default is not inspect.Parameter.empty:
            parameter["default"] = param.default

        if keyword in hints:
            parameter["annotation"] = hints.get(keyword)

        if parameter:
            signature.setdefault("parameters", {})[keyword] = parameter

    return signature


def decompose_attrs(
    obj: Any, *, _cache: dict[int, dict[str, Any]] | None = None, _parent: Any | None = None
) -> dict[str, Any]:
    if _cache is None:
        _cache = {}

    obj_id = id(obj)

    if obj_id in _cache:
        return _cache[obj_id]

    obj_class = type(obj)
    result: dict[str, Any] = {"class": obj_class}
    _cache[obj_id] = result

    if obj is None or isinstance(obj, (bool, int, float, str, bytes)):
        result["value"] = obj
        return result

    if isinstance(obj, (list, tuple, set, frozenset)):
        result["data"] = [decompose_attrs(item, _cache=_cache, _parent=obj) for item in obj]
        return result

    if isinstance(obj, dict):
        result["data"] = {
            str(k): decompose_attrs(v, _cache=_cache, _parent=obj) for k, v in obj.items()
        }
        return result

    if callable(obj):
        result["signature"] = compose_signature(obj)

        if obj_class.__name__ == "builtin_function_or_method":
            result["class"] = "builtin_method" if _parent is not None else "builtin_function"
            return result

    attributes = {}
    for name, value in iter_attributes(obj):
        try:
            attributes[name] = decompose_attrs(value, _cache=_cache, _parent=obj)
        except Exception as e:
            attributes[name] = {"class": type(e).__name__, "value": str(e)}

    if attributes:
        result["attributes"] = attributes
    return result


def iter_fields(obj: Any) -> Iterator[str]:
    """Yield unique public field names discoverable from an object and its MRO.

    Names are collected from the instance dict first, then each class in the
    MRO via descriptors, annotations, slots, and remaining class dict keys,
    with duplicates removed.

    Respects encapsulation and avoids private namespaces.
    """
    seen: set[str] = set()

    def _is_public(name: str) -> bool:
        return not name.startswith("_")

    def _yield_new_public(*names: str) -> Iterator[str]:
        for name in names:
            if _is_public(name) and name not in seen:
                seen.add(name)
                yield name

    def _is_valid_descriptor(value: Any) -> bool:
        if isinstance(value, property):
            return not getattr(value, "__isabstractmethod__", False)
        has_get = callable(getattr(value, "__get__", None))
        has_set_del = callable(getattr(value, "__set__", None)) or callable(
            getattr(value, "__delete__", None)
        )
        return has_get and has_set_del

    def _from_dict(o: Any) -> Iterator[str]:
        yield from _yield_new_public(*getattr(o, "__dict__", {}).keys())

    def _from_class(cls: type) -> Iterator[str]:
        cls_vars = dict(vars(cls))
        yield from _yield_new_public(*(n for n, v in cls_vars.items() if _is_valid_descriptor(v)))
        yield from _yield_new_public(*getattr(cls, "__annotations__", {}))
        slots = getattr(cls, "__slots__", ())
        yield from _yield_new_public(*((slots,) if isinstance(slots, str) else slots))
        yield from _yield_new_public(*cls_vars)

    yield from _from_dict(obj)
    for cls in obj.__class__.__mro__:
        yield from _from_class(cls)


def iter_attributes(obj: Any) -> Iterator[tuple[str, Any]]:
    """Yield (name, value) pairs for public fields that can be read via getattr.

    Skips the "mro" attribute on type objects and ignores fields that raise
    AttributeError when accessed.
    """
    for field_name in iter_fields(obj):
        if field_name == "mro" and isinstance(obj, type):
            continue
        try:
            yield (field_name, getattr(obj, field_name))
        except AttributeError:
            continue


def copy_namespace(obj: Any) -> dict[str, Any]:
    return dict(iter_attributes(obj))


class DataClassParams(TypedDict, total=True):
    cls_name: str
    fields: list[tuple[str, Any, Field[Any]]]
    bases: tuple[type, ...]
    namespace: dict[str, Any]
    init: bool
    repr: bool
    eq: bool
    order: bool
    unsafe_hash: bool
    frozen: bool
    match_args: bool
    kw_only: bool
    slots: bool
    weakref_slot: bool
    module: str | None
    decorator: Callable[..., type]


class FieldParams(TypedDict, total=False):
    name: str
    type: Any
    default: Any
    default_factory: Callable[[], Any]
    init: bool
    repr: bool
    hash: bool | None
    compare: bool
    kw_only: bool
    doc: str
    metadata: dict[Any, Any]


@dataclass
class Adapter[T]:
    """Dependency injection class for custom datatype sqlite3 adapters."""
    type: type[T]
    operator: Callable[[T], ...]
    registered: bool = False

    def register(self) -> None:
        if not self.registered:
            sql.register_adapter(self.type, self.operator)
            self.registered = True

@dataclass
class Converter[T]:
    """Dependency injection class for custom datatype sqlite3 converters."""
    type: str
    operator: Callable[[bytes], [T]]
    registered: bool = False

    def register(self) -> None:
        if not self.registered:
            sql.register_conveter(ident(self.type.strip().upper()), self.operator)
            self.registered = True


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
    def is_literal(self) -> bool:
        return self.origin is Literal

    @cached_property
    def is_optional(self) -> bool:
        return self.is_union and type(None) in self.union_args

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
        base = []
        if self.is_union:
            for node in self.union_members:
                base.extend(node.index)

        else:
            base.append(self)

        for child in self.children:
            base.extend(child.index)

        return base

    @property
    def raw(self) -> Any:
        return self._raw


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
class DataClassNode[T]:
    target: T | type[T]
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
    def dataclass(self) -> type[T]:
        if is_dataclass(self.target):
            if isinstance(self.target, type):
                return self.target
            return type(self.target)
        raise TypeError(self.target)

    @cached_property
    def field_entries(self) -> dict[str, FieldNode]:
        res = {}
        for f in dc_fields(self.dataclass):
            res[f.name] = FieldNode(
                name=f.name,
                _raw=self.resolved_hints[f.name],
                _field=f,
            )
        return res

    @cached_property
    def params(self) -> DataClassParams:
        dc_params = self.dataclass.__dataclass_params__
        return DataClassParams(
            cls_name=self.dataclass.__name__,
            fields=[f.field_array_entry for f in self.field_entries.values()],
            bases=tuple(b for b in self.dataclass.__bases__ if b is not object),
            namespace=copy_namespace(self.dataclass),
            init=dc_params.init,
            repr=dc_params.repr,
            eq=dc_params.eq,
            order=dc_params.order,
            unsafe_hash=dc_params.unsafe_hash,
            frozen=dc_params.frozen,
            match_args=getattr(dc_params, 'match_args', True),
            kw_only=getattr(dc_params, 'kw_only', False),
            slots=bool('__slots__' in self.dataclass.__dict__),
            weakref_slot=getattr(dc_params, 'weakref_slot', False),
            module=self.dataclass.__module__,
            decorator=dataclass,
        )

    def construct_dataclass(self) -> type:
        p = self.params
        return make_dataclass(
            cls_name=p['name'],
            fields=p['fields'],
            bases=p['bases'],
            namespace=p['namespace'],
            init=p['init'],
            repr=p['repr'],
            eq=p['eq'],
            order=p['order'],
            unsafe_hash=p['unsafe_hash'],
            frozen=p['frozen'],
            match_args=p['match_args'],
            kw_only=p['kw_only'],
            slots=p['slots'],
            weakref_slot=p['weakref_slot'],
            module=p['module'],
            decorator=p['decorator'],
        )

class DataBase:
    def __init__(self, path: str | Path) -> None:
        self.con: sql.Connection = sql.connect(
            _path(path),
            detect_types=sql.PARSE_DECLTYPES,
            autocommit=False,
        )
        self.con.row_factory = sql.Row
        self.con.execute("PRAGMA foreign_keys = ON")
        self.dc_nodes: dict[str, type] = {}

    def ensure_dc_node(self, dataclass: type, table: str) -> None:
        self.dc_nodes[table] = DataClassNode(dataclass)

    @overload
    def tableclass[T](self, cls: type[T], /, table: str) -> type[T]: ...

    @overload
    def tableclass[T](
        self,
        table: str,
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
        self,
        cls: type[T] | None = None,
        /,
        table: str,
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

        def ensure(final_cls) -> None:
            self.ensure_dc_node(final_cls, table)

        if hasattr(cls, "__dataclass_fields__"):
            ensure(cls)
            return cls

        def wrap(cls: type[T]) -> type[T]:
            cls = dataclass(
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
                weakref_slot=weakref_slot,
            )
            ensure(cls)
            return cls

        if cls is not None:
            return wrap(cls)
        return wrap
