"""WebGL animation manager — client-driven pull model.

The server sends one animation event at a time and WAITS for the client
to acknowledge completion before sending the next. No timers, no speculation.

Flow:
    1. run_animation() queues a move and returns immediately
    2. _process_next() dequeues one move:
       a. Non-animatable: apply model change, send cube_state, continue
       b. Animatable: send animation_start + cube_state, WAIT for client
    3. Client sends animation_done when its animation finishes
    4. on_client_animation_done() calls _process_next() for the next move
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
    """Animation manager using client-driven pull model.

    Sends one animation event at a time and waits for the client to
    acknowledge via animation_done before sending the next. No timers,
    no duration speculation.
    """

    __slots__ = [
        "_move_queue",
        "_is_processing",
        "_web_window",
        "_operator",
        "_current_move",
        "_waiting_for_client",
        "_is_undo",
    ]

    def __init__(self, vs: "ApplicationAndViewState", operator: "Operator") -> None:
        super().__init__(vs)
        self._move_queue: deque[_QueuedMove] = deque()
        self._is_processing: bool = False
        self._web_window: ClientSession | None = None
        self._operator: Operator = operator
        self._current_move: _QueuedMove | None = None
        self._waiting_for_client: bool = False
        self._is_undo: bool = False

    @property
    def is_idle(self) -> bool:
        """True when AM has no pending work and is not waiting for client."""
        return not self._waiting_for_client and not self._move_queue and not self._is_processing

    def set_web_window(self, window: "ClientSession") -> None:
        """Set the client session reference for sending state."""
        self._web_window = window

    def cancel_animation(self) -> None:
        """Cancel all pending animations (graceful — client finishes current).

        Playing state is managed exclusively by ClientSession
        (via _fast_playing flag). This method only clears the AM's
        internal queue — the caller is responsible for send_playing().
        """
        self._move_queue.clear()
        self._current_move = None
        self._is_processing = False
        self._waiting_for_client = False

    def run_animation(self, cube: "Cube", op: "OpProtocol", alg: "SimpleAlg") -> None:
        """Queue a move for animated playback (non-blocking)."""
        assert self._window is not None

        if self._event_loop is None:
            raise RuntimeError("EventLoop is required for animation. Call set_event_loop() first.")

        if self._event_loop.has_exit:
            return

        self._move_queue.append(_QueuedMove(cube, op, alg))

        if not self._is_processing and not self._waiting_for_client:
            self._process_next()

    def on_client_animation_done(self) -> None:
        """Called when client sends animation_done — process next queued move."""
        self._waiting_for_client = False
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

            # Non-animatable moves: apply and continue immediately
            if isinstance(alg, algs.AnnotationAlg):
                self._apply_model_change(move)
                if self._web_window:
                    self._web_window.send_state()
                continue

            if not isinstance(alg, algs.AnimationAbleAlg):
                self._apply_model_change(move)
                if self._web_window:
                    self._web_window.send_state()
                continue

            if alg.n % 4 == 0:
                self._apply_model_change(move)
                if self._web_window:
                    self._web_window.send_state()
                continue

            # Animatable move: apply model change, send to client, WAIT
            duration_ms = self._get_animation_duration_ms()

            self._apply_model_change(move)

            if self._web_window:
                self._web_window.send_animation_start(alg, duration_ms, is_undo=self._is_undo)
                self._web_window.send_state()

            # Wait for client to send animation_done
            self._waiting_for_client = True
            return

        # Queue empty
        self._is_processing = False
        self._current_move = None

    def _apply_model_change(self, move: _QueuedMove) -> None:
        """Apply a move's model change without animation."""
        with self._operator.with_animation(animation=False):
            move.op(move.alg, False)

    def _get_animation_duration_ms(self) -> int:
        """Get animation duration based on current speed setting.

        Uses the formula: D(I) = D0 * (DN/D0)^(I/7)
        where D0 and DN come from config.
        This maps speed 0 → D0 ms, speed 7 → DN ms.
        """
        speed_index = self._vs.get_speed_index
        cfg = self._vs._config
        d0 = cfg.animation_speed_config.d0
        dn = cfg.animation_speed_config.dn
        duration = d0 * (dn / d0) ** (speed_index / 7.0)
        return max(10, round(duration))
