"""CubeLogger — a thin ``logging.Logger`` subclass for the cube solver.

Only two custom extensions on top of standard ``logging``:
- ``tab()`` context manager for indented debug sections
- ``makeRecord()`` override to auto-inject the current indentation

Everything else (levels, handlers, filters, hierarchy) is pure standard
``logging``.

Global debug behaviour is controlled via two flags on the **root**
``CubeLogger`` (name ``cube``):

- ``quiet_all``: suppress everything below ERROR.
- ``debug_all``: force-enable all debug output, including ``DEBUG_ALL_ONLY``
  messages that are normally hidden.

Environment variables (read once at root-logger creation time):
    CUBE_QUIET_ALL: "1"/"true"/"yes" → suppress all debug output.
    CUBE_DEBUG_ALL: "1"/"true"/"yes" → enable all debug output.
"""
from __future__ import annotations

import logging
import os
import sys
from contextlib import contextmanager
from enum import Enum
from collections.abc import Mapping
from typing import Any, Callable, Generator

from cube.utils.logging._std_logging import (
    ROOT_LOGGER_NAME,
    ColonPrefixFormatter,
    DEBUG_ALL_ONLY,
    DEBUG_SUB,
    _StreamCallbackHandler,
)

# Re-export for convenience
__all__ = ["CubeLogger", "TabExceptionMode", "setup_root_logger"]

# Type for lazy debug arguments: a value OR a callable returning another LazyArg.
LazyArg = Callable[[], "LazyArg"] | Any


class TabExceptionMode(Enum):
    """Controls how tab() behaves when an exception is propagating.

    NORMAL: Print "end: X" as usual (original behavior)
    SILENT: Don't print anything on exception
    ABORTED: Print "❌ ABORTED: X" on exception
    """
    NORMAL = "normal"
    SILENT = "silent"
    ABORTED = "aborted"


# Module-level setting for tab() exception behavior
TAB_EXCEPTION_MODE: TabExceptionMode = TabExceptionMode.SILENT


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


# ---------------------------------------------------------------------------
# CubeLogger
# ---------------------------------------------------------------------------

