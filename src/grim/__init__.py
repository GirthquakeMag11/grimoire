from . import table
from .inspection import (
    classify_attribute,
    decompose,
    dict_attributes,
    field_is_optional,
    iter_attributes,
    iter_fields,
)

__all__ = [
    "iter_fields",
    "iter_attributes",
    "decompose",
    "dict_attributes",
    "classify_attribute",
    "field_is_optional",
    "table",
]
