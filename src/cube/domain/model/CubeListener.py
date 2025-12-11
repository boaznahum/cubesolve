"""
CubeListener Protocol
=====================

Protocol for objects that want to be notified of cube state changes.
"""
from __future__ import annotations

from typing import Protocol


class CubeListener(Protocol):
    """Protocol for listeners that want to be notified of cube events.

    Components like the viewer can implement this protocol to receive
    notifications when the cube state changes (e.g., after reset).
    """

    def on_reset(self) -> None:
        """Called after the cube has been reset to solved state.

        This is called AFTER the cube is fully reset but BEFORE any
        subsequent operations (like scramble). Use this to reload
        textures or other state that depends on the cube being solved.
        """
        ...
