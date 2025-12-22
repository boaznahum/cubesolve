"""Celebration effects module for cube solver.

This module provides configurable celebration effects when the cube is solved.
Effects are triggered automatically and can be customized via command-line or config.

Available effects:
    - none: No celebration effect
    - confetti: Particle burst explosion
    - victory_spin: Cube auto-rotates showing all faces
    - sparkle: Random bright spots twinkle on faces
    - glow: Cube pulses with bloom effect (pyglet2 only)
    - combo: Combination of multiple effects
"""
from __future__ import annotations

from cube.presentation.gui.effects.CelebrationEffect import CelebrationEffect
from cube.presentation.gui.effects.CelebrationManager import CelebrationManager
from cube.presentation.gui.effects.EffectRegistry import EffectRegistry

__all__ = [
    "CelebrationEffect",
    "EffectRegistry",
    "CelebrationManager",
]
