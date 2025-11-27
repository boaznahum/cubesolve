"""
Pyglet animation backend implementation.

Provides animation support using pyglet's clock and event loop.
"""

from typing import Callable

try:
    import pyglet
except ImportError as e:
    raise ImportError("pyglet is required for PygletAnimation: pip install pyglet") from e


class PygletAnimation:
    """Pyglet animation backend implementing AnimationBackend protocol.

    Uses pyglet's clock for smooth animation timing.
    """

    def __init__(self) -> None:
        self._running = False
        self._paused = False
        self._speed = 1.0
        self._current_animation: Callable[[float], bool] | None = None
        self._on_complete: Callable[[], None] | None = None

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
        update_func: Callable[[float], bool],
        on_complete: Callable[[], None] | None = None,
        interval: float = 1 / 60,
    ) -> None:
        """Run an animation.

        Args:
            update_func: Function(dt) that returns True while animation should continue
            on_complete: Optional callback when animation completes
            interval: Update interval in seconds (default 60 FPS)
        """
        if self._running:
            self.cancel()

        self._current_animation = update_func
        self._on_complete = on_complete
        self._running = True
        self._paused = False

        def animation_update(dt: float) -> None:
            if not self._running or self._paused:
                return

            # Apply speed multiplier
            adjusted_dt = dt * self._speed

            # Call update function
            if self._current_animation:
                should_continue = self._current_animation(adjusted_dt)

                if not should_continue:
                    self._finish_animation()

        pyglet.clock.schedule_interval(animation_update, interval)
        self._update_callback = animation_update

    def _finish_animation(self) -> None:
        """Complete the current animation."""
        self._running = False

        if hasattr(self, '_update_callback'):
            pyglet.clock.unschedule(self._update_callback)

        if self._on_complete:
            self._on_complete()

        self._current_animation = None
        self._on_complete = None

    def cancel(self) -> None:
        """Cancel the current animation."""
        if self._running:
            self._running = False
            if hasattr(self, '_update_callback'):
                pyglet.clock.unschedule(self._update_callback)
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