class CubeLogger(logging.Logger):
    """``logging.Logger`` subclass with indented-section support.

    Custom extensions:
    - ``tab()`` — context manager that indents nested log output.
    - ``makeRecord()`` — auto-injects the current ``indent`` string into
      every log record so that ``ColonPrefixFormatter`` can render it.
    - ``isEnabledFor()`` — respects the root cube logger's ``quiet_all``
      and ``debug_all`` flags.
    - ``set_cube_level(n)`` — sets verbosity threshold using sub-DEBUG levels.

    Everything else is inherited from ``logging.Logger``.
    """

    # Class-level reference to the root CubeLogger, set by setup_root_logger().
    _root_cube: CubeLogger | None = None

    def __init__(self, name: str, level: int = logging.NOTSET) -> None:
        super().__init__(name, level)
        self._indent: str = ""

        # Root-only flags (only meaningful on the root "cube" logger).
        self._quiet_all: bool = False
        self._debug_all: bool = False
        self._stream_handlers: dict[Callable[[str], None], _StreamCallbackHandler] = {}

    # --- Level overrides for global flags ---

    def isEnabledFor(self, level: int) -> bool:
        """Check if a message at *level* would be emitted.

        Adds two global overrides on top of standard behaviour:
        - ``quiet_all``: blocks everything below ERROR.
        - ``debug_all``: allows everything (overrides individual levels).
        """
        root = CubeLogger._root_cube
        if root is not None:
            if root._quiet_all and level < logging.ERROR:
                return False
            if root._debug_all:
                return True
        return super().isEnabledFor(level)

    # --- Verbose level ---

    @staticmethod
    def verbose_level(enabled: bool = False) -> int:
        """Return a logging level based on a debug flag.

        Args:
            enabled: True → ``logging.DEBUG`` (10), visible in normal debug.
                     False → internal verbose level (5), only visible with ``debug_all``.

        Usage::

            logger.log(logger.verbose_level(mouse_debug), "msg")
            logger.log_lazy(logger.verbose_level(flag), lambda: f"expensive: {x}")
        """
        return logging.DEBUG if enabled else DEBUG_ALL_ONLY

    # --- Lazy-arg logging ---

    def log_lazy(self, level: int, *args: LazyArg) -> None:
        """Log with lazy argument resolution.

        Arguments can be plain values or callables (``lambda: expensive()``).
        Callables are only evaluated if the message will actually be emitted.
        All resolved args are joined with spaces into a single message.

        Usage::

            logger.log_lazy(logging.DEBUG, "Face:", lambda: face.color)
            logger.log_lazy(logger.verbose_level(flag), lambda: f"msg")
            logger.log_lazy(CubeLogger.cube_level(3), "detail msg")
        """
        if not self.isEnabledFor(level):
            return
        resolved = [_resolve_arg(a) for a in args]
        self._log(level, " ".join(str(a) for a in resolved), ())

    # --- Record creation ---

    def makeRecord(
            self,
            name: str,
            level: int,
            fn: str,
            lno: int,
            msg: object,
            args: Any,
            exc_info: Any,
            func: str | None = None,
            extra: Mapping[str, object] | None = None,
            sinfo: str | None = None,
    ) -> logging.LogRecord:
        """Inject the current ``indent`` into every log record."""
        merged: dict[str, object] = dict(extra) if extra else {}
        merged.setdefault("indent", self._indent)
        return super().makeRecord(name, level, fn, lno, msg, args, exc_info,
                                  func, merged, sinfo)

    # --- Cube-level (sub-DEBUG verbosity) ---

    @staticmethod
    def cube_level(level: int) -> int:
        """Convert a cube verbosity level (1-5) to a logging level.

        - ``cube_level(1)`` → 10 (same as DEBUG, most important)
        - ``cube_level(2)`` → 9
        - ``cube_level(3)`` → 8
        - ``cube_level(4)`` → 7
        - ``cube_level(5)`` → 6 (most verbose)

        Usage::

            logger.log_lazy(CubeLogger.cube_level(3), "detail")
        """
        return DEBUG_SUB[level]

    def set_cube_level(self, level: int | None) -> None:
        """Set the cube-level verbosity threshold.

        Messages logged at ``cube_level(N)`` where N > threshold
        will be hidden.  ``None`` resets to DEBUG (show all).

        Usage::

            logger.set_cube_level(3)  # show levels 1-3, hide 4-5
        """
        if level is None:
            self.setLevel(logging.DEBUG)
        else:
            self.setLevel(DEBUG_SUB[level])

    # --- Global flags (root only) ---

    @property
    def quiet_all(self) -> bool:
        root = CubeLogger._root_cube
        return root._quiet_all if root is not None else False

    @quiet_all.setter
    def quiet_all(self, value: bool) -> None:
        root = CubeLogger._root_cube
        if root is not None:
            root._quiet_all = value

    @property
    def debug_all(self) -> bool:
        root = CubeLogger._root_cube
        return root._debug_all if root is not None else False

    @debug_all.setter
    def debug_all(self, value: bool) -> None:
        root = CubeLogger._root_cube
        if root is not None:
            root._debug_all = value

    # --- Stream callbacks (legacy API, backed by handlers) ---

    def add_stream(self, callback: Callable[[str], None]) -> None:
        """Register a stream callback on the root cube logger.

        Every log line produced by this logger or any child will be
        forwarded to *callback* as a formatted string.
        """
        root = CubeLogger._root_cube
        if root is None:
            return
        handler = _StreamCallbackHandler(callback)
        handler.setFormatter(ColonPrefixFormatter())
        root._stream_handlers[callback] = handler
        root.addHandler(handler)

    def remove_stream(self, callback: Callable[[str], None]) -> None:
        """Unregister a previously registered stream callback."""
        root = CubeLogger._root_cube
        if root is None:
            return
        handler = root._stream_handlers.pop(callback, None)
        if handler is not None:
            root.removeHandler(handler)

    # --- Indented sections ---

    @contextmanager
    def tab(
        self,
        headline: Callable[[], str] | str | None = None,
        char: str = '│'
    ) -> Generator[bool, None, None]:
        """Context manager for indented debug sections.

        Args:
            headline: Section title (lazy callable or string), printed on entry.
                      Only evaluated if debug is enabled.
            char: Indent character ('│' default, ' ' for blank)

        Yields:
            bool: True if debug is enabled (caller can skip expensive work)
        """
        is_enabled = self.isEnabledFor(logging.DEBUG)

        # Resolve headline string only if debug is enabled
        headline_str: str | None = None
        if is_enabled and headline:
            headline_str = headline() if callable(headline) else headline

        if headline_str:
            self.debug(f"── {headline_str} ──")

        # Save current indent and push deeper
        saved_indent = self._indent
        self._indent = f"{self._indent}{char}  "

        try:
            yield is_enabled
        finally:
            self._indent = saved_indent

            # Check if an exception is propagating
            exc_type = sys.exc_info()[0]
            has_exception = exc_type is not None

            if is_enabled and headline_str:
                if has_exception:
                    if TAB_EXCEPTION_MODE == TabExceptionMode.ABORTED:
                        self.debug(f"── ❌ ABORTED: {headline_str} ──")
                    elif TAB_EXCEPTION_MODE == TabExceptionMode.NORMAL:
                        self.debug(f"── end: {headline_str} ──")
                    # SILENT: don't print anything
                else:
                    self.debug(f"── end: {headline_str} ──")


# Register CubeLogger so that logging.getLogger() returns CubeLogger instances.
logging.setLoggerClass(CubeLogger)


# ---------------------------------------------------------------------------
# Root logger setup
# ---------------------------------------------------------------------------

def setup_root_logger(
    *,
    debug_all: bool = False,
    quiet_all: bool = False,
) -> CubeLogger:
    """Create (or reconfigure) the root ``cube`` logger.

    Call this once at application startup.  Returns the root ``CubeLogger``
    with a console handler attached.

    Args:
        debug_all: Enable all debug output by default.
        quiet_all: Suppress all debug output by default.
    """
    root: CubeLogger = logging.getLogger(ROOT_LOGGER_NAME)  # type: ignore[assignment]
    assert isinstance(root, CubeLogger), f"Expected CubeLogger, got {type(root)}"

    # Store as class-level reference for isEnabledFor() lookups.
    CubeLogger._root_cube = root

    # Apply env-var overrides.
    env_quiet = _env_bool("CUBE_QUIET_ALL")
    env_debug = _env_bool("CUBE_DEBUG_ALL")
    root._quiet_all = env_quiet if env_quiet is not None else quiet_all
    root._debug_all = env_debug if env_debug is not None else debug_all

    # Root level: allow everything through; individual loggers and
    # isEnabledFor() handle the actual gating.
    root.setLevel(logging.INFO)
    root.propagate = False

    # Remove stale handlers from previous setup_root_logger() calls
    # (e.g. when ApplicationAndViewState is recreated in tests).
    root.handlers.clear()

    # Console handler → stdout
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(ColonPrefixFormatter())
    root.addHandler(console)

    return root
