"""
Null Viewer implementation.

Provides a minimal AnimatableViewer implementation for backends that don't
need graphical rendering (console, web, etc.). This is a no-op viewer that
satisfies the protocol requirements without actually rendering anything.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from cube.application.protocols import AnimatableViewer

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.algs.AnimationAbleAlg import AnimationAbleAlg
    from cube.application.state import ApplicationAndViewState
    from cube.application.animation.AnimationManager import Animation


class NullViewer(AnimatableViewer):
    """No-op viewer for backends without graphical rendering.

    Implements AnimatableViewer protocol with no-op methods.
    Use this for backends like console, web, etc.
    """

    def __init__(self, cube: "Cube"):
        """Initialize with cube reference.

        Args:
            cube: The cube to view.
        """
        self._cube = cube

    @property
    def cube(self) -> "Cube":
        """The cube being viewed."""
        return self._cube

    def create_animation(
        self,
        alg: "AnimationAbleAlg",
        vs: "ApplicationAndViewState",
    ) -> "Animation":
        """Create animation - not supported in console mode.

        Console backend doesn't support animation, so this raises NotImplementedError.
        The console backend sets animation_manager to None, so this should never be called.

        Raises:
            NotImplementedError: Always - console doesn't support animation.
        """
        raise NotImplementedError("Console backend does not support animation")

    def update(self) -> None:
        """Update the viewer - no-op for console."""
        pass

    def draw(self) -> None:
        """Draw the cube - no-op for console (text rendering is separate)."""
        pass

    def reset(self) -> None:
        """Reset the viewer - no-op for console."""
        pass

    def cleanup(self) -> None:
        """Clean up resources - no-op for console."""
        pass
