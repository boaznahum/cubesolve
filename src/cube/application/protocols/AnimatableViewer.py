"""
AnimatableViewer protocol for viewers that support animation.

This protocol decouples AnimationManager (application layer) from specific
viewer implementations (presentation layer). Viewers implement this protocol
to provide animation creation, and AnimationManager schedules the animation
without knowing implementation details.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.algs.AnimationAbleAlg import AnimationAbleAlg
    from cube.application.state import ApplicationAndViewState
    from cube.application.animation.AnimationManager import Animation


@runtime_checkable
class AnimatableViewer(Protocol):
    """Protocol for viewers that support animation.

    Both GCubeViewer (display lists) and ModernGLCubeViewer (VBOs) implement
    this protocol, allowing AnimationManager to create animations polymorphically.

    The viewer decides HOW to animate (display lists, VBOs, shaders, etc.),
    while AnimationManager handles WHEN (scheduling, timing, event loop).
    """

    @property
    def cube(self) -> "Cube":
        """The cube being viewed."""
        ...

    def create_animation(
        self,
        alg: "AnimationAbleAlg",
        vs: "ApplicationAndViewState",
    ) -> "Animation":
        """Create an animation for the given algorithm.

        The viewer creates an Animation object with:
        - _animation_draw_only: Called each frame to render animated parts
        - _animation_update_only: Called to advance animation state
        - _animation_cleanup: Called when animation completes
        - delay: Time between frames
        - done: Flag to indicate completion

        Args:
            alg: The algorithm being animated (has get_animation_objects())
            vs: Application view state (for speed settings, view transforms)

        Returns:
            Animation object ready for scheduling by AnimationManager
        """
        ...

    def update(self) -> None:
        """Update the viewer's display (called when cube state changes)."""
        ...

    def draw(self) -> None:
        """Draw the cube to the screen."""
        ...

    def reset(self) -> None:
        """Reset the viewer (called when cube is reset or resized)."""
        ...

    def cleanup(self) -> None:
        """Clean up resources when shutting down."""
        ...
