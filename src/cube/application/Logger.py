"""Logger implementation with environment variable overrides.

Environment Variables (override constructor parameters):
    CUBE_QUIET_ALL: Set to "1", "true", or "yes" to suppress all debug output.
    CUBE_DEBUG_ALL: Set to "1", "true", or "yes" to enable all debug output.

Example:
    # Suppress all output in tests:
    CUBE_QUIET_ALL=1 python -m pytest tests/

    # Enable verbose debugging:
    CUBE_DEBUG_ALL=1 python -m cube.main_pyglet

See Also:
    ILogger: The protocol definition in cube.utils.logger_protocol
"""
from __future__ import annotations

import os
from typing import Any, Callable

from cube.utils.logger_protocol import ILogger


def _env_bool(name: str) -> bool | None:
    """Get boolean value from environment variable, or None if not set."""
    val = os.environ.get(name, "").lower()
    if val in ("1", "true", "yes"):
        return True
    if val in ("0", "false", "no"):
        return False
    return None


class Logger(ILogger):
    """Logger with environment variable overrides.

    Implements ILogger protocol for debug output control.

    The logger supports two-level control:
    - Global: debug_all (enable all) and quiet_all (suppress all)
    - Local: debug_on parameter per call

    Environment variables override constructor parameters if set.
    """

    __slots__ = ["_debug_all", "_quiet_all"]

    def __init__(self, debug_all: bool = False, quiet_all: bool = False) -> None:
        """Initialize logger with optional environment variable overrides.

        Args:
            debug_all: Enable all debug output by default.
            quiet_all: Suppress all debug output by default.

        Environment Variables (override if set):
            CUBE_QUIET_ALL: Overrides quiet_all parameter
            CUBE_DEBUG_ALL: Overrides debug_all parameter
        """
        # Environment variables override constructor args if set
        env_quiet = _env_bool("CUBE_QUIET_ALL")
        env_debug = _env_bool("CUBE_DEBUG_ALL")

        self._quiet_all = env_quiet if env_quiet is not None else quiet_all
        self._debug_all = env_debug if env_debug is not None else debug_all

    @property
    def is_debug_all(self) -> bool:
        """Return True if debug_all mode is enabled."""
        return self._debug_all

    @property
    def quiet_all(self) -> bool:
        """Return True if quiet_all mode is enabled (suppresses all debug output)."""
        return self._quiet_all

    @quiet_all.setter
    def quiet_all(self, value: bool) -> None:
        """Set quiet_all mode."""
        self._quiet_all = value

    def is_debug(self, debug_on: bool = False) -> bool:
        """Check if debug output should happen.

        Args:
            debug_on: Local flag to enable debug for this specific call.

        Returns:
            True if debug output should happen:
            - quiet_all is False AND (debug_all is True OR debug_on is True)
        """
        if self._quiet_all:
            return False
        return self._debug_all or debug_on

    def debug_prefix(self) -> str:
        """Return the standard debug prefix."""
        return "DEBUG:"

    def debug(self, debug_on: bool, *args: Any) -> None:
        """Print debug information if allowed by flags.

        Args:
            debug_on: Local flag to enable debug for this specific call.
            *args: Arguments to print, same as print() function.

        Logic:
            - If quiet_all is True → never print
            - If debug_all is True OR debug_on is True → print
        """
        if self._quiet_all:
            return
        if self._debug_all or debug_on:
            print("DEBUG:", *args, flush=True)

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
        if self._quiet_all:
            return
        if self._debug_all or debug_on:
            print("DEBUG:", func())
