from collections.abc import Iterator, Iterable, Callable
from typing import Any, get_type_hints
from types import SimpleNamespace, LambdaType
import inspect

_test = SimpleNamespace(
    name="alice",
    score=97.5,
    active=True,
    tags=["admin", "beta"],
    counts=(3, 7, 12),
    meta={"region": "us-west", "tier": 2},
    profile=SimpleNamespace(
        age=30,
        emails=["alice@work.com", "alice@home.net"],
        prefs=SimpleNamespace(
            theme="dark",
            font_size=14,
            pinned_items=frozenset({101, 202}),
        ),
    ),
    history=[
        SimpleNamespace(action="login", ts=1700000000),
        SimpleNamespace(action="upload", ts=1700003600, details={"size_kb": 480}),
    ],
    dimensions=range(5),
    nothing=None,
    type=SimpleNamespace,
)


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

        if param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.VAR_POSITIONAL):
            parameter["position"] = idx

        if param.default is not inspect.Parameter.empty:
            parameter["default"] = param.default

        if keyword in hints:
            parameter["annotation"] = hints.get(keyword)

        if parameter:
            signature.setdefault("parameters", {})[keyword] = parameter

    return signature


def decompose_attrs(obj: Any, *, _cache: dict[int, dict[str, Any]] | None = None, _parent: Any | None = None) -> dict[str, Any]:
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
        result["data"] = {str(k): decompose_attrs(v, _cache=_cache, _parent=obj) for k, v in obj.items()}
        return result

    if callable(obj):
        if isinstance(obj, LambdaType):
            result["class"] = "lambda"
            return result

        result["signature"] = compose_signature(obj)

        if obj_class.__name__ == "builtin_function_or_method":
            result["class"] = "builtin_method" if _parent is not None else "builtin_function"
            return result

    attributes = {}
    for name, value in iter_attributes(obj):
        attributes[name] = decompose_attrs(value, _cache=_cache, _parent=obj)

    if attributes:
        result["attributes"] = attributes
    return result


def tree_attrs(obj: Any, *, _name: str | None = None) -> dict[str, Any]:
    res: dict[str, Any] = {}
    obj_name: str = _name if _name is not None else type(obj).__name__.lower()

    def index_as_attrs(seq: Iterable[Any]) -> Iterator[tuple[str, Any]]:
        for idx, item in enumerate(seq):
            yield (f"{idx!s}", item)

    def keys_as_attrs(data: dict[..., Any]) -> Iterator[tuple[str, Any]]:
        for key, item in data.items():
            yield (f"{key!s}", item)

    def attr_dispenser() -> Iterator[tuple[str, Any]]:
        if isinstance(obj, (bool, int, float, str, bytes)):
            raise TypeError(type(obj).__name__)

        elif isinstance(obj, (list, tuple, set, frozenset)):
            yield from index_as_attrs(obj)

        elif isinstance(obj, dict):
            yield from keys_as_attrs(obj)

        else:
            yield from iter_attributes(obj)

    for name, value in attr_dispenser():
        key = obj_name + "__" + name + "_" + type(value).__name__.lower()

        if isinstance(value, (bool, int, float, str, bytes)):
            res[key] = value
            continue

        branch = tree_attrs(value, _name=key)
        res.update(branch)

    return res
