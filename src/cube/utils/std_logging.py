"""Standard-library logging infrastructure for the cube solver.

Provides:
- ColonPrefixFormatter: Transforms dot-separated logger names into the
  colon-separated prefix format used by solver debug output.
- WebSocketLogHandler: Forwards log records to a WebSocket session as JSON,
  scheduling the coroutine-based send safely against a running event loop.

Usage:
    import logging
    from cube.utils.std_logging import ROOT_LOGGER_NAME, ColonPrefixFormatter, WebSocketLogHandler

    # Root logger with console output
    root = logging.getLogger(ROOT_LOGGER_NAME)
    root.setLevel(logging.DEBUG)
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(ColonPrefixFormatter())
    root.addHandler(console)

    # Child logger (solver hierarchy)
    child = logging.getLogger(f"{ROOT_LOGGER_NAME}.LBL.Beginner3x3.L1Cross")
    child.debug("solving...")
    # Output: "DEBUG: LBL:Beginner3x3:L1Cross: solving..."
"""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    pass

# All solver loggers live under this namespace.
ROOT_LOGGER_NAME = "cube"


class ColonPrefixFormatter(logging.Formatter):
    """Format log records using the solver's colon-separated prefix convention.

    Standard ``logging`` uses dot-separated logger names (``cube.LBL.L1Cross``).
    This formatter converts the dotted hierarchy to the display format
    ``DEBUG: LBL:L1Cross: <message>`` that the solver debug output expects.

    The ``indent`` extra field (set by Logger.tab) is spliced into the prefix
    to reproduce the indented-section output::

        DEBUG: LBL:L1Cross: -- Processing --
        DEBUG: LBL:L1Cross:|   nested message
        DEBUG: LBL:L1Cross: -- end: Processing --
    """

    def format(self, record: logging.LogRecord) -> str:
        name = record.name

        # Strip the root namespace prefix to get the solver hierarchy.
        if name == ROOT_LOGGER_NAME:
            prefix = ""
        elif name.startswith(ROOT_LOGGER_NAME + "."):
            prefix = name[len(ROOT_LOGGER_NAME) + 1:].replace(".", ":")
        else:
            prefix = name.replace(".", ":")

        # Indentation injected by Logger.tab() via the ``extra`` dict.
        indent: str = getattr(record, "indent", "")

        if record.levelno >= logging.ERROR:
            header = "ERROR:"
        else:
            header = "DEBUG:"

        message = record.getMessage()

        if prefix:
            return f"{header} {prefix}{indent}: {message}"
        elif indent:
            return f"{header} {indent}: {message}"
        else:
            return f"{header} {message}"


class WebSocketLogHandler(logging.Handler):
    """Forward log records to a WebSocket client as JSON messages.

    This handler is completely self-contained -- it has no knowledge of solver
    internals.  It receives a *send_fn* callable at construction time and uses
    it to push each formatted log line to the client.

    The *send_fn* must be **thread-safe** (solver threads may emit log records
    from worker threads).  Typically this is ``ClientSession._send`` which
    delegates to ``WebglEventLoop.send_to`` (uses ``call_soon_threadsafe``).

    Cleanup is trivial -- just remove the handler from the root logger::

        root_logger.removeHandler(ws_handler)

    Error handling:
        If the WebSocket disconnects or the send raises, the exception is
        silently swallowed so that the solver is never interrupted by a
        logging failure.
    """

    def __init__(self, send_fn: Callable[[str], None], level: int = logging.DEBUG) -> None:
        super().__init__(level)
        self._send_fn = send_fn

    def emit(self, record: logging.LogRecord) -> None:
        try:
            line = self.format(record)
            self._send_fn(json.dumps({"type": "console_lines", "lines": [line]}))
        except Exception:
            # Degrade gracefully -- never crash the solver.
            pass


class _StreamCallbackHandler(logging.Handler):
    """Adapter that wraps a plain ``Callable[[str], None]`` as a logging.Handler.

    Used internally by ``Logger.add_stream`` / ``Logger.remove_stream`` to
    bridge the legacy stream-callback API to the standard-logging handler
    mechanism.
    """

    def __init__(self, callback: Callable[[str], None]) -> None:
        super().__init__(logging.DEBUG)
        self.callback = callback

    def emit(self, record: logging.LogRecord) -> None:
        try:
            line = self.format(record)
            self.callback(line)
        except Exception:
            pass
