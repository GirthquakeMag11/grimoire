from __future__ import annotations

import functools
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

def maybe_params(
    decorator_factory: Callable[..., Callable[[F], F]],
) -> Callable[..., Any]:
    """Allow a parameterized decorator to be used with or without
    parentheses.

    Wraps a decorator factory so it can be applied as either
    @decorator or @decorator(...), using default parameters when
    no arguments are supplied.
    """

    @functools.wraps(decorator_factory)
    def outer(*args, **kwargs):
        """Dispatch between direct decoration and factory invocation."""
        if len(args) == 1 and not kwargs:
            target = args[0]
            if callable(target):
                decorator = decorator_factory()
                return decorator(target)
            raise TypeError(
                "Decorator used without parentheses must be applied to a callable"
            )
        return decorator_factory(*args, **kwargs)

    return outer
