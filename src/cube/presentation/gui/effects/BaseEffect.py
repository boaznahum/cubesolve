"""Base class for celebration effects."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cube.presentation.gui.protocols.Renderer import Renderer
    from cube.application.state import ApplicationAndViewState


class BaseEffect:
    """Base class for celebration effects.

    Provides common functionality for all effects:
    - Duration tracking
    - Running state management
    - Renderer and state access

    Subclasses should override:
    - start(): Initialize effect-specific state
    - update(dt): Update effect state each frame
    - draw(): Render the effect
    - cleanup(): Clean up resources (optional)
    - is_supported(): Return False if effect doesn't work on certain backends
    """

    def __init__(
        self,
        renderer: "Renderer",
        vs: "ApplicationAndViewState",
        backend_name: str,
    ) -> None:
        """Initialize the base effect.

        Args:
            renderer: Renderer for drawing the effect.
            vs: Application state containing effect settings.
            backend_name: Name of the current backend.
        """
        self._renderer = renderer
        self._vs = vs
        self._backend_name = backend_name
        self._running = False
        self._elapsed = 0.0
        self._duration = vs.celebration_duration

    @property
    def name(self) -> str:
        """Effect name for display/logging."""
        return self.__class__.__name__

    @property
    def running(self) -> bool:
        """Whether the effect is currently active."""
        return self._running

    @property
    def progress(self) -> float:
        """Effect progress from 0.0 to 1.0."""
        if self._duration <= 0:
            return 1.0
        return min(1.0, self._elapsed / self._duration)

    def start(self) -> None:
        """Begin the celebration effect.

        Subclasses should call super().start() then initialize their state.
        """
        self._running = True
        self._elapsed = 0.0

    def update(self, dt: float) -> bool:
        """Update effect state for the next frame.

        Args:
            dt: Time delta since last update in seconds.

        Returns:
            True if the effect should continue, False if completed.
        """
        self._elapsed += dt
        if self._elapsed >= self._duration:
            self._running = False
            return False
        return True

    def draw(self) -> None:
        """Render the effect.

        Override in subclasses to draw particles, overlays, etc.
        """
        pass

    def cleanup(self) -> None:
        """Release any resources held by the effect."""
        self._running = False

    @classmethod
    def is_supported(cls, backend_name: str) -> bool:
        """Check if this effect is supported on the given backend.

        Most effects work on all backends. Override for backend-specific effects.

        Args:
            backend_name: Name of the backend.

        Returns:
            True if supported (default for most effects).
        """
        return True
