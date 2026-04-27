from ._test import _test
from .inspection import (
    compose_signature,
    decompose_attrs,
    iter_attributes,
    iter_fields,
    tree_attrs,
)
from .record import Record

__all__ = [
    "compose_signature",
    "decompose_attrs",
    "iter_attributes",
    "iter_fields",
    "tree_attrs",
]
