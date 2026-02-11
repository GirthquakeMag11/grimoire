from __future__ import annotations

from typing import Any, Dict, Hashable, List


def update_list(target: List[Any], source: List[Any]) -> List[Any]:
    """Replace items in 'target' list with items from 'source' list and
    return modified 'target' list.
    This mutates a list **in-place** and **does not** create a new instance.
    """
    for i in range(len(target)):
        if i < len(source):
            target[i] = source[i]

    if len(target) < len(source):
        target.extend(source[len(target) :])

    return target


def update_dict(
    target: Dict[Hashable, Any], source: Dict[Hashable, Any]
) -> Dict[Hashable, Any]:
    """Replace items in 'target' dict with items from 'source' dict and
    return modified 'target' dict.
    This mutates a dict **in-place** and **does not** create a new instance.

    Note:
        Yes, this is redundant, but at least it's not bound to a class.
    """
    for key, value in source.items():
        target[key] = value
    return target
