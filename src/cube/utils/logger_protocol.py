"""Logger protocol for dependency inversion.

Domain imports this protocol from utils (foundation layer).
Application layer provides the Logger implementation.

See Also:
    Logger: The concrete implementation in cube.application.Logger
    PrefixedLogger: Wrapper that adds prefix to messages
"""
from __future__ import annotations

from typing import Any, Callable, ContextManager, Protocol, runtime_checkable

# Type for debug flag: static bool, dynamic callable, or None (inherit/ignore)
DebugFlagType = bool | Callable[[], bool] | None


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

    def is_debug(self, debug_on: bool | None = None) -> bool:
        """Check if debug output should happen.

        Args:
            debug_on: Local flag to enable debug for this specific call.
                      If None, treated as False for root logger.

        Returns:
            True if debug output should happen:
            - quiet_all is False AND (debug_all is True OR debug_on is True)
        """
        ...

    def debug_prefix(self) -> str:
        """Return the standard debug prefix."""
        ...

    def debug(self, debug_on: bool | None, *args: Any) -> None:
        """Print debug information if allowed by flags.

        Args:
            debug_on: Local flag to enable debug for this specific call.
                      If None, uses logger's default (False for root, debug_flag for prefixed).
            *args: Arguments to print, same as print() function.

        Logic:
            - If quiet_all is True → never print
            - If debug_all is True OR debug_on is True → print
        """
        ...

    def debug_lazy(self, debug_on: bool | None, func: Callable[[], Any]) -> None:
        """Print debug information with lazy evaluation.

        The func is only called if we're actually going to print,
        avoiding expensive computation when debug is disabled.

        Args:
            debug_on: Local flag to enable debug for this specific call.
                      If None, uses logger's default.
            func: Callable that returns the message to print.

        Logic:
            - If quiet_all is True → never print, func not called
            - If debug_all is True OR debug_on is True → call func and print
        """
        ...

    def with_prefix(self, prefix: str, debug_flag: DebugFlagType = None) -> "ILogger":
        """Create a new logger that prepends prefix to all messages.

        Args:
            prefix: String to prepend to all messages (colon added automatically).
            debug_flag: Debug control for the new logger:
                - bool: Static True/False
                - Callable[[], bool]: Dynamic evaluation (e.g., lambda: self._is_debug_enabled)
                - None: Inherit from parent or use caller-provided debug_on

        Returns:
            New ILogger instance that delegates to this logger with prefix.

        Example:
            solver_logger = root_logger.with_prefix("Solver:Beginner", lambda: self._is_debug_enabled)
            step_logger = solver_logger.with_prefix("L1Cross")  # inherits debug_flag
            step_logger.debug(None, "solving...")
            # Output: "DEBUG: Solver:Beginner:L1Cross: solving..."
        """
        ...


@runtime_checkable
class IPrefixLogger(ILogger, Protocol):
    """Logger with mutable prefix and indented sections support.

    Use this when the prefix isn't known at construction time but will be set later.
    Extends ILogger with set_prefix() and tab() methods.

    Example:
        logger: IPrefixLogger = MutablePrefixLogger(parent_logger)
        logger.set_prefix("MyComponent")

        with logger.tab(lambda: "Processing slice 1") as dbg:
            logger.debug(None, "nested message")
            with logger.tab(lambda: "Source face"):
                logger.debug(None, "deeper nested")

        # Output:
        # ── Processing slice 1 ──
        # │  nested message
        # │  ── Source face ──
        # │  │  deeper nested
    """

    def set_prefix(self, prefix: str) -> None:
        """Set the prefix for this logger.

        Args:
            prefix: The prefix to prepend to all debug messages.
        """
        ...

    def tab(
        self,
        headline: Callable[[], str] | str | None = None,
        char: str = '│'
    ) -> ContextManager[bool]:
        """Context manager for indented debug sections.

        Creates a visually nested section in debug output. All debug calls
        within the context are indented with the specified character.

        Args:
            headline: Section title, printed on entry. Can be:
                - Callable (lazy): Only evaluated if debug is enabled
                - str: Static string
                - None: No headline printed
            char: Indent character ('│' default, ' ' for blank indent)

        Yields:
            bool: True if debug is enabled (caller can skip expensive work)

        Example:
            with logger.tab(lambda: f"Slice {i}") as dbg:
                if dbg:
                    expensive = compute()
                logger.debug(None, "processing...")
        """
        ...
