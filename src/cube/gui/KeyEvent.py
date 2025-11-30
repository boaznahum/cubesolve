"""Backend-independent keyboard event."""

from dataclasses import dataclass


@dataclass(frozen=True)
class KeyEvent:
    """Backend-independent keyboard event."""

    symbol: int  # Key code (use Keys constants)
    modifiers: int  # Modifier flags (use Modifiers constants)
    char: str | None = None  # Character if printable key
