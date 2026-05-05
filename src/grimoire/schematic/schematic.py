from collections.abc import (
    Callable,
    Iterable,
    Iterator,
)
from dataclasses import (
    is_dataclass,
)
from enum import Enum
from functools import (
    cached_property,
)
from inspect import (
    getattr_static,
    isclass,
)
from sys import (
    _getframe as get_frame,
)
from sys import (
    _getframemodulename as get_frame_module_name,
)
from types import (
    FunctionType,
    LambdaType,
    MethodType,
    TypeAliasType,
    UnionType,
)
from typing import (
    Annotated,
    Any,
    Final,
    Literal,
    NotRequired,
    Protocol,
    ReadOnly,
    Required,
    TypedDict,
    Union,
    _TypedDictMeta,
    cast,
    dataclass_transform,
    get_args,
    get_origin,
    get_type_hints,
    runtime_checkable,
)


class MissingTypeAnnotationError(BaseException):
    def __init__(self, type_name: str, *field_names: str) -> None:
        super().__init__(
            f"{type_name!s} is missing type annotation for field(s): {', '.join(fn for fn in field_names)}"
        )


class RedundantParamaterError(BaseException):
    def __init__(self, parameter_name: str, got: int, expected: int = 1) -> None:
        super().__init__(f"{parameter_name = }, {expected = }, {got = }")


class MissingType(Enum):
    MISSING = object()


MISSING: Final[MissingType] = MissingType.MISSING


def get_module_name(obj: Any) -> str:
    obj_type: type[Any] = obj if isinstance(obj, type) else type(obj)
    return obj_type.__module__


def islambda(obj: Any) -> bool:
    return (type(obj) is LambdaType) and (getattr(obj, "__name__", None) == "<lambda>")


def isfunction(obj: Any) -> bool:
    return (type(obj) is FunctionType) and (getattr(type(obj), "__name__", None) == "function")


def ismethod(obj: Any) -> bool:
    return (type(obj) is MethodType) and (getattr(type(obj), "__name__", None) == "method")


def get_type_name[T](obj: T | type[T]) -> str:
    if islambda(obj):
        return "lambda"
    elif isfunction(obj):
        return "function"
    elif ismethod(obj):
        return "ismethod"
    elif isclass(obj):
        return obj.__name__
    else:
        return obj.__class__.__name__


def caller_module_name(*, depth: int = 1, default: str = "__main__") -> str:
    try:
        return get_frame_module_name(depth + 1) or default
    except AttributeError:
        pass
    try:
        return str(get_frame(depth + 1).f_globals.get("__name__", default))
    except AttributeError, ValueError:
        pass
    return default


def iter_fields[T](obj: T) -> Iterator[str]:
    """Yield unique public field names discoverable from an object and its MRO.

    Names are collected from the instance dict first, then each class in the
    MRO via descriptors, annotations, slots, and remaining class dict keys,
    with duplicates removed.

    Respects encapsulation and avoids private namespaces.
    """
    seen: set[str] = set()
    objtype: type[T] = obj if isclass(obj) else type(obj)

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
    for cls in objtype.__mro__:
        yield from _from_class(cls)


def iter_type_annotations[T](obj: T | type[T]) -> Iterator[tuple[str, Any]]:
    target: type[T] = obj if isinstance(obj, type) else type(obj)
    hints: dict[str, Any] = {}
    try:
        hints = get_type_hints(target, include_extras=True)
    except TypeError as e:
        if "does not have annotations" in str(e):
            raise MissingTypeAnnotationError(get_type_name(obj), *iter_fields(obj)) from None

    for field_name in iter_fields(obj):
        if field_name == "mro" and isinstance(obj, type):
            continue
        if field_name not in target.__annotations__:
            continue

        yield (field_name, hints.get(field_name, Any))


def iter_attributes(
    obj: Any, *, static: bool = False, default: Any = MISSING
) -> Iterator[tuple[str, Any]]:
    """Yield (name, value) pairs for public fields that can be read via getattr.

    Skips the "mro" attribute on type objects.
    """
    getter = getattr_static if static is True else getattr
    for field_name in iter_fields(obj):
        if field_name == "mro" and isinstance(obj, type):
            continue
        value = getter(obj, field_name, default)
        type_value = getter(type(obj), field_name, default)
        if ismethod(value) or ismethod(type_value):
            continue
        yield (field_name, value)


