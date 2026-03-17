from __future__ import annotations

from collections.abc import Iterator
from enum import Enum, EnumMeta
from typing import Any


class NestedEnumMeta(EnumMeta):
    """
    Metaclass extending EnumMeta to support hierarchical isinstance checks.

    When a NestedEnum subclass is defined inside another, isinstance() on a
    leaf member returns True for every ancestor class in the chain.
    """

    _nested_parent: NestedEnumMeta | None

    def __new__(
        metacls,
        name: str,
        bases: tuple[type, ...],
        namespace: Any,
        **kwargs: Any,
    ) -> NestedEnumMeta:
        cls = super().__new__(metacls, name, bases, namespace, **kwargs)
        cls._nested_parent = None
        return cls

    def __get__(cls, obj: object, objtype: type | None = None) -> NestedEnumMeta:
        """
        Marks every NestedEnum class as a non-data descriptor.

        When EnumMeta scans the enclosing class body, it calls `_is_descriptor()`
        on each value, which resolves __get__ via the metaclass. Finding it here
        causes EnumMeta to store the nested class as a plan attribute rather than
        an enum member. Accessing it normally still returns the class iself.
        """
        return cls

    def __set_name__(cls, owner: type, name: str) -> None:
        """
        Called by type.__new__ when the nested class is bound to the enclosing
        class.
        Records the enclosing NestedEnum as this class's parent.
        """
        if isinstance(owner, NestedEnumMeta):
            cls._nested_parent = owner

    def __instancecheck__(cls, instance: object) -> bool:
        # Standard check covers the direct enum (e.g. ExampleEnum.MEMBER -> ExampleEnum)
        if super().__instancecheck__(instance):
            return True
        # Walk up the nested parent chain of the instance's own enum class
        inst_type = type(instance)
        if isinstance(inst_type, NestedEnumMeta):
            parent: NestedEnumMeta | None = inst_type._nested_parent  # type: ignore[attr-defined]
            while parent is not None:
                if parent is cls:
                    return True
                parent = parent._nested_parent
        return False

    def children(cls) -> Iterator[NestedEnumMeta]:
        """Yield the immediate nested NestedEnum subclasses of this class."""
        for val in vars(cls).values():
            if isinstance(val, NestedEnumMeta):
                yield val

    def walk(cls) -> Iterator[NestedEnum]:
        """Yield all leaf members in the subtree rooted at this class, depth-first."""
        yield from cls
        for child in cls.children():
            yield from child.walk()


class NestedEnum(Enum, metaclass=NestedEnumMeta):
    """Base class for enums that propogate isinstance checks up the nesting hierarchy."""
