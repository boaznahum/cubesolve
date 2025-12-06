"""Confetti particle burst celebration effect."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from cube.presentation.gui.effects.BaseEffect import BaseEffect

if TYPE_CHECKING:
    from cube.presentation.gui.protocols.Renderer import Renderer
    from cube.application.state import ApplicationAndViewState


@dataclass
class Particle:
    """A single confetti particle."""

    x: float
    y: float
    z: float
    vx: float  # velocity x
    vy: float  # velocity y
    vz: float  # velocity z
    color: tuple[int, int, int]
    size: float
    rotation: float
    rotation_speed: float
    alpha: float = 1.0  # transparency


class ConfettiEffect(BaseEffect):
    """Particle burst explosion effect.

    Creates a burst of colorful confetti particles that explode outward
    from the center and fall with gravity.
    """

    # Cube face colors for confetti
    COLORS = [
        (255, 255, 255),  # White
        (255, 255, 0),    # Yellow
        (255, 0, 0),      # Red
        (255, 128, 0),    # Orange
        (0, 0, 255),      # Blue
        (0, 255, 0),      # Green
    ]

    def __init__(
        self,
        renderer: "Renderer",
        vs: "ApplicationAndViewState",
        backend_name: str,
    ) -> None:
        super().__init__(renderer, vs, backend_name)
        self._particles: list[Particle] = []
        self._gravity = -150.0  # units/s^2 (negative = down)
        self._num_particles = 150
        self._initial_speed_min = 80.0
        self._initial_speed_max = 200.0
        self._particle_size_min = 3.0
        self._particle_size_max = 8.0
        self._fade_start = 0.7  # Start fading at 70% progress

    @property
    def name(self) -> str:
        return "confetti"

    def start(self) -> None:
        """Initialize the confetti burst."""
        super().start()
        self._particles = []

        # Create particles bursting from center
        for _ in range(self._num_particles):
            # Random direction (spherical distribution, biased upward)
            theta = random.uniform(0, 2 * math.pi)  # horizontal angle
            phi = random.uniform(-math.pi / 6, math.pi / 2)  # vertical angle (more up than down)

            # Random speed
            speed = random.uniform(self._initial_speed_min, self._initial_speed_max)

            # Calculate velocity components
            vx = speed * math.cos(theta) * math.cos(phi)
            vy = speed * math.sin(phi)  # mostly upward
            vz = speed * math.sin(theta) * math.cos(phi)

            self._particles.append(
                Particle(
                    x=0.0,
                    y=0.0,
                    z=0.0,
                    vx=vx,
                    vy=vy,
                    vz=vz,
                    color=random.choice(self.COLORS),
                    size=random.uniform(self._particle_size_min, self._particle_size_max),
                    rotation=random.uniform(0, 360),
                    rotation_speed=random.uniform(-360, 360),
                    alpha=1.0,
                )
            )

    def update(self, dt: float) -> bool:
        """Update particle positions and physics."""
        if not super().update(dt):
            return False

        # Calculate fade based on progress
        if self.progress > self._fade_start:
            fade_progress = (self.progress - self._fade_start) / (1.0 - self._fade_start)
            global_alpha = 1.0 - fade_progress
        else:
            global_alpha = 1.0

        # Update each particle
        for p in self._particles:
            # Apply velocity
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.z += p.vz * dt

            # Apply gravity
            p.vy += self._gravity * dt

            # Apply rotation
            p.rotation += p.rotation_speed * dt

            # Apply air resistance (slight drag)
            drag = 0.98
            p.vx *= drag
            p.vz *= drag

            # Update alpha
            p.alpha = global_alpha

        return True

    def draw(self) -> None:
        """Draw all particles."""
        if not self._particles:
            return

        shapes = self._renderer.shapes

        for p in self._particles:
            # Skip particles that have fallen too far
            if p.y < -300:
                continue

            # Skip fully transparent particles
            if p.alpha <= 0.01:
                continue

            # Calculate color with alpha
            r, g, b = p.color
            # Apply alpha by darkening (simple approach without actual alpha blending)
            r = int(r * p.alpha)
            g = int(g * p.alpha)
            b = int(b * p.alpha)

            # Draw as a small quad (simplified - no rotation for performance)
            half = p.size / 2

            # Create quad vertices
            vertices = [
                np.array([p.x - half, p.y - half, p.z]),
                np.array([p.x + half, p.y - half, p.z]),
                np.array([p.x + half, p.y + half, p.z]),
                np.array([p.x - half, p.y + half, p.z]),
            ]

            shapes.quad(vertices, (r, g, b))

    def cleanup(self) -> None:
        """Clean up particles."""
        super().cleanup()
        self._particles = []
