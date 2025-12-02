"""Manager for celebration effect lifecycle."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cube.presentation.gui.effects.CelebrationEffect import CelebrationEffect
    from cube.presentation.gui.protocols.EventLoop import EventLoop
    from cube.presentation.gui.protocols.Renderer import Renderer
    from cube.application.state import ApplicationAndViewState


class CelebrationManager:
    """Manages celebration effect lifecycle.

    Responsible for:
    - Creating effects from the registry
    - Starting/stopping effects
    - Scheduling updates via the event loop
    - Calling draw() during render cycle
    - Detecting cube solve state transitions

    Usage:
        manager = CelebrationManager(renderer, vs, event_loop, "pyglet2")

        # In update loop, check for solve
        if cube.solved and not last_solved:
            manager.trigger_celebration()

        # In draw loop
        manager.draw()
    """

    def __init__(
        self,
        renderer: "Renderer",
        vs: "ApplicationAndViewState",
        event_loop: "EventLoop",
        backend_name: str,
    ) -> None:
        """Initialize the celebration manager.

        Args:
            renderer: Renderer for drawing effects.
            vs: Application state containing effect settings.
            event_loop: Event loop for scheduling updates.
            backend_name: Current backend name.
        """
        self._renderer = renderer
        self._vs = vs
        self._event_loop = event_loop
        self._backend_name = backend_name
        self._current_effect: "CelebrationEffect | None" = None
        self._update_scheduled = False

    def trigger_celebration(self) -> None:
        """Start the configured celebration effect.

        Creates a new effect instance and starts it. If an effect is already
        running, it will be stopped first.
        """
        if not self._vs.celebration_enabled:
            return

        # Stop any running effect
        self.stop()

        # Create and start new effect
        from cube.presentation.gui.effects.EffectRegistry import EffectRegistry

        effect = EffectRegistry.get_effect(
            self._vs.celebration_effect,
            self._renderer,
            self._vs,
            self._backend_name,
        )

        self._current_effect = effect
        effect.start()

        # Schedule updates at 60 FPS
        self._event_loop.schedule_interval(self._update, 1 / 60)
        self._update_scheduled = True

        self._vs.debug(True, f"Celebration started: {effect.name}")

    def _update(self, dt: float) -> None:
        """Update callback for event loop.

        Args:
            dt: Time delta since last update.
        """
        if self._current_effect and self._current_effect.running:
            if not self._current_effect.update(dt):
                self.stop()

    def draw(self) -> None:
        """Draw current effect.

        Should be called from the window's on_draw method, after drawing
        the cube but before any UI overlays.
        """
        if self._current_effect and self._current_effect.running:
            self._current_effect.draw()

    def stop(self) -> None:
        """Stop the current effect and clean up."""
        if self._update_scheduled:
            self._event_loop.unschedule(self._update)
            self._update_scheduled = False

        if self._current_effect:
            self._current_effect.cleanup()
            self._vs.debug(True, f"Celebration stopped: {self._current_effect.name}")
            self._current_effect = None

    @property
    def is_celebrating(self) -> bool:
        """Check if a celebration effect is currently running."""
        return self._current_effect is not None and self._current_effect.running

    def cleanup(self) -> None:
        """Clean up the manager and any running effect."""
        self.stop()
