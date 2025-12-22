"""Victory spin celebration effect."""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from cube.presentation.gui.effects.BaseEffect import BaseEffect

if TYPE_CHECKING:
    from cube.application.state import ApplicationAndViewState
    from cube.presentation.gui.protocols.Renderer import Renderer


class VictorySpinEffect(BaseEffect):
    """Cube auto-rotates to show all solved faces.

    A simple but satisfying effect where the cube smoothly rotates
    to display all six faces to the user.
    """

    def __init__(
        self,
        renderer: "Renderer",
        vs: "ApplicationAndViewState",
        backend_name: str,
    ) -> None:
        super().__init__(renderer, vs, backend_name)
        self._start_alpha_x = 0.0
        self._start_alpha_y = 0.0
        self._rotations = 1.0  # Number of full rotations
        self._tilt_amount = 0.3  # Radians of tilt during spin

    @property
    def name(self) -> str:
        return "victory_spin"

    def start(self) -> None:
        """Store initial view angles."""
        super().start()
        self._start_alpha_x = self._vs.alpha_x
        self._start_alpha_y = self._vs.alpha_y

    def update(self, dt: float) -> bool:
        """Update cube rotation angles."""
        if not super().update(dt):
            # Restore original view on completion
            self._vs.alpha_x = self._start_alpha_x
            self._vs.alpha_y = self._start_alpha_y
            return False

        # Smooth ease-in-out progress
        eased = self._ease_in_out(self.progress)

        # Rotate around Y axis for the main spin
        self._vs.alpha_y = self._start_alpha_y + (2 * math.pi * self._rotations * eased)

        # Add a slight tilt on X axis for dramatic effect (rises and falls)
        tilt = math.sin(self.progress * math.pi) * self._tilt_amount
        self._vs.alpha_x = self._start_alpha_x + tilt

        return True

    def _ease_in_out(self, t: float) -> float:
        """Smooth ease-in-out function (cubic).

        Args:
            t: Progress from 0.0 to 1.0

        Returns:
            Eased value from 0.0 to 1.0
        """
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2

    def draw(self) -> None:
        """No additional drawing - effect modifies view angles directly."""
        pass

    def cleanup(self) -> None:
        """Restore original view angles."""
        self._vs.alpha_x = self._start_alpha_x
        self._vs.alpha_y = self._start_alpha_y
        super().cleanup()
