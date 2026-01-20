"""Unified Logger implementation with prefix chaining and level-based filtering.

All logging functionality consolidated into a single Logger class:
- Root logger owns quiet_all/debug_all (set delegate=None)
- Child loggers share root's state via reference
- Prefix chaining via with_prefix()
- Mutable prefix via set_prefix()
- Level-based filtering via set_level()
- Indented sections via tab()

Environment Variables (for root logger):
    CUBE_QUIET_ALL: Set to "1", "true", or "yes" to suppress all debug output.
    CUBE_DEBUG_ALL: Set to "1", "true", or "yes" to enable all debug output.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Callable, Generator

from typing_extensions import deprecated

from cube.utils.logger_protocol import DebugFlagType, ILogger, LazyArg

if TYPE_CHECKING:
    pass


def _env_bool(name: str) -> bool | None:
    """Get boolean value from environment variable, or None if not set."""
    val = os.environ.get(name, "").lower()
    if val in ("1", "true", "yes"):
        return True
    if val in ("0", "false", "no"):
        return False
    return None


def _resolve_arg(arg: LazyArg, depth: int = 0) -> Any:
    """Recursively resolve callables until a non-callable value.

    Args:
        arg: Value or callable to resolve.
        depth: Current recursion depth (prevents infinite loops).

    Returns:
        The resolved non-callable value.

    Raises:
        RecursionError: If callable resolution exceeds max depth (10).
    """
    if depth > 10:
        raise RecursionError(
            "LazyArg resolution exceeded max depth (10). "
            "Possible infinite loop in callable chain."
        )
    if callable(arg):
        return _resolve_arg(arg(), depth + 1)
    return arg


class Logger(ILogger):
    """Unified logger with prefix chaining, debug flags, and level filtering.

    Can be used as:
    - Root logger: delegate=None, owns quiet_all/debug_all state
    - Child logger: delegate=parent, shares root's state via _root reference

    Supports:
    - Prefix chaining: root.with_prefix("A").with_prefix("B") -> "A:B:"
    - Mutable prefix: set_prefix() for dynamic prefix changes
    - Debug flag callback: evaluated on each debug() call
    - Level filtering: set_level(N), messages with level > N are hidden
    - Indented sections: tab() context manager

    Example:
        # Root logger (from ApplicationAndViewState)
        root = Logger()  # delegate=None -> root

        # Solver creates prefixed logger with debug_flag callback
        solver_log = root.with_prefix("Solver:LBL", lambda: self._is_debug_enabled)

        # Element chains further, inheriting debug_flag
        step_log = solver_log.with_prefix("L1Cross")

        # Usage
        step_log.debug(None, "solving...")  # Uses inherited debug_flag
        # Output: "DEBUG: Solver:LBL:L1Cross: solving..."

        # Level filtering
        step_log.set_level(3)
        step_log.debug(None, "verbose", level=5)  # Hidden: 5 > 3
    """

    __slots__ = ["_delegate", "_root", "_prefix", "_debug_flag", "_level", "_quiet_all", "_debug_all"]

    def __init__(
        self,
        delegate: ILogger | None = None,
        prefix: str = "",
        debug_flag: DebugFlagType = None,
        *,
        debug_all: bool = False,
        quiet_all: bool = False,
    ) -> None:
        """Initialize logger.

        Args:
            delegate: Parent logger to delegate to. None = root logger.
            prefix: Prefix for this logger's messages.
            debug_flag: Debug control - bool, callable returning bool, or None.
            debug_all: (Root only) Enable all debug output by default.
            quiet_all: (Root only) Suppress all debug output by default.
        """
        self._delegate = delegate
        self._prefix = prefix
        self._level: int | None = None

        if delegate is None:
            # Root logger: no debug_flag inheritance
            self._debug_flag = debug_flag
        else:
            # Child logger: inherit debug_flag if not specified
            if debug_flag is not None:
                self._debug_flag = debug_flag
            else:
                self._debug_flag = getattr(delegate, "_debug_flag", None)

        if delegate is None:
            # Root logger: owns quiet_all/debug_all, apply env overrides
            env_quiet = _env_bool("CUBE_QUIET_ALL")
            env_debug = _env_bool("CUBE_DEBUG_ALL")
            self._quiet_all = env_quiet if env_quiet is not None else quiet_all
            self._debug_all = env_debug if env_debug is not None else debug_all
            self._root: Logger = self
        else:
            # Child logger: shares root's state
            # Access _root from delegate (works for Logger, may need cast for other ILogger)
            self._root = getattr(delegate, "_root", self)  # type: ignore[assignment]
            self._quiet_all = False  # Not used, but slot must be initialized
            self._debug_all = False  # Not used, but slot must be initialized

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

    # --- Properties ---

    @property
    def is_debug_all(self) -> bool:
        """Return True if debug_all mode is enabled (from root)."""
        return self._root._debug_all

    @property
    def quiet_all(self) -> bool:
        """Return True if quiet_all mode is enabled (from root)."""
        return self._root._quiet_all

    @quiet_all.setter
    def quiet_all(self, value: bool) -> None:
        """Set quiet_all mode on root logger."""
        self._root._quiet_all = value

    # --- Debug methods ---

    def is_debug(self, debug_on: bool | None = None, *, level: int | None = None) -> bool:
        """Check if debug output should happen.

        Args:
            debug_on: Override debug flag. If None, uses this logger's debug_flag.
            level: Optional debug level. If set, also checks level <= threshold.
        """
        # Root's quiet_all always wins
        if self._root._quiet_all:
            return False

        # Level check (local level takes precedence)
        if level is not None and self._level is not None and level > self._level:
            return False

        # Resolve debug_on using debug_flag
        effective_debug = self._resolve_debug_flag(debug_on)

        # Check parent's level if we don't have local level
        if level is not None and self._level is None and self._delegate is not None:
            return self._delegate.is_debug(effective_debug, level=level)

        # Root's debug_all or effective debug_on
        return self._root._debug_all or effective_debug

    def debug_prefix(self) -> str:
        """Return the combined prefix for output."""
        if self._delegate is not None and self._prefix:
            return f"{self._delegate.debug_prefix()} {self._prefix}:"
        elif self._prefix:
            return f"DEBUG: {self._prefix}:"
        return "DEBUG:"

    def debug(self, debug_on: bool | None, *args: LazyArg, level: int | None = None) -> None:
        """Print debug information with prefix.

        Args:
            debug_on: Override debug flag. If None, uses this logger's debug_flag.
            *args: Arguments to print. Can be regular values or Callable[[], Any]
                   for lazy evaluation. Callables are resolved recursively.
            level: Optional debug level. If set, also checks level <= threshold.
        """
        if not self.is_debug(debug_on, level=level):
            return
        # Resolve any callables in args (lazy evaluation)
        resolved_args = [_resolve_arg(a) for a in args]
        # Print directly with prefix
        if self._prefix:
            print("DEBUG:", f"{self._prefix}:", *resolved_args, flush=True)
        else:

            print("DEBUG:", *resolved_args, flush=True)

    @deprecated("Use debug() with callable args instead: debug(None, lambda: value)")
    def debug_lazy(self, debug_on: bool | None, func: Callable[[], Any], *, level: int | None = None) -> None:
        """Print debug with lazy evaluation.

        .. deprecated::
            Use debug() with callable args instead.

        Args:
            debug_on: Override debug flag. If None, uses this logger's debug_flag.
            func: Callable that returns the message to print.
            level: Optional debug level. If set, also checks level <= threshold.
        """
        if not self.is_debug(debug_on, level=level):
            return
        # Print directly with prefix
        if self._prefix:
            print("DEBUG:", f"{self._prefix}:", func(), flush=True)
        else:
            print("DEBUG:", func(), flush=True)

    # --- Prefix operations ---

    def set_prefix(self, prefix: str) -> None:
        """Set/change the prefix for this logger.

        Args:
            prefix: New prefix to use.
        """
        self._prefix = prefix

    def with_prefix(self, prefix: str, debug_flag: DebugFlagType = None) -> "Logger":
        """Create child logger with chained prefix.

        Chains prefixes: self.prefix + ":" + new_prefix
        Inherits debug_flag if not specified.

        Args:
            prefix: Additional prefix to add.
            debug_flag: Debug control for the new logger, or None to inherit.

        Returns:
            New Logger with combined prefix.
        """
        if self._prefix:
            combined_prefix = f"{self._prefix}:{prefix}"
        else:
            combined_prefix = prefix
        effective_flag = debug_flag if debug_flag is not None else self._debug_flag
        return Logger(delegate=self, prefix=combined_prefix, debug_flag=effective_flag)

    # --- Level operations ---

    def set_level(self, level: int | None) -> None:
        """Set the debug level threshold for this logger.

        Args:
            level: Threshold (messages with level <= threshold are shown).
                   None means inherit from parent or no filtering.
        """
        self._level = level

    # --- Indented sections ---

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
        is_enabled = self.is_debug(None)

        # Resolve headline string (for both start and end messages)
        headline_str: str | None = None
        if headline:
            headline_str = headline() if callable(headline) else headline

        if is_enabled and headline_str:
            # Print headline with current prefix
            if self._prefix:
                print("DEBUG:", f"{self._prefix}:", f"── {headline_str} ──", flush=True)
            else:
                print("DEBUG:", f"── {headline_str} ──", flush=True)

        # Save current prefix and add indent
        saved_prefix = self._prefix
        if self._prefix:
            self._prefix = f"{self._prefix}{char}  "
        else:
            self._prefix = f"{char}  "

        try:
            yield is_enabled
        finally:
            # Restore prefix
            self._prefix = saved_prefix

            # Print end message
            if is_enabled and headline_str:
                if self._prefix:
                    print("DEBUG:", f"{self._prefix}:", f"── end: {headline_str} ──", flush=True)
                else:
                    print("DEBUG:", f"── end: {headline_str} ──", flush=True)


