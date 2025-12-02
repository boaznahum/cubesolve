"""Combo celebration effect - combines multiple effects."""
from __future__ import annotations

from typing import TYPE_CHECKING

from cube.presentation.gui.effects.BaseEffect import BaseEffect
from cube.presentation.gui.effects.effects.ConfettiEffect import ConfettiEffect
from cube.presentation.gui.effects.effects.VictorySpinEffect import VictorySpinEffect
from cube.presentation.gui.effects.effects.SparkleEffect import SparkleEffect

if TYPE_CHECKING:
    from cube.presentation.gui.protocols.Renderer import Renderer
    from cube.application.state import ApplicationAndViewState


class ComboEffect(BaseEffect):
    """Combination of multiple celebration effects.

    Runs confetti, victory spin, and sparkle simultaneously
    for maximum celebration impact!
    """

    def __init__(
        self,
        renderer: "Renderer",
        vs: "ApplicationAndViewState",
        backend_name: str,
    ) -> None:
        super().__init__(renderer, vs, backend_name)
        # Create sub-effects
        self._confetti = ConfettiEffect(renderer, vs, backend_name)
        self._victory_spin = VictorySpinEffect(renderer, vs, backend_name)
        self._sparkle = SparkleEffect(renderer, vs, backend_name)

    @property
    def name(self) -> str:
        return "combo"

    def start(self) -> None:
        """Start all sub-effects."""
        super().start()
        self._confetti.start()
        self._victory_spin.start()
        self._sparkle.start()

    def update(self, dt: float) -> bool:
        """Update all sub-effects."""
        if not super().update(dt):
            return False

        # Update all sub-effects
        self._confetti.update(dt)
        self._victory_spin.update(dt)
        self._sparkle.update(dt)

        return True

    def draw(self) -> None:
        """Draw all sub-effects."""
        # Draw in order: sparkle (on cube), confetti (particles), glow would go here
        self._sparkle.draw()
        self._confetti.draw()
        # Victory spin modifies view angles, doesn't draw anything

    def cleanup(self) -> None:
        """Clean up all sub-effects."""
        self._confetti.cleanup()
        self._victory_spin.cleanup()
        self._sparkle.cleanup()
        super().cleanup()
