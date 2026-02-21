"""
AnimationBackend protocol definition.

This protocol defines the interface for animation support in GUI backends.
"""

from typing import TYPE_CHECKING, Callable, Collection, Protocol, runtime_checkable

if TYPE_CHECKING:
    from cube.domain.model.PartSlice import PartSlice
    from cube.domain.model.Cube import Cube
    from cube.domain.model.FaceName import FaceName


@runtime_checkable
class AnimationBackend(Protocol):
    """Protocol for animation support.

    Animation backends handle the visual interpolation of cube rotations.
    Not all backends need to support animation (e.g., headless mode returns
    supported=False).
    """

    @property
    def supported(self) -> bool:
        """Whether this backend supports animation.

        Returns:
            True if animation is available, False otherwise
        """
        ...

    @property
    def running(self) -> bool:
        """Whether an animation is currently in progress.

        Returns:
            True if animating, False otherwise
        """
        ...

    @property
    def speed(self) -> float:
        """Current animation speed multiplier (1.0 = normal)."""
        ...

    @speed.setter
    def speed(self, value: float) -> None:
        """Set animation speed multiplier.

        Args:
            value: Speed multiplier (1.0 = normal, 2.0 = twice as fast)
        """
        ...

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

        The animation visually interpolates the rotation. When complete,
        on_complete is called so the caller can apply the actual model change.

        Args:
            cube: The cube being rotated
            rotate_face: Face/axis of rotation (determines rotation direction)
            slices: Which slice indices are rotating (for NxN cubes)
            n_quarter_turns: Number of 90-degree turns (1-3, negative for CCW)
            parts_to_animate: Collection of PartSlice objects being rotated
            on_complete: Callback when animation finishes
        """
        ...

    def cancel(self) -> None:
        """Cancel the current animation immediately.

        If an animation is running, it stops and on_complete is NOT called.
        """
        ...

    def pause(self) -> None:
        """Pause the current animation.

        Animation can be resumed with resume().
        """
        ...

    def resume(self) -> None:
        """Resume a paused animation."""
        ...

    def skip(self) -> None:
        """Skip to the end of the current animation.

        The animation completes instantly and on_complete IS called.
        """
        ...
