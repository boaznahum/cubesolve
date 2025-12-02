"""No-op celebration effect."""
from __future__ import annotations

from cube.presentation.gui.effects.BaseEffect import BaseEffect


class NoneEffect(BaseEffect):
    """No-op effect - does nothing.

    Used when celebrations are disabled or as a fallback for unsupported backends.
    """

    @property
    def name(self) -> str:
        return "none"

    def start(self) -> None:
        """Immediately complete - no celebration."""
        self._running = False

    def update(self, dt: float) -> bool:
        """Always returns False - effect is always complete."""
        return False

    def draw(self) -> None:
        """No visual output."""
        pass
