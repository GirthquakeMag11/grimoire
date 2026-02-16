"""In-place mutation utilities for lists and dictionaries."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeVar

K = TypeVar("K", bound=str | int | float | tuple[str | int | float, ...])
T = TypeVar("T")


def update_list(target: list[T], source: Sequence[T]) -> list[T]:
    """Replace and extend a list in-place with items from a source sequence.

    Updates the target list by:
    1. Replacing existing items at matching indices
    2. Extending with any additional items from source

    This mutates the target list **in-place** and does **not** create a new instance.

    Args:
        target: The list to be modified in-place
        source: A sequence of items to copy into target

    Returns:
        The modified target list (same object, for chaining)
    """
    target_len = len(target)
    source_len = len(source)

    # Replace existing items
    for i in range(min(target_len, source_len)):
        target[i] = source[i]

    # Extend if source is longer
    if source_len > target_len:
        target.extend(source[target_len:])

    return target


def update_dict(target: dict[K, T], source: Mapping[K, T]) -> dict[K, T]:
    """Update a dictionary in-place with items from a source mapping.

    This is a simple wrapper around dict.update() that returns the modified
    dictionary for method chaining. Mutates the target dict **in-place** and
    does **not** create a new instance.

    Args:
        target: The dictionary to be modified in-place
        source: A mapping of key-value pairs to copy into target

    Returns:
        The modified target dictionary (same object, for chaining)
    """
    target.update(source)
    return target
