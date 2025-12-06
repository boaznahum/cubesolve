"""Sparkle celebration effect."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from cube.presentation.gui.effects.BaseEffect import BaseEffect

if TYPE_CHECKING:
    from cube.presentation.gui.protocols.Renderer import Renderer
    from cube.application.state import ApplicationAndViewState


@dataclass
class Sparkle:
    """A single sparkle point."""
    x: float
    y: float
    z: float
    size: float
    brightness: float  # 0.0 to 1.0
    lifetime: float    # seconds remaining
    max_lifetime: float


class SparkleEffect(BaseEffect):
    """Random bright spots twinkle on cube faces.

    Creates sparkling points that appear randomly around the cube,
    fade in and out, creating a twinkling celebration effect.
    """

    # Bright colors for sparkles
    COLORS = [
        (255, 255, 255),  # White
        (255, 255, 200),  # Warm white
        (200, 255, 255),  # Cool white
        (255, 255, 0),    # Yellow
        (255, 200, 100),  # Gold
    ]

    def __init__(
        self,
        renderer: "Renderer",
        vs: "ApplicationAndViewState",
        backend_name: str,
    ) -> None:
        super().__init__(renderer, vs, backend_name)
        self._sparkles: list[Sparkle] = []
        self._spawn_rate = 30.0  # sparkles per second
        self._spawn_accumulator = 0.0
        self._cube_size = 50.0  # approximate cube half-size for spawn area
        self._sparkle_lifetime_min = 0.2
        self._sparkle_lifetime_max = 0.6
        self._sparkle_size_min = 2.0
        self._sparkle_size_max = 6.0

    @property
    def name(self) -> str:
        return "sparkle"

    def start(self) -> None:
        """Initialize the sparkle effect."""
        super().start()
        self._sparkles = []
        self._spawn_accumulator = 0.0

    def _spawn_sparkle(self) -> Sparkle:
        """Create a new sparkle at a random position on/near the cube."""
        # Random position on cube surface (roughly)
        face = random.randint(0, 5)
        half = self._cube_size

        if face == 0:    # Front
            x, y, z = random.uniform(-half, half), random.uniform(-half, half), half
        elif face == 1:  # Back
            x, y, z = random.uniform(-half, half), random.uniform(-half, half), -half
        elif face == 2:  # Top
            x, y, z = random.uniform(-half, half), half, random.uniform(-half, half)
        elif face == 3:  # Bottom
            x, y, z = random.uniform(-half, half), -half, random.uniform(-half, half)
        elif face == 4:  # Right
            x, y, z = half, random.uniform(-half, half), random.uniform(-half, half)
        else:            # Left
            x, y, z = -half, random.uniform(-half, half), random.uniform(-half, half)

        lifetime = random.uniform(self._sparkle_lifetime_min, self._sparkle_lifetime_max)

        return Sparkle(
            x=x, y=y, z=z,
            size=random.uniform(self._sparkle_size_min, self._sparkle_size_max),
            brightness=0.0,  # Start dark, fade in
            lifetime=lifetime,
            max_lifetime=lifetime,
        )

    def update(self, dt: float) -> bool:
        """Update sparkles - spawn new ones, update brightness, remove dead ones."""
        if not super().update(dt):
            return False

        # Spawn new sparkles
        self._spawn_accumulator += self._spawn_rate * dt
        while self._spawn_accumulator >= 1.0:
            self._sparkles.append(self._spawn_sparkle())
            self._spawn_accumulator -= 1.0

        # Update existing sparkles
        alive_sparkles = []
        for s in self._sparkles:
            s.lifetime -= dt
            if s.lifetime > 0:
                # Brightness curve: fade in then fade out
                progress = 1.0 - (s.lifetime / s.max_lifetime)
                if progress < 0.3:
                    # Fade in
                    s.brightness = progress / 0.3
                elif progress > 0.7:
                    # Fade out
                    s.brightness = (1.0 - progress) / 0.3
                else:
                    # Full brightness
                    s.brightness = 1.0
                alive_sparkles.append(s)

        self._sparkles = alive_sparkles
        return True

    def draw(self) -> None:
        """Draw all sparkles as small bright quads."""
        if not self._sparkles:
            return

        shapes = self._renderer.shapes

        for s in self._sparkles:
            if s.brightness <= 0.01:
                continue

            # Pick a random bright color and apply brightness
            base_color = random.choice(self.COLORS)
            r = int(base_color[0] * s.brightness)
            g = int(base_color[1] * s.brightness)
            b = int(base_color[2] * s.brightness)

            # Draw as small quad facing camera (billboard-ish)
            half = s.size / 2
            vertices = [
                np.array([s.x - half, s.y - half, s.z]),
                np.array([s.x + half, s.y - half, s.z]),
                np.array([s.x + half, s.y + half, s.z]),
                np.array([s.x - half, s.y + half, s.z]),
            ]
            shapes.quad(vertices, (r, g, b))

    def cleanup(self) -> None:
        """Clean up sparkles."""
        super().cleanup()
        self._sparkles = []
