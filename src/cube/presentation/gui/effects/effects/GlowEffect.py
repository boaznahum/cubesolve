"""Glow/pulse celebration effect."""
from __future__ import annotations

from typing import TYPE_CHECKING

from cube.presentation.gui.effects.BaseEffect import BaseEffect

if TYPE_CHECKING:
    from cube.application.state import ApplicationAndViewState
    from cube.presentation.gui.protocols.Renderer import Renderer


class GlowEffect(BaseEffect):
    """Cube pulses with a glowing aura effect.

    Creates expanding rings/halos around the cube that pulse
    to simulate a glowing celebration effect.
    """

    # Glow colors (warm golden glow)
    GLOW_COLORS = [
        (255, 255, 100),  # Yellow
        (255, 200, 50),   # Gold
        (255, 150, 0),    # Orange
    ]

    def __init__(
        self,
        renderer: "Renderer",
        vs: "ApplicationAndViewState",
        backend_name: str,
    ) -> None:
        super().__init__(renderer, vs, backend_name)
        self._pulse_frequency = 3.0  # pulses per second
        self._num_rings = 3
        self._cube_size = 55.0  # slightly larger than cube
        self._max_expansion = 30.0  # how far rings expand

    @property
    def name(self) -> str:
        return "glow"

    def start(self) -> None:
        """Initialize the glow effect."""
        super().start()

    def update(self, dt: float) -> bool:
        """Update glow state."""
        return super().update(dt)

    def draw(self) -> None:
        """Draw pulsing glow rings around the cube."""
        shapes = self._renderer.shapes

        # Calculate pulse phase (0 to 1, repeating)
        pulse_phase = (self._elapsed * self._pulse_frequency) % 1.0

        # Draw expanding rings on each face
        for ring_idx in range(self._num_rings):
            # Stagger ring phases
            ring_phase = (pulse_phase + ring_idx / self._num_rings) % 1.0

            # Ring expands outward and fades
            expansion = ring_phase * self._max_expansion
            # Fade out as ring expands (bright at start, dim at end)
            brightness = 1.0 - ring_phase

            if brightness < 0.1:
                continue

            # Pick color based on ring index
            base_color = self.GLOW_COLORS[ring_idx % len(self.GLOW_COLORS)]
            r = int(base_color[0] * brightness)
            g = int(base_color[1] * brightness)
            b = int(base_color[2] * brightness)

            size = self._cube_size + expansion

            # Draw glow quads on each face (simplified - just front-facing planes)
            # Front face glow
            self._draw_glow_ring(shapes, (0, 0, size), size, (r, g, b))
            # Back face glow
            self._draw_glow_ring(shapes, (0, 0, -size), size, (r, g, b))
            # Top face glow
            self._draw_glow_ring(shapes, (0, size, 0), size, (r, g, b), vertical=True)
            # Bottom face glow
            self._draw_glow_ring(shapes, (0, -size, 0), size, (r, g, b), vertical=True)

    def _draw_glow_ring(
        self,
        shapes,
        center: tuple[float, float, float],
        size: float,
        color: tuple[int, int, int],
        vertical: bool = False,
    ) -> None:
        """Draw a single glow ring/halo."""
        cx, cy, cz = center
        half = size * 0.8  # Ring size

        if vertical:
            # Horizontal ring (for top/bottom)
            vertices = [
                (cx - half, cy, cz - half),
                (cx + half, cy, cz - half),
                (cx + half, cy, cz + half),
                (cx - half, cy, cz + half),
            ]
        else:
            # Vertical ring (for front/back)
            vertices = [
                (cx - half, cy - half, cz),
                (cx + half, cy - half, cz),
                (cx + half, cy + half, cz),
                (cx - half, cy + half, cz),
            ]

        shapes.quad(vertices, color)

    def cleanup(self) -> None:
        """Clean up glow effect."""
        super().cleanup()
