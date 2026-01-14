"""Prefixed logger that wraps ILogger with automatic prefix and debug flag."""
from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Callable, Generator

from cube.utils.logger_protocol import DebugFlagType, ILogger

if TYPE_CHECKING:
    pass


class PrefixedLogger(ILogger):
    """Logger wrapper that adds prefix and optional debug flag.

    Delegates all operations to the wrapped logger, prepending prefix
    to all output and optionally using a debug flag for the debug_on parameter.

    Supports chaining: root.with_prefix("A").with_prefix("B") -> "A:B:"

    Example:
        solver_logger = root_logger.with_prefix("Solver:Beginner", lambda: self._is_debug_enabled)
        step_logger = solver_logger.with_prefix("L1Cross")  # inherits debug_flag
        step_logger.debug(None, "solving...")
        # Output: "DEBUG: Solver:Beginner:L1Cross: solving..."
    """

    __slots__ = ["_delegate", "_prefix", "_debug_flag", "_level"]

    def __init__(
        self,
        delegate: ILogger,
        prefix: str,
        debug_flag: DebugFlagType = None
    ) -> None:
        """Initialize prefixed logger.

        Args:
            delegate: The logger to wrap and delegate to.
            prefix: Prefix to prepend (colon added automatically in output).
            debug_flag: Debug control - bool, callable returning bool, or None.
        """
        self._delegate = delegate
        self._prefix = prefix
        self._debug_flag = debug_flag
        self._level: int | None = None  # Inherit from parent by default

    def _resolve_debug_flag(self, debug_on: bool | None) -> bool:
        """Resolve the effective debug_on value.

        Priority:
        1. If debug_on is explicitly True/False, use it
        2. If self._debug_flag is set, evaluate and use it
        3. Return False as fallback
        """
        if debug_on is not None:
            return debug_on

        if self._debug_flag is None:
            return False

        if callable(self._debug_flag):
            return bool(self._debug_flag())

        return self._debug_flag

    @property
    def is_debug_all(self) -> bool:
        """Delegate to wrapped logger."""
        return self._delegate.is_debug_all

    @property
    def quiet_all(self) -> bool:
        """Delegate to wrapped logger."""
        return self._delegate.quiet_all

    @quiet_all.setter
    def quiet_all(self, value: bool) -> None:
        """Delegate to wrapped logger."""
        self._delegate.quiet_all = value

    def is_debug(self, debug_on: bool | None = None, *, level: int | None = None) -> bool:
        """Check if debug output should happen.

        Args:
            debug_on: Override debug flag. If None, uses this logger's debug_flag.
            level: Optional debug level. If set, also checks level <= threshold.
        """
        # Local level check first
        if level is not None and self._level is not None and level > self._level:
            return False
        effective_debug = self._resolve_debug_flag(debug_on)
        # Delegate level check if we don't have local level
        if level is not None and self._level is None:
            return self._delegate.is_debug(effective_debug, level=level)
        return self._delegate.is_debug(effective_debug)

    def debug_prefix(self) -> str:
        """Return the combined prefix."""
        return f"{self._delegate.debug_prefix()} {self._prefix}:"

    def debug(self, debug_on: bool | None, *args: Any, level: int | None = None) -> None:
        """Print debug information with prefix.

        Args:
            debug_on: Override debug flag. If None, uses this logger's debug_flag.
            *args: Arguments to print.
            level: Optional debug level. If set, also checks level <= threshold.
        """
        if not self.is_debug(debug_on, level=level):
            return
        # Print directly - we already did all checks in is_debug()
        print("DEBUG:", f"{self._prefix}:", *args, flush=True)

    def debug_lazy(self, debug_on: bool | None, func: Callable[[], Any], *, level: int | None = None) -> None:
        """Print debug with lazy evaluation and prefix.

        Args:
            debug_on: Override debug flag. If None, uses this logger's debug_flag.
            func: Callable that returns the message to print.
            level: Optional debug level. If set, also checks level <= threshold.
        """
        if not self.is_debug(debug_on, level=level):
            return
        # Print directly - we already did all checks in is_debug()
        print("DEBUG:", f"{self._prefix}:", func(), flush=True)

    def with_prefix(self, prefix: str, debug_flag: DebugFlagType = None) -> ILogger:
        """Create nested prefixed logger.

        Chains prefixes: self.prefix + ":" + new_prefix
        Inherits debug_flag if not specified.

        Args:
            prefix: Additional prefix to add.
            debug_flag: Debug control for the new logger, or None to inherit.

        Returns:
            New PrefixedLogger with combined prefix.
        """
        combined_prefix = f"{self._prefix}:{prefix}"
        effective_flag = debug_flag if debug_flag is not None else self._debug_flag
        return PrefixedLogger(self._delegate, combined_prefix, effective_flag)

    # --- Level-based debug ---

    def set_level(self, level: int | None) -> None:
        """Set the debug level threshold for this logger.

        Args:
            level: Threshold (messages with level <= threshold are shown).
                   None means inherit from parent.
        """
        self._level = level


