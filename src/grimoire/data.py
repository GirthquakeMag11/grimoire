from __future__ import annotations

import asyncio
import inspect
from dataclasses import (
    is_dataclass,
    fields as dataclass_fields,
    Field,
)
from annotationlib import (
    Format,
)
from collections import (
    UserDict,
)
from collections.abc import (
    Awaitable,
    Callable,
    Coroutine,
    Iterator,
)
from dataclasses import (
    _MISSING_TYPE as MissingType,
)
from dataclasses import (
    MISSING as MISSING,
)
from inspect import (
    Parameter,
    Signature,
    getattr_static,
)
from inspect import (
    isclass as inspect_isclass,
)
from inspect import (
    signature as inspect_signature,
)
from inspect import (
    _ParameterKind as ParameterKind,
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
)
from typing import (  # type: ignore[attr-defined]
    Any,
    TypedDict,
    _TypedDictMeta,
    cast,
    get_type_hints,
    Literal,
    Required,
    NotRequired,
    Annotated,
    Optional,
    Union,
    ReadOnly,
)

type Job[T] = (
    Callable[..., T]
    | Callable[[], Coroutine[Any, Any, T]]
    | Callable[..., Awaitable[T]]
    | Coroutine[Any, Any, T]
    | Awaitable[T]
)


class MissingTypeAnnotationError(BaseException):
    def __init__(self, type_name: str, *field_names: str) -> None:
        super().__init__(
            f"{type_name!s} is missing type annotation for field(s): {', '.join(fn for fn in field_names)}"
        )


def ensure_async[T](job: Job[T], *args: Any, **kwargs: Any) -> Awaitable[T]:
    if inspect.iscoroutinefunction(job):
        return job(*args, **kwargs)
    if inspect.isawaitable(job):
        return job
    if callable(job):
        return asyncio.to_thread(job, *args, **kwargs)  # type: ignore[arg-type]
    raise TypeError(f"Cannot coerce {type(job).__name__} into an awaitable")


def is_lambdafunc(obj: Any) -> bool:
    return (type(obj) is LambdaType) and (getattr(obj, "__name__", None) == "<lambda>")


def is_namedfunc(obj: Any) -> bool:
    return (type(obj) is FunctionType) and (getattr(obj, "__name__", "<lambda>") != "<lambda>")


def get_module_name[T](obj: T) -> str:
    objtype: type[T] = obj if inspect_isclass(obj) else type(obj)
    return objtype.__module__


def get_type_name[T](obj: T | type[T]) -> str:
    if is_lambdafunc(obj):
        return "lambda"
    objtype: type[T] = obj if inspect_isclass(obj) else type(obj)  # type: ignore[assignment]
    return objtype.__name__


def iter_fields[T](obj: T) -> Iterator[str]:
    """Yield unique public field names discoverable from an object and its MRO.

    Names are collected from the instance dict first, then each class in the
    MRO via descriptors, annotations, slots, and remaining class dict keys,
    with duplicates removed.

    Respects encapsulation and avoids private namespaces.
    """
    seen: set[str] = set()
    objtype: type[T] = obj if inspect_isclass(obj) else type(obj)

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


def iter_attributes(obj: Any, *, static: bool = False) -> Iterator[tuple[str, Any]]:
    """Yield (name, value) pairs for public fields that can be read via getattr.

    Skips the "mro" attribute on type objects.
    """
    getter = getattr_static if static is True else getattr
    for field_name in iter_fields(obj):
        if field_name == "mro" and isinstance(obj, type):
            continue
        yield (field_name, getter(obj, field_name, MISSING))


def iter_type_annotations[T](obj: T | type[T], *, strict: bool = True) -> Iterator[tuple[str, Any]]:
    target: type[T] = obj if inspect_isclass(obj) else type(obj)  # type: ignore[assignment]
    hints: dict[str, Any] = {}
    try:
        hints = get_type_hints(target, include_extras=True)
    except TypeError as e:
        if "does not have annotations" in str(e) and strict is True:
            raise MissingTypeAnnotationError(get_type_name(obj), *iter_fields(obj)) from None

    for field_name in iter_fields(obj):
        if field_name == "mro" and isinstance(obj, type):
            continue
        if field_name not in hints and strict is True:
            raise MissingTypeAnnotationError(get_type_name(obj), field_name)

        yield (field_name, hints.get(field_name, Any))


def iter_parameter_annotations(
    obj: Callable[..., Any], *, strict: bool = True
) -> Iterator[tuple[str, Any]]:
    sig: Signature = inspect_signature(obj, eval_str=True, annotation_format=Format.FORWARDREF)
    params: dict[str, Any] = dict(sig.parameters)
    for name, param in params.items():
        if param.annotation is Parameter.empty:
            if strict is True:
                raise MissingTypeAnnotationError(get_type_name(obj), name)
            else:
                yield (name, Any)
        else:
            yield (name, param.annotation)


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


