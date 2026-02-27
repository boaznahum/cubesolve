"""Web animation manager — non-blocking animation for async event loop.

The standard AnimationManager uses a blocking while loop that would freeze
the asyncio event loop. This subclass queues moves and processes them via
scheduled callbacks, allowing the async event loop to continue running.

Two-phase solve strategy:
    The web backend uses slv.solution() to compute the solution instantly
    (no animation), then replays it with op.play(). This means run_animation()
    only receives replay moves — no solver is running concurrently. Model
    changes are deferred to _on_animation_done(), matching the base class flow:
    animate → cleanup → apply model change → rebuild display lists → next.
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
    from cube.presentation.gui.backends.web.ClientSession import ClientSession


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
    async coroutines.

    Flow:
        1. run_animation() queues a move and returns immediately
        2. _process_next() dequeues one move, creates Animation, starts async task
        3. Each tick: advance angle + send frame to browser
        4. When done: cleanup, apply model change, rebuild display lists, next
    """

    __slots__ = [
        "_move_queue",
        "_is_processing",
        "_web_window",
        "_operator",
        "_current_move",
        "_animation_task",
    ]

    def __init__(self, vs: "ApplicationAndViewState", operator: "Operator") -> None:
        import asyncio
        super().__init__(vs)
        self._move_queue: deque[_QueuedMove] = deque()
        self._is_processing: bool = False
        self._web_window: ClientSession | None = None
        self._operator: Operator = operator
        self._current_move: _QueuedMove | None = None
        self._animation_task: asyncio.Task[None] | None = None

    def set_web_window(self, window: "ClientSession") -> None:
        """Set the client session reference for triggering redraws."""
        self._web_window = window

    def cancel_animation(self) -> None:
        """Cancel the current animation and discard all queued moves.

        The cube stays wherever the model is — moves already animated and
        applied are kept, remaining queued moves are thrown away.
        Cancels the async task to interrupt any in-progress sleep immediately.
        """
        # Clear the queue (discard remaining moves)
        self._move_queue.clear()

        # Stop current animation if running
        animation = self._current_animation
        if animation:
            animation.done = True  # signal the async loop to stop
            animation.cleanup()
        self._set_animation(None)
        self._current_move = None
        self._is_processing = False

        # Cancel the async task to interrupt sleep immediately
        if self._animation_task and not self._animation_task.done():
            self._animation_task.cancel()
        self._animation_task = None

        # Rebuild display lists to reflect current model state
        if self._web_window:
            self._web_window.update_gui_elements()

    def run_animation(self, cube: "Cube", op: "OpProtocol", alg: "SimpleAlg") -> None:
        """Queue a move for animated playback (non-blocking).

        Model changes are DEFERRED to _on_animation_done(), matching the
        base class flow. This works because the web backend uses a two-phase
        solve: slv.solution() computes instantly, then op.play() replays.
        No solver runs concurrently with animation.
        """
        assert self._window is not None

        if self._event_loop is None:
            raise RuntimeError("EventLoop is required for animation. Call set_event_loop() first.")

        if self._event_loop.has_exit:
            return

        # Queue the move — model change deferred to _on_animation_done()
        self._move_queue.append(_QueuedMove(cube, op, alg))

        if not self._is_processing:
            self._process_next()

    def _process_next(self) -> None:
        """Process queued moves until hitting an animatable one.

        Uses a loop (not recursion) to skip non-animatable moves, avoiding
        stack overflow when many annotations/non-animatable moves are queued.
        When an animatable move is found, starts an async animation task
        (which calls _on_animation_done → _process_next when complete).
        """
        while self._move_queue:
            self._is_processing = True
            move = self._move_queue.popleft()
            self._current_move = move

            event_loop = self._event_loop
            assert event_loop is not None

            if event_loop.has_exit:
                self._is_processing = False
                return

            alg = move.alg

            # ── Non-animatable moves: apply and continue loop ──

            if isinstance(alg, algs.AnnotationAlg):
                # Must use _apply_model_change (which disables animation) to
                # prevent re-entry: operator.play(annotation) with animation
                # enabled would call run_animation() again → infinite loop.
                self._apply_model_change(move)
                if self._web_window:
                    self._web_window.update_gui_elements()
                continue

            try:
                viewer = self._window.viewer  # type: ignore[union-attr]
            except RuntimeError:
                self._apply_model_change(move)
                continue

            if viewer is None:
                self._apply_model_change(move)
                continue

            if not isinstance(alg, algs.AnimationAbleAlg):
                self._apply_model_change(move)
                continue

            if alg.n % 4 == 0:
                self._apply_model_change(move)
                continue

            # ── Animatable move: start async animation and return ──

            animation: Animation = viewer.create_animation(alg, self._vs)
            self._set_animation(animation)

            import asyncio
            loop = asyncio.get_event_loop()
            self._animation_task = loop.create_task(self._animate_async(animation))
            return  # async task will call _on_animation_done → _process_next

        # Queue empty
        self._is_processing = False

    def _apply_model_change(self, move: _QueuedMove) -> None:
        """Apply a move's model change without animation."""
        with self._operator.with_animation(animation=False):
            move.op(move.alg, False)

    async def _animate_async(self, animation: Animation) -> None:
        """Run animation as async coroutine with real sleeps between frames.

        Each iteration: advance angle -> draw frame -> await sleep.
        The await guarantees the WebSocket send completes and the frame
        reaches the browser before the next frame is prepared.

        Wrapped in try/finally to ensure _on_animation_done() always runs,
        preventing _is_processing from getting stuck on True after a crash.
        CancelledError is caught separately — cancel_animation() already
        handles cleanup, so we just exit silently.
        """
        import asyncio

        delay = animation.delay

        try:
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
                # Task.cancel() interrupts this sleep immediately.
                await asyncio.sleep(delay)
        except asyncio.CancelledError:
            # cancel_animation() already cleaned up — just exit
            return
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Animation loop error: {e}", flush=True)
        finally:
            self._animation_task = None
            try:
                self._on_animation_done()
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Animation done error: {e}", flush=True)
                # Emergency reset — ensure queue never gets permanently stuck
                self._set_animation(None)
                self._current_move = None
                self._is_processing = False

    def _on_animation_done(self) -> None:
        """Handle animation completion.

        Follows the same order as the base class _op_and_play_animation():
        1. Cleanup animation (unhide parts in viewer)
        2. Apply model change (operator(alg, False))
        3. Rebuild display lists (update_gui_elements)
        4. Process next queued move
        """
        # 1. Cleanup animation
        animation = self._current_animation
        if animation:
            animation.cleanup()
        self._set_animation(None)

        # 2. Apply model change
        move = self._current_move
        if move:
            self._apply_model_change(move)
        self._current_move = None

        # 3. Rebuild display lists to reflect the updated model
        if self._web_window:
            self._web_window.update_gui_elements()

        # 4. Process next queued move
        self._process_next()
