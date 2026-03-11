"""Circular buffer that captures logger output.

Just a buffer — stores up to ``max_lines`` debug lines.
The Logger's stream callback mechanism handles routing.
"""
from __future__ import annotations

from collections import deque


class LogStreamBuffer:
    """Circular buffer for logger output lines.

    Usage:
        buf = LogStreamBuffer(max_lines=500)
        logger.add_stream(buf.append)   # register with root logger
        lines = buf.snapshot()          # get all buffered lines
    """

    def __init__(self, max_lines: int = 500) -> None:
        self._lines: deque[str] = deque(maxlen=max_lines)

    def append(self, line: str) -> None:
        """Called by the logger stream callback for every debug line."""
        self._lines.append(line)

    def snapshot(self) -> list[str]:
        """Return a copy of all buffered lines."""
        return list(self._lines)

    def clear(self) -> None:
        """Clear the buffer."""
        self._lines.clear()
