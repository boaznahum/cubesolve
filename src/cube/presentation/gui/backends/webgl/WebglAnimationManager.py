"""WebGL animation manager — sends animation events to client.

Unlike the web backend which sends per-frame rendering commands, the webgl
backend sends animation START events and lets the client animate at 60fps.
The server applies the model change immediately and sends the new cube state.

Flow:
    1. run_animation() queues a move and returns immediately
    2. _process_next() dequeues one move:
       a. Non-animatable: apply model change, send cube_state, continue
       b. Animatable: send animation_start event, apply model change,
          send cube_state (client uses it after animation completes),
          schedule next move after estimated animation duration
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cube.application.animation.AnimationManager import AnimationManager
from cube.domain import algs

if TYPE_CHECKING:
    from cube.application.animation.AnimationManager import OpProtocol
    from cube.application.commands.Operator import Operator
    from cube.application.state import ApplicationAndViewState
    from cube.domain.algs import SimpleAlg
    from cube.domain.model.Cube import Cube
    from cube.presentation.gui.backends.webgl.ClientSession import ClientSession


@dataclass
class _QueuedMove:
    """A queued animation move."""
    cube: Cube
    op: OpProtocol
    alg: SimpleAlg


class WebglAnimationManager(AnimationManager):
    """Animation manager that sends events to the client for local animation.

    Instead of rendering frames server-side, sends:
    - animation_start: face rotation animation event
    - cube_state: updated face colors (applied after client animation)
    """

    __slots__ = [
        "_move_queue",
        "_is_processing",
        "_web_window",
        "_operator",
        "_current_move",
        "_pending_timer",
    ]

    def __init__(self, vs: "ApplicationAndViewState", operator: "Operator") -> None:
        super().__init__(vs)
        self._move_queue: deque[_QueuedMove] = deque()
        self._is_processing: bool = False
        self._web_window: ClientSession | None = None
        self._operator: Operator = operator
        self._current_move: _QueuedMove | None = None
        self._pending_timer: bool = False

    def set_web_window(self, window: "ClientSession") -> None:
        """Set the client session reference for sending state."""
        self._web_window = window

    def cancel_animation(self) -> None:
        """Cancel all pending animations."""
        self._move_queue.clear()
        self._current_move = None
        self._is_processing = False
        self._pending_timer = False

        # Tell client to stop animations and snap to current state
        if self._web_window:
            self._web_window.send_animation_stop()
            self._web_window.send_cube_state()

    def run_animation(self, cube: "Cube", op: "OpProtocol", alg: "SimpleAlg") -> None:
        """Queue a move for animated playback (non-blocking)."""
        assert self._window is not None

        if self._event_loop is None:
            raise RuntimeError("EventLoop is required for animation. Call set_event_loop() first.")

        if self._event_loop.has_exit:
            return

        self._move_queue.append(_QueuedMove(cube, op, alg))

        if not self._is_processing:
            self._process_next()

    def _process_next(self) -> None:
        """Process queued moves, sending animation events to client."""
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

            # Non-animatable moves: apply and continue
            if isinstance(alg, algs.AnnotationAlg):
                self._apply_model_change(move)
                if self._web_window:
                    self._web_window.send_cube_state()
                    self._web_window.send_text()
                continue

            if not isinstance(alg, algs.AnimationAbleAlg):
                self._apply_model_change(move)
                if self._web_window:
                    self._web_window.send_cube_state()
                continue

            if alg.n % 4 == 0:
                self._apply_model_change(move)
                if self._web_window:
                    self._web_window.send_cube_state()
                continue

            # Animatable move: apply model change FIRST, then send animation
            # event with post-move state embedded. This ensures the client
            # has the correct final state when the animation completes.
            duration_ms = self._get_animation_duration_ms()

            self._apply_model_change(move)

            if self._web_window:
                self._web_window.send_animation_start(alg, duration_ms)
                self._web_window.send_cube_state()
                self._web_window.send_text()

            # Schedule next move after animation duration
            # (gives client time to animate before showing next move)
            self._pending_timer = True
            delay_s = duration_ms / 1000.0
            event_loop.schedule_once(self._on_timer, delay_s)
            return  # Wait for timer to process next

        # Queue empty
        self._is_processing = False
        self._current_move = None

    def _on_timer(self, _dt: float) -> None:
        """Timer callback — process next queued move."""
        self._pending_timer = False
        self._process_next()

    def _apply_model_change(self, move: _QueuedMove) -> None:
        """Apply a move's model change without animation."""
        with self._operator.with_animation(animation=False):
            move.op(move.alg, False)

    def _get_animation_duration_ms(self) -> int:
        """Get animation duration based on current speed setting.

        Supports fractional speed indices (e.g. 2.5) by interpolating
        between adjacent duration entries.
        """
        from cube.application.state import speeds
        speed_index = self._vs.get_speed_index
        if speed_index >= len(speeds) - 1:
            speed_index = len(speeds) - 1

        # Speed 0 = slowest (long duration), higher = faster
        # Map speed index to duration: 0→500ms, 1→400ms, ... 7→50ms
        durations = [500, 400, 300, 200, 150, 100, 70, 50]

        int_idx = int(speed_index)
        frac = speed_index - int_idx

        if frac == 0 or int_idx >= len(durations) - 1:
            idx = min(int_idx, len(durations) - 1)
            return durations[idx]

        # Interpolate between adjacent durations
        lo = durations[int_idx]
        hi = durations[min(int_idx + 1, len(durations) - 1)]
        return round(lo + (hi - lo) * frac)
