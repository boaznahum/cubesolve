"""Logger implementation that delegates to config.

The environment variable override logic is in _config.py, accessible via ConfigProtocol.
This ensures all code (including tests) uses the same logic.

Environment Variables (handled by _config.py):
    CUBE_QUIET_ALL: Set to "1", "true", or "yes" to suppress all debug output.
    CUBE_DEBUG_ALL: Set to "1", "true", or "yes" to enable all debug output.

Example:
    # Suppress all output in tests:
    CUBE_QUIET_ALL=1 python -m pytest tests/

    # Enable verbose debugging:
    CUBE_DEBUG_ALL=1 python -m cube.main_pyglet

See Also:
    ILogger: The protocol definition in cube.utils.logger_protocol
    ConfigProtocol: quiet_all and debug_all properties
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from cube.utils.logger_protocol import ILogger

if TYPE_CHECKING:
    from cube.utils.config_protocol import ConfigProtocol


class Logger(ILogger):
    """Logger that delegates to config for quiet_all/debug_all flags.

    Implements ILogger protocol for debug output control.

    The logger supports two-level control:
    - Global: debug_all (enable all) and quiet_all (suppress all) from config
    - Local: debug_on parameter per call
    """

    __slots__ = ["_config"]

    def __init__(self, config: "ConfigProtocol") -> None:
        """Initialize logger with config reference.

        Args:
            config: ConfigProtocol instance for quiet_all/debug_all flags
        """
        self._config = config

    @property
    def is_debug_all(self) -> bool:
        """Return True if debug_all mode is enabled."""
        return self._config.debug_all

    @property
    def quiet_all(self) -> bool:
        """Return True if quiet_all mode is enabled (suppresses all debug output)."""
        return self._config.quiet_all

    @quiet_all.setter
    def quiet_all(self, value: bool) -> None:
        """Set quiet_all mode."""
        self._config.quiet_all = value

    def is_debug(self, debug_on: bool = False) -> bool:
        """Check if debug output should happen.

        Args:
            debug_on: Local flag to enable debug for this specific call.

        Returns:
            True if debug output should happen:
            - quiet_all is False AND (debug_all is True OR debug_on is True)
        """
        if self._config.quiet_all:
            return False
        return self._config.debug_all or debug_on

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
        if self._config.quiet_all:
            return
        if self._config.debug_all or debug_on:
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
        if self._config.quiet_all:
            return
        if self._config.debug_all or debug_on:
            print("DEBUG:", func())
