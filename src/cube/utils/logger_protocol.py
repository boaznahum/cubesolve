"""Logger protocol for dependency inversion.

Domain imports this protocol from utils (foundation layer).
Application layer provides the Logger implementation.

See Also:
    Logger: The unified implementation in cube.utils.prefixed_logger
"""
from __future__ import annotations

from typing import Any, Callable, ContextManager, Protocol, TypeAlias, runtime_checkable

# Type for debug flag: static bool, dynamic callable, or None (inherit/ignore)
DebugFlagType = bool | Callable[[], bool] | None

# Recursive type: a value OR a callable that returns another LazyArg.
# Allows lazy evaluation of debug arguments - callables are only invoked if debug is enabled.
LazyArg: TypeAlias = "Callable[[], LazyArg] | Any"


@runtime_checkable
class ILogger(Protocol):
    """Logger protocol - provides debug output control with prefix and indentation.

    This protocol defines the interface for debug/logging operations.
    Access via service provider: cube.sp.logger

    The logger supports two-level control:
    - Global: debug_all (enable all) and quiet_all (suppress all)
    - Local: debug_on parameter per call

    Logic:
        - If quiet_all is True → never output
        - If debug_all is True OR debug_on is True → output

    Example:
        logger = cube.sp.logger.with_prefix("Solver", lambda: self._is_debug_enabled)
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

    def is_debug(self, debug_on: bool | None = None, *, level: int | None = None) -> bool:
        """Check if debug output should happen.

        Args:
            debug_on: Local flag to enable debug for this specific call.
                      If None, treated as False for root logger.
            level: Optional debug level. If set, also checks level <= threshold.

        Returns:
            True if debug output should happen:
            - quiet_all is False AND (debug_all is True OR debug_on is True)
            - AND (level is None OR level <= threshold)
        """
        ...

    def debug_prefix(self) -> str:
        """Return the standard debug prefix."""
        ...

    def debug(self, debug_on: bool | None, *args: LazyArg, level: int | None = None) -> None:
        """Print debug information if allowed by flags.

        Args:
            debug_on: Local flag to enable debug for this specific call.
                      If None, uses logger's default (False for root, debug_flag for prefixed).
            *args: Arguments to print. Can be regular values or Callable[[], Any]
                   for lazy evaluation. Callables are resolved recursively only
                   when debug output is enabled, avoiding expensive computation
                   when debugging is off.
            level: Optional debug level. If set, also checks level <= threshold.

        Logic:
            - If quiet_all is True → never print
            - If level > threshold → never print
            - If debug_all is True OR debug_on is True → resolve callables and print

        Example:
            # Lazy evaluation - lambda only called if debug is on
            logger.debug(None, "Result:", lambda: expensive_computation())

            # Mix static and lazy args
            logger.debug(None, "Part", part_num, "colors:", lambda: part.colors_id)
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

    # --- Level-based debug ---

    def set_level(self, level: int | None) -> None:
        """Set the debug level threshold for this logger.

        Args:
            level: Debug level threshold (1-5 typical). Only messages with
                   level <= threshold are output. None means no level filtering
                   (all levels pass if debug is otherwise enabled).

        Example:
            logger.set_level(3)  # Only show level 1, 2, 3
            logger.debug(None, "shown", level=2)   # level 2 <= 3, shown
            logger.debug(None, "hidden", level=5)  # level 5 > 3, hidden
        """
        ...

    # --- Prefix and indentation ---

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

