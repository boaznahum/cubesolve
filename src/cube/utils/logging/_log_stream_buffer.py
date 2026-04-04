"""Circular buffer that captures logger output with monotonic indexing.

Each line gets a unique, monotonically increasing index.  Clients track
the last index they received and can request any gap — even after
reconnection or panel close/reopen.

Thread-safe: solver threads call ``append`` while the asyncio event loop
calls ``snapshot`` / ``fetch``.
"""
from __future__ import annotations

import threading
from collections import deque
from typing import NamedTuple


class IndexedLine(NamedTuple):
    """A log line with its monotonic index."""
    idx: int
    text: str


class FetchResult(NamedTuple):
    """Result of a fetch request."""
    lines: list[IndexedLine]
    head: int          # current head index (highest index in buffer)
    truncated: bool    # True if requested lines were evicted from buffer


class LogStreamBuffer:
    """Circular buffer for logger output lines with monotonic indexing.

    Usage:
        buf = LogStreamBuffer(max_lines=500)
        logger.add_stream(buf.append)   # register with root logger

        # Snapshot (all buffered lines with indices)
        result = buf.fetch(from_index=0)

        # Incremental fetch (only new lines)
        result = buf.fetch(from_index=last_known_index)

        # Current head index (cheap, no copy)
        head = buf.head
    """

    def __init__(self, max_lines: int = 500) -> None:
        self._lines: deque[IndexedLine] = deque(maxlen=max_lines)
        self._head: int = -1  # -1 means no lines yet
        self._lock = threading.Lock()

    @property
    def head(self) -> int:
        """Current head index (-1 if empty). Thread-safe (GIL-atomic read)."""
        return self._head

    def append(self, line: str) -> None:
        """Called by the logger stream callback for every debug line."""
        with self._lock:
            self._head += 1
            self._lines.append(IndexedLine(self._head, line))

    def fetch(self, from_index: int = 0) -> FetchResult:
        """Return lines from ``from_index`` onward.

        If ``from_index`` refers to lines that have been evicted (buffer
        wrapped around), returns whatever is available and sets
        ``truncated=True``.
        """
        with self._lock:
            if not self._lines:
                return FetchResult(lines=[], head=self._head, truncated=False)

            oldest = self._lines[0].idx
            truncated = from_index < oldest

            # Collect lines with index >= from_index
            result: list[IndexedLine] = []
            for entry in self._lines:
                if entry.idx >= from_index:
                    result.append(entry)

            return FetchResult(lines=result, head=self._head, truncated=truncated)

    def snapshot(self) -> list[str]:
        """Return a copy of all buffered lines (text only, for backward compat)."""
        with self._lock:
            return [entry.text for entry in self._lines]

    def clear(self) -> None:
        """Clear the buffer."""
        with self._lock:
            self._lines.clear()
            # Don't reset _head — indices are monotonic across clears
