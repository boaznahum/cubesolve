"""Logger protocol for dependency inversion.

Domain imports this protocol from utils (foundation layer).
Application layer provides the Logger implementation.

See Also:
    Logger: The concrete implementation in cube.application.Logger
"""
from __future__ import annotations

from typing import Any, Callable, Protocol, runtime_checkable


@runtime_checkable
class ILogger(Protocol):
    """Logger protocol - provides debug output control.

    This protocol defines the interface for debug/logging operations.
    Access via service provider: cube.sp.logger

    The logger supports two-level control:
    - Global: debug_all (enable all) and quiet_all (suppress all)
    - Local: debug_on parameter per call

    Logic:
        - If quiet_all is True → never output
        - If debug_all is True OR debug_on is True → output
    """

    @property
    def is_debug_all(self) -> bool:
        """Return True if debug_all mode is enabled."""
        ...

    @property
    def quiet_all(self) -> bool:
        """Return True if quiet_all mode is enabled (suppresses all debug output)."""
        ...

    @quiet_all.setter
    def quiet_all(self, value: bool) -> None:
        """Set quiet_all mode."""
        ...

    def is_debug(self, debug_on: bool = False) -> bool:
        """Check if debug output should happen.

        Args:
            debug_on: Local flag to enable debug for this specific call.

        Returns:
            True if debug output should happen:
            - quiet_all is False AND (debug_all is True OR debug_on is True)
        """
        ...

    def debug_prefix(self) -> str:
        """Return the standard debug prefix."""
        ...

    def debug(self, debug_on: bool, *args: Any) -> None:
        """Print debug information if allowed by flags.

        Args:
            debug_on: Local flag to enable debug for this specific call.
            *args: Arguments to print, same as print() function.

        Logic:
            - If quiet_all is True → never print
            - If debug_all is True OR debug_on is True → print
        """
        ...

    def debug_lazy(self, debug_on: bool, func: Callable[[], Any]) -> None:
        """Print debug information with lazy evaluation.

        The func is only called if we're actually going to print,
        avoiding expensive computation when debug is disabled.

        Args:
            debug_on: Local flag to enable debug for this specific call.
            func: Callable that returns the message to print.

        Logic:
            - If quiet_all is True → never print, func not called
            - If debug_all is True OR debug_on is True → call func and print
        """
        ...
