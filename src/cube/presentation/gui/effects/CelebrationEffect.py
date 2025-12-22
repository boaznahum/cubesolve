"""Protocol definition for celebration effects."""
from __future__ import annotations

from typing import Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    pass


@runtime_checkable
class CelebrationEffect(Protocol):
    """Protocol for celebration effects when cube is solved.

    Effects are triggered when the cube transitions from unsolved to solved state.
    Each effect manages its own lifecycle: start, update loop, draw, cleanup.

    Implementations should:
    - Be lightweight and not block the main thread
    - Support graceful degradation for unsupported backends
    - Clean up resources in cleanup() method
    """

    @property
    def name(self) -> str:
        """Effect name for display/logging."""
        ...

    @property
    def running(self) -> bool:
        """Whether the effect is currently active."""
        ...

    def start(self) -> None:
        """Begin the celebration effect.

        Called once when the effect is triggered. Initialize any state,
        particles, timers, etc. here.
        """
        ...

    def update(self, dt: float) -> bool:
        """Update effect state for the next frame.

        Args:
            dt: Time delta since last update in seconds.

        Returns:
            True if the effect should continue, False if it has completed.
        """
        ...

    def draw(self) -> None:
        """Render the effect.

        Called during the window's draw cycle. Should render any visual
        elements of the effect (particles, overlays, etc.).
        """
        ...

    def cleanup(self) -> None:
        """Release any resources held by the effect.

        Called when the effect completes or is stopped early.
        Free any GPU resources, clear particle arrays, etc.
        """
        ...

    @classmethod
    def is_supported(cls, backend_name: str) -> bool:
        """Check if this effect is supported on the given backend.

        Args:
            backend_name: Name of the backend ("pyglet", "pyglet2", etc.)

        Returns:
            True if the effect can run on this backend.
        """
        ...
