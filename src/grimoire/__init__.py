from .inspection import (
    iter_fields,
    iter_attributes,
    compose_signature,
    decompose_attrs,
    tree_attrs,
)
from .record import Record
from ._test import _test

__all__ = [
    "iter_fields",
    "iter_attributes",
    "compose_signature",
    "decompose_attrs",
    "tree_attrs",
]
