"""
nested_enum.py
==============
Provides NestedEnum and NestedEnumMeta, enabling deeply nested enum hierarchies
where isinstance checks propagate upward through every ancestor class in the
nesting chain.


Overview
--------
Standard Python Enum subclasses defined inside another enum are not treated as
members — they become plain class attributes. NestedEnum builds on that behaviour
to additionally record each nested class's parent, so that isinstance(member,
ancestor) returns True all the way up the chain.


Defining a Hierarchy
--------------------
Subclass NestedEnum at every level. Leaf members are declared exactly as they
would be in a standard Enum:

    class EventType(NestedEnum):
        class UserEvents(NestedEnum):
            class Interaction(NestedEnum):
                NEW    = "new"
                EDIT   = "edit"
                DELETE = "delete"

            class Navigation(NestedEnum):
                PAGE_VIEW = "page_view"
                BACK      = "back"


isinstance Checks
-----------------
A leaf member is an instance of its own class and every ancestor up to the root:

    event = EventType.UserEvents.Interaction.NEW

    isinstance(event, EventType.UserEvents.Interaction)  # True  — direct class
    isinstance(event, EventType.UserEvents)              # True  — one level up
    isinstance(event, EventType)                         # True  — two levels up

Members in a different branch of the same hierarchy are not matched:

    isinstance(event, EventType.UserEvents.Navigation)   # False — wrong branch


Structural Pattern Matching
---------------------------
Two pattern forms are available inside a match block:

Value pattern — matches one exact member using ==:

    match event:
        case EventType.UserEvents.Interaction.NEW:
            ...  # only this specific member

Class pattern — matches any member for which isinstance returns True, meaning
the whole subtree rooted at that class:

    match event:
        case EventType.UserEvents.Interaction.NEW:
            ...  # exact member first
        case EventType.UserEvents.Interaction():
            ...  # any other Interaction member
        case EventType.UserEvents.Navigation():
            ...  # any Navigation member
        case EventType.UserEvents():
            ...  # any remaining UserEvents member
        case _:
            ...  # anything else

WARNING: Class patterns must be ordered from most specific to least specific.
A broader ancestor pattern (e.g. EventType.UserEvents()) will silently shadow
all more specific patterns that follow it, because isinstance returns True for
every descendant. Python does not emit a warning for unreachable case branches.


Accessing Members
-----------------
Members are accessed by traversing the nesting path, exactly as with nested
class attributes:

    EventType.UserEvents.Interaction.NEW    # <Interaction.NEW: 'new'>
    EventType.UserEvents.Navigation.BACK    # <Navigation.BACK: 'back'>

Standard enum conveniences work normally on any leaf class:

    list(EventType.UserEvents.Interaction)       # [NEW, EDIT, DELETE]
    EventType.UserEvents.Interaction["EDIT"]     # <Interaction.EDIT: 'edit'>
    EventType.UserEvents.Interaction("delete")   # <Interaction.DELETE: 'delete'>


Limitations
-----------
- Only leaf classes (those that actually declare members) should contain enum
  values. Intermediate classes (EventType, UserEvents) are structural containers
  and should remain empty of members.

- Multiple inheritance involving two separate NestedEnum roots is not supported;
  _nested_parent tracks a single linear chain.

- Iterating over an intermediate class (e.g. list(EventType)) yields an empty
  sequence — only leaf classes are iterable in the usual enum sense.
"""

from __future__ import annotations

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
        if super().__instance__(instance):
            return True
        # Walk up the nested parent chain of the instance's own enum class
        inst_type = type(instance)
        if isinstance(inst_type, NestedEnumMeta):
            parent: NestedEnumMeta | None = inst_type._nested_parent
            while parent is not None:
                if parent is cls:
                    return True
                parent = parent._nested_parent
        return False

class NestedEnum(Enum, metaclass=NestedEnumMeta):
    """Base class for enums that propogate isinstance checks up the nesting hierarchy."""