def construct_typeddict(
    name: str,
    module: str,
    annotations: dict[str, Any],
    total: bool = False,
    required_keys: Iterable[str] = (),
    optional_keys: Iterable[str] = (),
    readonly_keys: Iterable[str] = (),
) -> type[dict[str, Any]]:
    return cast(
        type[dict[str, Any]],
        _TypedDictMeta(
            name,
            (),
            {
                "__annotations__": annotations,
                "__module__": module,
                "__orig_bases__": (TypedDict,),
                "__total__": total,
                "__required_keys__": frozenset(required_keys),
                "__optional_keys__": frozenset(optional_keys),
                "__readonly_keys__": frozenset(readonly_keys),
            },
        ),
    )


def validate_typeddict(td: type[dict[str, Any]], data: dict[str, Any]) -> None:
    hints = get_type_hints(td, include_extras=True)
    required = td.__required_keys__

    extra = data.keys() - hints.keys()
    if extra:
        raise TypeError(f"Unexpected keys: {extra}")

    missing = required - data.keys()
    if missing:
        raise TypeError(f"Missing required keys: {missing}")


class TypeNode:
    def __init__(self, *, target: Any, parent: Any = MISSING) -> None:
        self.target: Any = target
        self.parent: Any = parent

    @cached_property
    def name(self) -> str | None:
        if self.is_class or self.is_type_alias:
            return self.target.__name__
        return None

    @cached_property
    def is_generic(self) -> bool:
        return self.origin is not None and not self.is_literal and not self.is_union

    @cached_property
    def type_params(self) -> tuple[Any, ...]:
        if self.is_type_alias:
            return self.target.__type_params__
        return ()

    @cached_property
    def is_type_alias(self) -> bool:
        return isinstance(self.target, TypeAliasType)

    @cached_property
    def is_class(self) -> bool:
        return isclass(self.origin)

    @cached_property
    def is_dataclass(self) -> bool:
        return isinstance(self.target, type) and is_dataclass(self.target)

    @cached_property
    def is_optional(self) -> bool:
        return self.is_union and type(None) in self.union_values

    @cached_property
    def option_values(self) -> tuple[Any, ...]:
        if self.is_optional:
            return tuple(arg for arg in self.union_values if arg is not type(None))
        return ()

    @cached_property
    def is_union(self) -> bool:
        return self.origin is Union or self.origin is UnionType

    @cached_property
    def union_values(self) -> tuple[Any, ...]:
        if self.is_union:
            return get_args(self.inner_type)
        return ()

    @cached_property
    def inner_type(self) -> Any:
        if self.is_annotated:
            return get_args(self.target)[0]
        elif self.is_type_alias:
            return self.target.__value__
        return self.target

    @cached_property
    def is_annotated(self) -> bool:
        return get_origin(self.target) is Annotated

    @cached_property
    def annotated_extras(self) -> tuple[Any, ...]:
        if self.is_annotated:
            return get_args(self._raw)[1:]
        return ()

    @cached_property
    def is_literal(self) -> bool:
        return self.origin is Literal

    @cached_property
    def literal_values(self) -> tuple[Any, ...]:
        if self.is_literal:
            return get_args(self.inner_type)
        return ()

    @cached_property
    def is_readonly(self) -> bool:
        return self.origin is ReadOnly

    @cached_property
    def is_required(self) -> bool:
        return self.origin is Required

    @cached_property
    def is_not_required(self) -> bool:
        return self.origin is NotRequired

    @cached_property
    def origin(self) -> Any | None:
        return get_origin(self.inner_type)

    @cached_property
    def args(self) -> tuple[TypeNode, ...]:
        if self.is_literal:
            return ()
        return tuple(TypeNode(self, a) for a in get_args(self.inner_type) if a is not type(None))


class FieldNode:
    def __init__(self, default: Any, default_factory: Callable[[], Any] | MissingType) -> None:
        self.default: Any = default
        self.default_factory: Callable[[], Any] | MissingType = default_factory

    def __set_name__(self, owner: type[Any], name: str) -> None:
        self.name: str = name
        self.annotation: Any = get_type_hints(owner, include_extras=True).get(self.name, Any)
        self.typenode: TypeNode = TypeNode(target=self.annotation, parent=self)
        if not hasattr(owner, "__field_nodes__"):
            type.__setattr__(owner, "__field_nodes__", {})
        owner.__field_nodes__[self.name] = self

    @property
    def required(self) -> bool:
        return self.typenode.is_required

    @property
    def not_required(self) -> bool:
        return self.typenode.is_not_required

    @property
    def optional(self) -> bool:
        return self.typenode.is_optional

    @property
    def readonly(self) -> bool:
        return self.typenode.is_readonly

    @property
    def has_default(self) -> bool:
        return self.default is not MISSING

    @property
    def has_default_factory(self) -> bool:
        return self.default_factory is not MISSING


