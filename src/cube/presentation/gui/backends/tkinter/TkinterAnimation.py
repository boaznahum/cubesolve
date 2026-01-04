"""
Tkinter animation backend implementation.

Provides animation support using Tkinter's after() scheduling.
Note: The main animation scheduling is done through TkinterEventLoop.schedule_interval().
This class provides the AnimationBackend protocol implementation for completeness.
"""

from typing import TYPE_CHECKING, Callable, Collection

from cube.presentation.gui.protocols import AnimationBackend

if TYPE_CHECKING:
    from cube.domain.model.PartSlice import PartSlice
    from cube.domain.model.Cube import Cube
    from cube.domain.geometric.cube_boy import FaceName


class TkinterAnimation(AnimationBackend):
    """Tkinter animation backend implementing AnimationBackend protocol.

    Uses Tkinter's after() for timing. The actual animation scheduling
    is typically done through TkinterEventLoop.schedule_interval(),
    but this class provides the AnimationBackend protocol for consistency.
    """

    def __init__(self) -> None:
        self._running = False
        self._paused = False
        self._speed = 1.0
        self._current_animation: Callable[[float], bool] | None = None
        self._on_complete: Callable[[], None] | None = None
        self._root = None  # Tk root for after() scheduling
        self._after_id: str | None = None

    def set_root(self, root) -> None:
        """Set the Tk root window for scheduling.

        Args:
            root: The tk.Tk root window
        """
        self._root = root

    @property
    def supported(self) -> bool:
        """Animation is supported with Tkinter."""
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

        if self._after_id and self._root:
            try:
                self._root.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

        if self._on_complete:
            self._on_complete()

        self._current_animation = None
        self._on_complete = None

    def cancel(self) -> None:
        """Cancel the current animation."""
        if self._running:
            self._running = False
            if self._after_id and self._root:
                try:
                    self._root.after_cancel(self._after_id)
                except Exception:
                    pass
                self._after_id = None
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
