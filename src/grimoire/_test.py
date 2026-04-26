"""Stress-test fixture for a ``get_type_hints``-based data parser.

Covers, in one dataclass:

* Old-style ``TypeAlias`` and PEP 695 ``type`` statements (incl. a recursive one).
* ``Annotated`` — plain, nested inside generics, nested inside unions, and
  as an alias target.
* ``Literal`` — homogeneous and mixed.
* PEP 604 unions (``X | Y``) and ``X | None``.
* Generics: builtins, ``collections.abc`` ABCs, custom ``Generic[T]`` class,
  and a PEP 695 ``class Foo[T, U]``.
* ``NewType``, ``TypedDict`` (total and non-total), ``NamedTuple``,
  ``Protocol``, ``Enum`` / ``IntEnum``.
* ``Callable`` — fixed and variadic.
* ``ClassVar`` and ``Final`` (both of which ``get_type_hints`` will surface
  and a parser typically needs to skip or special-case).
* Forward references, including a deliberately double-quoted one.

Designed to be loaded with ``get_type_hints(StressTest, include_extras=True)``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import (
    Annotated,
    Any,
    ClassVar,
    Final,
    Generic,
    Literal,
    NamedTuple,
    NewType,
    NotRequired,
    Protocol,
    Required,
    TypeAlias,
    TypedDict,
    TypeVar,
    runtime_checkable,
)

# ---------------------------------------------------------------------------
# Supporting types
# ---------------------------------------------------------------------------


class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class Priority(IntEnum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2


UserId = NewType("UserId", int)
Score = NewType("Score", float)


class Point(NamedTuple):
    x: float
    y: float
    label: str = ""


class AddressDict(TypedDict):
    street: str
    city: str
    zip_code: str


class PartialAddressDict(TypedDict, total=False):
    street: str
    city: str
    zip_code: str


class MixedRequirednessDict(TypedDict):
    id: Required[int]
    nickname: NotRequired[str]


@runtime_checkable
class SupportsName(Protocol):
    @property
    def name(self) -> str: ...


T = TypeVar("T")


@dataclass
class Box(Generic[T]):
    value: T


# PEP 695 generic class
class Pair[A, B]:
    def __init__(self, a: A, b: B) -> None:
        self.a = a
        self.b = b


@dataclass(frozen=True)
class FieldMeta:
    """Marker used inside ``Annotated[...]`` to stress metadata extraction."""

    description: str = ""
    deprecated: bool = False


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

# Old-style explicit TypeAlias
UserName: TypeAlias = str
IntOrStr: TypeAlias = int | str
OptionalTags: TypeAlias = list[str] | None
StringMap: TypeAlias = dict[str, str]
PositiveInt: TypeAlias = Annotated[int, FieldMeta(description="non-negative"), "positive"]

# PEP 695 ``type`` statements (lazy-evaluated TypeAliasType objects)
type Vector = list[float]
type Matrix = list[Vector]
type JSONPrimitive = str | int | float | bool | None
type JSONValue = JSONPrimitive | list[JSONValue] | dict[str, JSONValue]  # recursive
type Handler[U] = Callable[[U], None]
type MaybeBoxed[U] = Box[U] | None


# ---------------------------------------------------------------------------
# The stress-test dataclass
# ---------------------------------------------------------------------------


@dataclass
class StressTest:
    # --- Plain primitives ---
    plain_int: int
    plain_str: str
    plain_bool: bool
    plain_float: float
    plain_bytes: bytes
    plain_none: None

    # --- Generic builtins ---
    list_of_ints: list[int]
    dict_str_int: dict[str, int]
    tuple_fixed: tuple[int, str, bool]
    tuple_variadic: tuple[int, ...]
    tuple_empty: tuple[()]
    set_of_strs: set[str]
    frozenset_of_floats: frozenset[float]

    # --- Nested generics ---
    nested_mapping: dict[str, list[tuple[int, int]]]
    list_of_dicts: list[dict[str, Any]]
    deeply_nested: list[dict[str, list[tuple[int, str | None]]]]

    # --- Unions (PEP 604) ---
    int_or_str: int | str
    optional_int: int | None
    three_way: int | str | bytes
    optional_list: list[int] | None
    union_of_generics: list[int] | dict[str, int] | None

    # --- Literals ---
    mode: Literal["r", "w", "a"]
    mixed_literal: Literal[1, "two", True, None]
    single_literal: Literal["only"]
    literal_in_union: Literal["auto"] | int

    # --- Annotated ---
    age: Annotated[int, FieldMeta(description="years")]
    tagged_str: Annotated[str, "tag1", "tag2"]
    nested_annotated: Annotated[list[int], FieldMeta(description="ids")]
    annotated_inside_generic: list[Annotated[int, FieldMeta(description="row id")]]
    annotated_union: Annotated[int | str, FieldMeta(description="either")]
    optional_annotated: Annotated[str, FieldMeta(deprecated=True)] | None
    double_annotated: Annotated[Annotated[int, "inner"], "outer"]

    # --- Type aliases (old style) ---
    username: UserName
    either: IntOrStr
    tags: OptionalTags
    config: StringMap
    positive: PositiveInt

    # --- PEP 695 aliases ---
    vector: Vector
    matrix: Matrix
    json_prim: JSONPrimitive
    json_value: JSONValue  # recursive — the classic parser breaker
    int_handler: Handler[int]
    maybe_boxed_str: MaybeBoxed[str]

    # --- NewType ---
    user_id: UserId
    score: Score
    optional_user_id: UserId | None

    # --- Enums ---
    color: Color
    priority: Priority
    optional_color: Color | None

    # --- Custom / generic classes ---
    point: Point
    address: AddressDict
    partial_address: PartialAddressDict
    mixed_td: MixedRequirednessDict
    named: SupportsName
    boxed_int: Box[int]
    boxed_str_list: Box[list[str]]
    boxed_optional: Box[int | None]
    pair: Pair[int, str]
    nested_pair: Pair[Box[int], list[str]]

    # --- ABCs from collections.abc ---
    sequence_of_ints: Sequence[int]
    mapping_str_any: Mapping[str, Any]
    callable_field: Callable[[int, str], bool]
    variadic_callable: Callable[..., None]
    callable_returning_union: Callable[[int], str | None]

    # --- Forward references (self & other) ---
    parent: StressTest | None
    children: list[StressTest]
    sibling: "StressTest | None"  # deliberately double-quoted
    forward_boxed: "Box[StressTest]"

    # --- Any / object ---
    anything: Any
    obj: object

    # --- Defaults with factories (keep these at the end) ---
    extras: dict[str, Any] = field(default_factory=dict)
    history: list[int] = field(default_factory=list)
    meta_tags: Annotated[list[str], FieldMeta(description="free-form")] = field(
        default_factory=list
    )

    # --- ClassVar / Final — present in __annotations__, typically skipped by parsers ---
    VERSION: ClassVar[str] = "1.0"
    REGISTRY: ClassVar[dict[str, type[StressTest]]] = {}
    MAX_ITEMS: Final[int] = 100