@dataclass
class TypeNode:
    _parent: Any
    target: Any

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
        return inspect_isclass(self.origin)

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


@dataclass
class PseudoField:
    _type: type[Any]
    _name: str

    @property
    def value(self) -> Any:
        return getattr(self._type, self._name, MISSING)

    @property
    def static(self) -> Any:
        return getattr_static(self._type, self._name, MISSING)


@dataclass
class FieldNode:
    _parent: Any
    target: Any

    @cached_property
    def name(self) -> str | None:
        if self.is_param or self.is_field:
            return self.target.name
        return None

    @cached_property
    def has_default(self) -> bool:
        if self.is_param:
            return (self.target.default is not Parameter.empty)
        elif self.is_field:
            return (self.target.default is not MISSING)

    @cached_property
    def default(self) -> Any:
        if self.has_default:
            return self.target.default
        return MISSING

    @cached_property
    def has_default_factory(self) -> bool:
        if self.is_field:
            return self.target.default_factory is not MISSING
        return False

    @cached_property
    def is_param(self) -> bool:
        return isinstance(self.target, Parameter)

    @cached_property
    def is_field(self) -> bool:
        return isinstance(self.target, Field)

    @cached_property
    def type(self) -> TypeNode | MissingType:
        if self.is_param:
            if self.target.annotation is Parameter.empty:
                return MISSING
            return TypeNode(self, self.target.annotation)
        elif self.is_field:
            return TypeNode(self, self.target.type)

    @cached_property
    def var_positional(self) -> bool:
        if self.is_param:
            return (self.target.kind is ParameterKind.VAR_POSITIONAL)
        return False

    @cached_property
    def var_keyword(self) -> bool:
        if self.is_param:
            return (self.target.kind is ParameterKind.VAR_KEYWORD)
        return False

    @cached_property
    def positional_only(self) -> bool:
        if self.is_param:
            return (self.target.kind is ParameterKind.POSITIONAL_ONLY)
        return False

    @cached_property
    def positional_or_keyword(self) -> bool | None:
        if self.is_param:
            return (self.target.kind is ParameterKind.POSITIONAL_OR_KEYWORD)
        elif self.is_field:
            return (self.target.kw_only is not True)
        return None

    @cached_property
    def keyword_only(self) -> bool | None:
        if self.is_param:
            return (self.target.kind is ParameterKind.KEYWORD_ONLY)
        elif self.is_field:
            return (self.target.kw_only is True)
        return None



def model_typeddict(
    obj: Any,
    *,
    total: bool = False,
    strict: bool = True,
    type_name: str | None = None,
    mod_name: str | None = None,
) -> type[dict[str, Any]]:
    is_callable = isinstance(obj, (FunctionType, LambdaType, MethodType))
    is_class = inspect_isclass(obj)
    obj_type = obj if is_class else type(obj)
    is_data = is_dataclass(obj_type)

    name = type_name if type_name is not None else get_type_name(obj)
    module = mod_name if mod_name is not None else caller_module_name(default=get_module_name(obj))

    annotations = (
        dict(iter_parameter_annotations(cast(Callable[..., Any], obj), strict=strict))
        if is_callable
        else dict(iter_type_annotations(obj, strict=strict))
    )

    fieldnodes: list[FieldNode]

    if is_data:
        fieldnodes = [FieldNode(f) for f in dataclass_fields(obj_type)]
    elif is_callable:
        fieldnodes = [FieldNode(p) for p in list(inspect_signature(obj).parameters.values())]
    else:
        fieldnodes = [FieldNode(p) for p in list(inspect_signature(obj_type.__init__).parameters.values())]

    required: set[str] = set()
    optional: set[str] = set()
    readonly: set[str] = set()

    for fnode in fieldnodes:
        if fnode.name not in annotations:
            continue

        if fnode.type.is_required or (not fnode.has_default and not fnode.has_default_factory):
            required.add(fnode.name)
        if fnode.type.is_optional or (fnode.has_default and fnode.default is None):
            optional.add(fnode.name)
        if fnode.type.is_readonly:
            readonly.add(fnode.name)

        if fnode.var_positional:
            annotations[fnode.name] = Iterable[annotations[fnode.name]]
        if fnode.var_keyword:
            annotations[fnode.name] = dict[str, annotations[fnode.name]]

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
                "__required_keys__": frozenset(required),
                "__optional_keys__": frozenset(optional),
                "__readonly_keys__": frozenset(readonly),
            },
        ),
    )

