from typing import Protocol, runtime_checkable

from rich.console import RenderableType


@runtime_checkable
class RichFormattable(Protocol):
    """A protocol for objects that can be formatted."""

    def format(self) -> RenderableType:
        """Format the object."""