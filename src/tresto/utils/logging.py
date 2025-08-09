from __future__ import annotations

from functools import wraps
from inspect import isawaitable
from typing import TYPE_CHECKING, Any

from rich.console import Console

if TYPE_CHECKING:
    from collections.abc import Callable

console = Console()


def log_exceptions[T, **P](
    types: type[Exception] | tuple[type[Exception], ...],
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to log exceptions with the console."""

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        if isawaitable(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                try:
                    return await func(*args, **kwargs)
                except types as e:
                    console.print(f"[red]Error in {func.__name__}: {e}[/red]")
                    raise

            return async_wrapper

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except types as e:
                console.print(f"[red]Error in {func.__name__}: {e}[/red]")
                raise

        return wrapper

    return decorator
