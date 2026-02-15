"""Utilities for creating flexible decorator factories."""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def maybe_params(
    decorator_factory: Callable[..., Callable[[F], F]],
) -> Callable[..., F | Callable[[F], F]]:
    """Allow a parameterized decorator to be used with or without parentheses.

    Wraps a decorator factory so it can be applied in two ways:
    - @decorator - uses default parameters
    - @decorator(...) - uses supplied parameters

    This is useful for creating decorators that have optional configuration
    without forcing users to always use parentheses.

    Args:
        decorator_factory: A function that takes parameters and returns a
            decorator function. Should accept no arguments for default behavior.

    Returns:
        A wrapper function that can be used both as a direct decorator and
        as a decorator factory.

    Raises:
        TypeError: If used without parentheses on a non-callable object.

    Example:
        >>> @maybe_params
        ... def my_decorator(prefix=""):
        ...     def decorator(func):
        ...         @functools.wraps(func)
        ...         def wrapper(*args, **kwargs):
        ...             print(f"{prefix}Calling {func.__name__}")
        ...             return func(*args, **kwargs)
        ...         return wrapper
        ...     return decorator
        ...
        >>> @my_decorator
        ... def foo(): pass  # Uses default prefix
        ...
        >>> @my_decorator(prefix="DEBUG: ")
        ... def bar(): pass  # Uses custom prefix
    """

    @functools.wraps(decorator_factory)
    def outer(*args: Any, **kwargs: Any) -> F | Callable[[F], F]:
        """Dispatch between direct decoration and factory invocation.

        If called with a single callable argument and no kwargs, assume
        direct decoration. Otherwise, invoke the factory with the arguments.
        """
        if len(args) == 1 and not kwargs:
            target = args[0]
            if callable(target):
                # Direct decoration: @decorator
                decorator = decorator_factory()
                return decorator(target)
            raise TypeError(
                "Decorator used without parentheses must be applied to a callable"
            )
        # Factory invocation: @decorator(...)
        return decorator_factory(*args, **kwargs)

    return outer