def fieldnode(
    *,
    default: Any = MISSING,
    default_factory: Callable[[], Any] | MissingType = MISSING,
    primary_key: bool = False,
) -> FieldNode:
    return FieldNode(
        default=default,
        default_factory=default_factory,
        primary_key=primary_key,
    )


@runtime_checkable
class _SchematicProtocol(Protocol):
    __field_nodes__: dict[str, FieldNode]
    __total__: bool
    __defaults__: dict[str, Any]
    __default_factories__: dict[str, Callable[[], Any]]
    __annotations__: dict[str, Any]
    __primary_key__: tuple[str, FieldNode]
    __spec__: type[dict[str, Any]]


class _SchematicMeta(type):
    def __new__(
        mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any], **kwargs: Any
    ) -> type:
        return super().__new__(mcs, name, bases, namespace)

    def __init__(
        cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any], **kwargs: Any
    ) -> type:
        super().__init__(name, bases, namespace, **kwargs)

    def __call__(cls, **kwargs: Any) -> ...:
        data = cls.__defaults__.copy()
        for field, factory in cls.__default_factories__.items():
            data[field] = factory()
        data.update(kwargs)
        try:
            validate_typeddict(cls.__spec__, data)
        except TypeError:
            raise ValueError(
                f"Provided keywords does not match specification as defined on {cls.__name__}"
            ) from None
        new_instance = cls.__new__()  # type: ignore[call-arg]
        new_instance.__dict__.update(data)
        return new_instance

    @cached_property
    def required_keys(cls) -> frozenset[str]:
        assert hasattr(cls, "__spec__")
        return cast(frozenset[str], cls.__spec__.__required_keys__)

    @cached_property
    def optional_keys(cls) -> frozenset[str]:
        assert hasattr(cls, "__spec__")
        return cast(frozenset[str], cls.__spec__.__optional_keys__)

    @cached_property
    def readonly_keys(cls) -> frozenset[str]:
        assert hasattr(cls, "__spec__")
        return cast(frozenset[str], cls.__spec__.__readonly_keys__)


@dataclass_transform(field_specifiers=(FieldNode, fieldnode))
def schematic(
    cls: type[_SchematicProtocol], total: bool = False, closed: bool = True
) -> _SchematicMeta:
    namespace: dict[str, Any] = dict(vars(cls))

    defaults: dict[str, Any] = {}
    default_factories: dict[str, Callable[[], Any]] = {}

    required: set[str] = set()
    optional: set[str] = set()
    readonly: set[str] = set()

    annotations: dict[str, Any] = {}

    primary_key: tuple[str, FieldNode] | None = None

    for fname, fnode in namespace["__field_nodes__"].items():
        annotations[fname] = fnode.type

        if fnode.primary_key:
            if primary_key is not None:
                raise RedundantParamaterError("primary_key", 2)
            else:
                primary_key = (fname, fnode)

        if fnode.has_default:
            defaults[fname] = fnode.default
        elif fnode.has_default_factory:
            default_factories[fname] = fnode.default_factory

        if fnode.required or (total is True and not fnode.not_required):
            required.add(fname)
        if fnode.optional:
            optional.add(fname)
        if fnode.readonly:
            readonly.add(fname)

    if not primary_key:
        raise ValueError(f"{cls.__name__} missing primary_key")

    namespace["__field_nodes__"] = cls.__field_nodes__
    namespace["__total__"] = total
    namespace["__defaults__"] = defaults
    namespace["__default_factories__"] = default_factories
    namespace["__annotations__"] = annotations
    namespace["__primary_key__"] = ()
    namespace["__spec__"] = construct_typeddict(
        name=f"{cls.__name__}Spec",
        module=cls.__module__,
        annotations=annotations,
        required_keys=required,
        optional_keys=optional,
        readonly_keys=readonly,
    )

    schematic: _SchematicMeta = _SchematicMeta(
        name=cls.__name__,
        bases=cls.__bases__,
        namespace=namespace,
    )

    return schematic
