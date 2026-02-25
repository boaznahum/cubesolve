"""Web animation manager — non-blocking animation for async event loop.

The standard AnimationManager uses a blocking while loop that would freeze
the asyncio event loop. This subclass queues moves and processes them via
scheduled callbacks, allowing the async event loop to continue running.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cube.application.animation.AnimationManager import Animation, AnimationManager
from cube.domain import algs

if TYPE_CHECKING:
    from cube.application.animation.AnimationManager import OpProtocol
    from cube.application.commands.Operator import Operator
    from cube.application.state import ApplicationAndViewState
    from cube.domain.algs import SimpleAlg
    from cube.domain.model.Cube import Cube
    from cube.presentation.gui.backends.web.WebAppWindow import WebAppWindow


@dataclass
class _QueuedMove:
    """A queued animation move."""

    cube: Cube
    op: OpProtocol
    alg: SimpleAlg


class WebAnimationManager(AnimationManager):
    """Non-blocking animation manager for the web backend.

    Instead of blocking in a while loop (which would freeze the asyncio
    event loop), this queues moves and processes them one at a time via
    scheduled interval callbacks.

    Flow:
        1. run_animation() queues a move and returns immediately
        2. _process_next() dequeues one move, creates Animation, schedules tick
        3. Each tick: advance angle + send frame to browser
        4. When done: cleanup, apply model change, process next in queue
    """

    __slots__ = [
        "_move_queue",
        "_is_processing",
        "_web_window",
        "_operator",
        "_current_move",
    ]

    def __init__(self, vs: "ApplicationAndViewState", operator: "Operator") -> None:
        super().__init__(vs)
        self._move_queue: deque[_QueuedMove] = deque()
        self._is_processing: bool = False
        self._web_window: WebAppWindow | None = None
        self._operator: Operator = operator
        self._current_move: _QueuedMove | None = None

    def set_web_window(self, window: "WebAppWindow") -> None:
        """Set the web window reference for triggering redraws."""
        self._web_window = window

    def run_animation(self, cube: "Cube", op: "OpProtocol", alg: "SimpleAlg") -> None:
        """Queue a move for animation (non-blocking).

        Unlike the base class which blocks until animation completes,
        this queues the move and returns immediately. Moves are processed
        sequentially via event loop callbacks to maintain correct ordering.
        """
        assert self._window is not None

        if self._event_loop is None:
            raise RuntimeError("EventLoop is required for animation. Call set_event_loop() first.")

        if self._event_loop.has_exit:
            return

        # Queue ALL moves (including non-animated) to maintain ordering.
        # If we executed non-animated moves immediately while animated moves
        # are queued, the cube state would become inconsistent.
        self._move_queue.append(_QueuedMove(cube, op, alg))

        if not self._is_processing:
            self._process_next()

    def _process_next(self) -> None:
        """Process the next queued move."""
        if not self._move_queue:
            self._is_processing = False
            return

        self._is_processing = True
        move = self._move_queue.popleft()
        self._current_move = move

        event_loop = self._event_loop
        assert event_loop is not None

        if event_loop.has_exit:
            self._is_processing = False
            return

        alg = move.alg

        # ── Early exits (same logic as _op_and_play_animation) ──

        # AnnotationAlg — execute immediately, no animation
        if isinstance(alg, algs.AnnotationAlg):
            with self._operator.with_animation(animation=False):
                move.op(alg, False)
            if self._web_window:
                self._web_window.update_gui_elements()
            self._process_next()
            return

        # No viewer — execute directly
        try:
            viewer = self._window.viewer  # type: ignore[union-attr]
        except RuntimeError:
            self._apply_move_directly(move)
            self._process_next()
            return

        if viewer is None:
            self._apply_move_directly(move)
            self._process_next()
            return

        # Not animation-able — execute directly
        if not isinstance(alg, algs.AnimationAbleAlg):
            self._apply_move_directly(move)
            self._process_next()
            return

        # Zero rotation — skip animation
        if alg.n % 4 == 0:
            self._apply_move_directly(move)
            self._process_next()
            return

        # ── Create and start animation ──

        animation: Animation = viewer.create_animation(alg, self._vs)
        self._set_animation(animation)

        # Run animation as async coroutine with real sleeps between frames.
        # This guarantees WebSocket frames are sent with actual time gaps,
        # unlike schedule_interval where multiple ticks can fire in the same
        # event loop iteration and bunch up frame sends.
        import asyncio
        loop = asyncio.get_event_loop()
        loop.create_task(self._animate_async(animation))

    def _apply_move_directly(self, move: _QueuedMove) -> None:
        """Apply a move without animation (suppresses re-entry into animation)."""
        with self._operator.with_animation(animation=False):
            move.op(move.alg, False)

    async def _animate_async(self, animation: Animation) -> None:
        """Run animation as async coroutine with real sleeps between frames.

        Each iteration: advance angle → draw frame → await sleep.
        The await guarantees the WebSocket send completes and the frame
        reaches the browser before the next frame is prepared.
        """
        import asyncio

        delay = animation.delay

        while not animation.done:
            # Advance animation angle
            animation.update_gui_elements()

            # Send frame to browser
            if self._web_window:
                self._web_window._on_draw()

            if animation.done:
                break

            # Real async sleep — yields to event loop, ensuring the
            # WebSocket frame is sent before preparing the next one.
            await asyncio.sleep(delay)

        self._on_animation_done()

    def _on_animation_done(self) -> None:
        """Handle animation completion — cleanup, apply model, process next."""
        # Cleanup animation (unhides parts in viewer)
        animation = self._current_animation
        if animation:
            animation.cleanup()
        self._set_animation(None)

        # Apply the model change with animation suppressed.
        # At this point _w_with_animation context has exited (animation_running=False),
        # so we must suppress animation to prevent re-entry into run_animation().
        move = self._current_move
        assert move is not None
        self._apply_move_directly(move)
        self._current_move = None

        # Update GUI to reflect model change
        if self._web_window:
            self._web_window.update_gui_elements()

        # Process next queued move
        self._process_next()