class MutablePrefixLogger(ILogger):
    """Logger wrapper with mutable prefix and indented sections support.

    Use this when the prefix isn't known at construction time but will be set later.
    Supports indented sections via tab() context manager.

    Example:
        logger = MutablePrefixLogger(parent_logger)
        logger.set_prefix("MyComponent")

        with logger.tab(lambda: "Processing slice 1"):
            logger.debug(None, "nested message")
            with logger.tab(lambda: "Source face"):
                logger.debug(None, "deeper nested")

        # Output:
        # ── Processing slice 1 ──
        # │  nested message
        # │  ── Source face ──
        # │  │  deeper nested
    """

    __slots__ = ["_delegate", "_base_prefix", "_prefix", "_level"]

    def __init__(self, delegate: ILogger) -> None:
        """Initialize with parent logger and no prefix.

        Args:
            delegate: The parent logger to wrap.
        """
        self._delegate = delegate
        self._base_prefix: str = ""  # Component name without formatting
        self._prefix: str = ""       # Full leader: component + ": " + indent
        self._level: int | None = None  # Inherit from parent by default

    def set_prefix(self, prefix: str) -> None:
        """Set the prefix for this logger.

        Args:
            prefix: The prefix to prepend to all debug messages.
        """
        self._base_prefix = prefix
        self._prefix = f"{prefix}: "

    @contextmanager
    def tab(
        self,
        headline: Callable[[], str] | str | None = None,
        char: str = '│'
    ) -> Generator[bool, None, None]:
        """Context manager for indented debug sections.

        Args:
            headline: Section title (lazy callable or string), printed on entry
            char: Indent character ('│' default, ' ' for blank)

        Yields:
            bool: True if debug is enabled (caller can skip expensive work)
        """
        # Check if debug is enabled
        is_enabled = self._delegate.is_debug(None)

        # Resolve headline string (for both start and end messages)
        headline_str: str | None = None
        if headline:
            headline_str = headline() if callable(headline) else headline

        if is_enabled and headline_str:
            # Print headline with current prefix
            self._delegate.debug(None, f"{self._prefix}── {headline_str} ──")

        # Save current prefix and add indent
        saved_prefix = self._prefix
        self._prefix = f"{self._prefix}{char}  "

        try:
            yield is_enabled
        finally:
            # Restore prefix
            self._prefix = saved_prefix

            # Print end message
            if is_enabled and headline_str:
                self._delegate.debug(None, f"{self._prefix}── end: {headline_str} ──")

    @property
    def is_debug_all(self) -> bool:
        """Delegate to wrapped logger."""
        return self._delegate.is_debug_all

    @property
    def quiet_all(self) -> bool:
        """Delegate to wrapped logger."""
        return self._delegate.quiet_all

    @quiet_all.setter
    def quiet_all(self, value: bool) -> None:
        """Delegate to wrapped logger."""
        self._delegate.quiet_all = value

    def is_debug(self, debug_on: bool | None = None, *, level: int | None = None) -> bool:
        """Check if debug output should happen."""
        # Local level check first
        if level is not None and self._level is not None and level > self._level:
            return False
        # Delegate level check if we don't have local level
        if level is not None and self._level is None:
            return self._delegate.is_debug(debug_on, level=level)
        return self._delegate.is_debug(debug_on)

    def debug_prefix(self) -> str:
        """Return the combined prefix."""
        if self._base_prefix:
            return f"{self._delegate.debug_prefix()} {self._base_prefix}:"
        return self._delegate.debug_prefix()

    def debug(self, debug_on: bool | None, *args: Any, level: int | None = None) -> None:
        """Print debug information with prefix and indentation."""
        if not self.is_debug(debug_on, level=level):
            return
        # Print directly - we already did all checks in is_debug()
        if self._prefix:
            print("DEBUG:", self._prefix, *args, flush=True)
        else:
            print("DEBUG:", *args, flush=True)

    def debug_lazy(self, debug_on: bool | None, func: Callable[[], Any], *, level: int | None = None) -> None:
        """Print debug with lazy evaluation, prefix and indentation."""
        if not self.is_debug(debug_on, level=level):
            return
        # Print directly - we already did all checks in is_debug()
        if self._prefix:
            print("DEBUG:", self._prefix, func(), flush=True)
        else:
            print("DEBUG:", func(), flush=True)

    def with_prefix(self, prefix: str, debug_flag: DebugFlagType = None) -> ILogger:
        """Create nested prefixed logger.

        If this logger has a prefix, chains them. Otherwise just uses the new prefix.
        """
        if self._base_prefix:
            combined = f"{self._base_prefix}:{prefix}"
        else:
            combined = prefix
        return PrefixedLogger(self._delegate, combined, debug_flag)

    # --- Level-based debug ---

    def set_level(self, level: int | None) -> None:
        """Set the debug level threshold for this logger.

        Args:
            level: Threshold (messages with level <= threshold are shown).
                   None means inherit from parent.
        """
        self._level = level
