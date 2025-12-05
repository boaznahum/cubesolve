"""
Pyglet animation backend implementation.

Provides animation support using pyglet's clock and event loop.
"""

from typing import Callable, Collection, TYPE_CHECKING

try:
    import pyglet
except ImportError as e:
    raise ImportError("pyglet is required for PygletAnimation: pip install pyglet") from e

from cube.presentation.gui.protocols import AnimationBackend

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model.cube_boy import FaceName
    from cube.domain.model._part_slice import PartSlice


class PygletAnimation(AnimationBackend):
    """Pyglet animation backend implementing AnimationBackend protocol.

    Uses pyglet's clock for smooth animation timing.
    """

    def __init__(self) -> None:
        self._running = False
        self._paused = False
        self._speed = 1.0
        self._current_animation: Callable[[float], bool] | None = None
        self._on_complete: Callable[[], None] | None = None
        self._update_callback: Callable[[float], None] | None = None

    @property
    def supported(self) -> bool:
        """Animation is supported with pyglet."""
        return True

    @property
    def running(self) -> bool:
        """Whether an animation is currently running."""
        return self._running

    @property
    def speed(self) -> float:
        """Animation speed multiplier."""
        return self._speed

    @speed.setter
    def speed(self, value: float) -> None:
        """Set animation speed multiplier."""
        self._speed = max(0.1, value)  # Minimum speed

    def run_animation(
        self,
        cube: "Cube",
        rotate_face: "FaceName",
        slices: Collection[int],
        n_quarter_turns: int,
        parts_to_animate: Collection["PartSlice"],
        on_complete: Callable[[], None],
    ) -> None:
        """Start an animation for a cube rotation.

        Note: This is the protocol-compliant signature. The actual animation
        logic is handled by AnimationManager through EventLoop.schedule_interval().

        Args:
            cube: The cube being rotated
            rotate_face: Face/axis of rotation
            slices: Which slice indices are rotating
            n_quarter_turns: Number of 90-degree turns
            parts_to_animate: Collection of PartSlice objects
            on_complete: Callback when animation finishes
        """
        if self._running:
            self.cancel()

        self._on_complete = on_complete
        self._running = True
        self._paused = False

        # The actual animation frames are handled by AnimationManager
        # through EventLoop.schedule_interval(). This is just for
        # tracking state and providing the protocol interface.

    def _finish_animation(self) -> None:
        """Complete the current animation."""
        self._running = False

        if self._update_callback is not None:
            pyglet.clock.unschedule(self._update_callback)
            self._update_callback = None

        if self._on_complete:
            self._on_complete()

        self._current_animation = None
        self._on_complete = None

    def cancel(self) -> None:
        """Cancel the current animation."""
        if self._running:
            self._running = False
            if self._update_callback is not None:
                pyglet.clock.unschedule(self._update_callback)
                self._update_callback = None
            self._current_animation = None
            self._on_complete = None

    def pause(self) -> None:
        """Pause the current animation."""
        self._paused = True

    def resume(self) -> None:
        """Resume a paused animation."""
        self._paused = False

    def skip(self) -> None:
        """Skip to the end of the current animation."""
        if self._running:
            self._finish_animation()
