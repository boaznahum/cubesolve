"""Backend-independent mouse event."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MouseEvent:
    """Backend-independent mouse event."""

    x: int  # X position in window coordinates
    y: int  # Y position in window coordinates
    dx: int = 0  # Delta X for drag events
    dy: int = 0  # Delta Y for drag events
    button: int = 0  # Mouse button (1=left, 2=middle, 3=right)
    modifiers: int = 0  # Modifier flags
