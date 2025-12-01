"""
DisplayListManager protocol definition.

This protocol defines the interface for managing compiled display lists.
"""

from typing import Protocol, Sequence, runtime_checkable

from cube.presentation.gui.types import DisplayList


@runtime_checkable
class DisplayListManager(Protocol):
    """Protocol for managing compiled display lists.

    Display lists are pre-compiled rendering commands that can be
    executed efficiently. For backends without native display list support
    (e.g., tkinter), this can store callable objects or canvas item IDs.
    """

    def create_list(self) -> DisplayList:
        """Create a new display list and return its handle.

        Returns:
            Opaque handle to the display list
        """
        ...

    def begin_compile(self, list_id: DisplayList) -> None:
        """Begin compiling rendering commands into the list.

        All subsequent rendering calls are recorded until end_compile().

        Args:
            list_id: Handle from create_list()
        """
        ...

    def end_compile(self) -> None:
        """End compilation and finalize the display list."""
        ...

    def call_list(self, list_id: DisplayList) -> None:
        """Execute a single display list.

        Args:
            list_id: Handle to execute
        """
        ...

    def call_lists(self, list_ids: Sequence[DisplayList]) -> None:
        """Execute multiple display lists in order.

        Args:
            list_ids: Sequence of handles to execute
        """
        ...

    def delete_list(self, list_id: DisplayList) -> None:
        """Delete a display list and free resources.

        Args:
            list_id: Handle to delete
        """
        ...

    def delete_lists(self, list_ids: Sequence[DisplayList]) -> None:
        """Delete multiple display lists.

        Args:
            list_ids: Sequence of handles to delete
        """
        ...
