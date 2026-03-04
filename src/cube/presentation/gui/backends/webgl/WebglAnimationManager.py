"""WebGL animation manager — client-driven pull model.

The server sends one animation event at a time and WAITS for the client
to acknowledge completion before sending the next. No timers, no speculation.

Two modes of operation:

**Queue mode** (default — used for redo/undo playback):
    1. run_animation() queues a move and returns immediately
    2. _process_next() dequeues one move:
       a. Non-animatable: apply model change, send cube_state, continue
       b. Animatable: send animation_start + cube_state, WAIT for client
    3. Client sends animation_done when its animation finishes
    4. on_client_animation_done() calls _process_next() for the next move

**Blocking mode** (used during one-phase solve):
    1. run_animation() is called from solver worker thread
    2. Non-animatable: apply + send state, return immediately
    3. Animatable: apply + send animation_start, block on threading.Event
    4. Client sends animation_done → event is set → solver thread unblocks
    This keeps solver annotations (markers) visible during animation.
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cube.application.animation.AnimationManager import AnimationManager
from cube.domain import algs

if TYPE_CHECKING:
    from collections.abc import Callable

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
        "_on_queue_drained",
        "_blocking_mode",
        "_blocking_event",
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
        self._on_queue_drained: Callable[[], None] | None = None
        self._blocking_mode: bool = False
        self._blocking_event: threading.Event = threading.Event()

    @property
    def is_idle(self) -> bool:
        """True when AM has no pending work and is not waiting for client."""
        return not self._waiting_for_client and not self._move_queue and not self._is_processing

    def set_web_window(self, window: "ClientSession") -> None:
        """Set the client session reference for sending state."""
        self._web_window = window

    def set_on_queue_drained(self, callback: "Callable[[], None] | None") -> None:
        """Set callback for when the animation queue becomes empty.

        Used by ClientSession to notify the FSM when animations complete
        (e.g., after a single redo/undo animation finishes).
        """
        self._on_queue_drained = callback

    def set_blocking_mode(self, enabled: bool) -> None:
        """Enable or disable blocking mode for one-phase solve.

        In blocking mode, run_animation() blocks the calling thread
        (solver worker) until the client signals animation_done.
        """
        self._blocking_mode = enabled
        if not enabled:
            # Ensure event is set so no thread stays blocked
            self._blocking_event.set()

    def cancel_animation(self) -> None:
        """Cancel all pending animations (graceful — client finishes current).

        Playing state is managed by ClientSession's FlowStateMachine.
        This method only clears the AM's internal queue.

        In blocking mode: signals the operator to abort and unblocks
        the solver thread so OpAborted can propagate cleanly.
        """
        if self._blocking_mode:
            self._operator.abort()
            self._blocking_event.set()
            return
        self._move_queue.clear()
        self._current_move = None
        self._is_processing = False
        self._waiting_for_client = False

    def run_animation(self, cube: "Cube", op: "OpProtocol", alg: "SimpleAlg") -> None:
        """Queue a move for animated playback.

        In queue mode (default): non-blocking, queues and returns.
        In blocking mode: blocks caller until client animation completes.
        """
        assert self._window is not None

        if self._event_loop is None:
            raise RuntimeError("EventLoop is required for animation. Call set_event_loop() first.")

        if self._event_loop.has_exit:
            return

        if self._blocking_mode:
            self._run_blocking(cube, op, alg)
            return

        self._move_queue.append(_QueuedMove(cube, op, alg))

        if not self._is_processing and not self._waiting_for_client:
            self._process_next()

    def on_client_animation_done(self) -> None:
        """Called when client sends animation_done — process next queued move.

        In blocking mode: unblocks the solver thread instead of processing queue.
        """
        if self._blocking_mode:
            self._blocking_event.set()
            return
        self._waiting_for_client = False
        self._process_next()

    def _run_blocking(self, cube: "Cube", op: "OpProtocol", alg: "SimpleAlg") -> None:
        """Run a single move in blocking mode (called from solver thread).

        For non-animatable moves: applies and sends state, returns immediately.
        For animatable moves: applies, sends animation_start, then blocks
        on _blocking_event until the client signals animation_done.
        """
        move = _QueuedMove(cube, op, alg)

        # Non-animatable moves: apply and return immediately
        if isinstance(alg, algs.AnnotationAlg):
            self._apply_model_change(move)
            if self._web_window:
                self._web_window.send_state()
            return

        if not isinstance(alg, algs.AnimationAbleAlg):
            self._apply_model_change(move)
            if self._web_window:
                self._web_window.send_state()
            return

        if alg.n % 4 == 0:
            self._apply_model_change(move)
            if self._web_window:
                self._web_window.send_state()
            return

        # Animatable move: apply, send animation_start, BLOCK
        duration_ms = self._get_animation_duration_ms()
        self._apply_model_change(move)

        if self._web_window:
            self._web_window.send_animation_start(alg, duration_ms, is_undo=self._is_undo)
            self._web_window.send_state()

        # Block solver thread until client signals animation_done
        self._blocking_event.clear()
        self._blocking_event.wait()

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
        if self._on_queue_drained:
            self._on_queue_drained()

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
