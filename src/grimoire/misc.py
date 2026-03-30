from __future__ import annotations

import collections.abc
from dataclasses import dataclass, field
import types
import typing
from typing import (
    get_type_hints,
    get_origin,
    get_args
)

# type TypeAnnotation = typing._AnyMeta | typing._TupleType | typing._SpecialForm | typing._ProtocolMeta | typing._CallableType | typing._SpecialGenericAlias | typing._TypedCacheSpecialForm | typing._DeprecatedGenericAlias

# type of "type Example" is typing.TypeAliasType, type of actual "TypeAlias" is _SpecialForm

type TypeAnnotation = (
    typing._AnyMeta
    | typing._TupleType
    | typing._SpecialForm
    | typing._ProtocolMeta
    | typing._CallableType
    | typing._SpecialGenericAlias
    | typing._TypedCacheSpecialForm
    | typing._DeprecatedGenericAlias
)

type BuiltInType = (
    types.FunctionType
    | types.LambdaType
    | types.CodeType
    | types.MappingProxyType
    | types.CellType
    | types.GeneratorType
    | types.CoroutineType
    | types.AsyncGeneratorType
    | types.MethodType
    | types.BuiltinFunctionType
    | types.BuiltinMethodType
    | types.WrapperDescriptorType
    | types.MethodWrapperType
    | types.MethodDescriptorType
    | types.ClassMethodDescriptorType
    | types.ModuleType
    | types.TracebackType
    | types.FrameType
    | types.GetSetDescriptorType
    | types.MemberDescriptorType
    | types.DynamicClassAttribute
    | types.GenericAlias
    | types.UnionType
    | types.EllipsisType
    | types.NoneType
    | types.NotImplementedType
)

type BuiltInBaseClass = (
    collections.abc.Hashable
    | collections.abc.Awaitable
    | collections.abc.Coroutine
    | collections.abc.AsyncIterable
    | collections.abc.AsyncIterator
    | collections.abc.AsyncGenerator
    | collections.abc.Iterable
    | collections.abc.Iterator
    | collections.abc.Reversible
    | collections.abc.Generator
    | collections.abc.Sized
    | collections.abc.Container
    | collections.abc.Collection
    | collections.abc.Buffer
    | collections.abc.Callable
    | collections.abc.Set
    | collections.abc.MutableSet
    | collections.abc.Mapping
    | collections.abc.MappingView
    | collections.abc.KeysView
    | collections.abc.ItemsView
    | collections.abc.ValuesView
    | collections.abc.MutableMapping
    | collections.abc.Sequence
    | collections.abc.MutableSequence
)


