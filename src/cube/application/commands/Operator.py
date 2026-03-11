import functools
import warnings
from collections.abc import MutableSequence, Reversible, Sequence
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Callable

from typing_extensions import deprecated

from cube.application.exceptions.app_exceptions import OpAborted
from cube.application.state import ApplicationAndViewState
from cube.domain.algs.Alg import Alg
from cube.domain.algs.Algs import Algs
from cube.domain.algs.AnnotationAlg import AnnotationAlg
from cube.domain.algs.HeadingAlg import HeadingAlg
from cube.domain.algs.SeqAlg import SeqAlg
from cube.domain.algs.SimpleAlg import SimpleAlg
from cube.domain.model.Cube import Cube
from cube.utils.SSCode import SSCode

from ...domain.solver.protocols.AnnotationProtocol import AnnotationProtocol
from ...domain.solver.protocols.OperatorProtocol import OperatorProtocol
from ...utils.service_provider import IServiceProvider

if TYPE_CHECKING:
    from ..animation.AnimationManager import AnimationManager, OpProtocol


class OperatorBuffer:
    """Handle yielded by Operator.with_buffer() for explicit flush control.

    Auto-flush on AnnotationAlg and context exit still happen.
    This just adds an explicit flush() call for when the solver
    needs to query cube state mid-buffer.

    Can only be used inside the ``with op.with_buffer() as buffer:`` block.
    """

    __slots__ = ["_operator", "_active"]

    def __init__(self, operator: "Operator") -> None:
        self._operator = operator
        self._active: bool = True

    def flush(self) -> None:
        """Explicitly flush the buffer: simplify + play buffered moves.

        After flush, the cube state is up-to-date and safe to query.
        Buffering continues — subsequent op.play() calls still buffer.

        Raises:
            RuntimeError: If called outside the with_buffer() context.
        """
        if not self._active:
            raise RuntimeError("OperatorBuffer.flush() can only be called inside with_buffer() context")
        self._operator._flush_buffer()

    def _deactivate(self) -> None:
        """Mark this handle as inactive (called by with_buffer __exit__)."""
        self._active = False


class Operator(OperatorProtocol):
    __slots__ = ["_cube",
                 "_history",
                 "_redo_queue",
                 "_in_undo_redo",
                 "_recording",
                 "_self_annotation_running",
                 "_aborted",
                 "_animation_running",
                 "_animation_enabled",
                 "_animation_manager",
                 "_app_state",
                 "_annotation",
                 "_log_path",
                 "_buffer",
                 "_buffer_depth"]

    def __init__(self, cube: Cube,
                 app_state: ApplicationAndViewState,
                 animation_manager: 'AnimationManager | None' = None,
                 animation_enabled: bool = False) -> None:
        super().__init__()

        self._aborted: Any = None
        self._cube = cube
        self._history: MutableSequence[Alg] = []
        self._redo_queue: MutableSequence[Alg] = []
        self._in_undo_redo: bool = False

        # a non none indicates that recorder is running
        self._recording: MutableSequence[Alg] | None = None

        # why we need both

        # indicate that this operator has invoked animation amanager
        #  and reentry to op comes from animation
        self._animation_running = False
        self._animation_manager = animation_manager
        self._animation_enabled: bool = animation_enabled

        self._app_state = app_state
        self._self_annotation_running = False

        if animation_manager is not None:
            from cube.application.commands.op_annotation import OpAnnotation
            self._annotation: AnnotationProtocol = OpAnnotation(self)
        else:
            from cube.domain.solver.protocols.NoopAnnotation import NoopAnnotation
            self._annotation = NoopAnnotation(self)

        # Buffer mode: list of algs waiting to be flushed, or None if not buffering
        self._buffer: MutableSequence[Alg] | None = None
        self._buffer_depth: int = 0  # nesting depth for with_buffer()

        # Get config from app_state
        cfg = app_state.config
        self._log_path = cfg.operation_log_path if cfg.operation_log else None

    @property
    def app_state(self) -> ApplicationAndViewState:
        return self._app_state

    def check_clear_rais_abort(self):
        if self._aborted:
            self._aborted = False
            self._app_state.debug(True, f"A signal abort was raise, not in loop, raising an exception {OpAborted}")
            raise OpAborted()

    def play(self, alg: Alg, inv: Any = False, animation: Any = True) -> None:
        """
        Execute an algorithm on the cube.

        If inside a with_buffer() context and buffer mode is enabled:
        - AnnotationAlg triggers a flush before playing the annotation immediately
        - Other algs are buffered (not played until flush)

        :param alg:
        :param inv:
        :param animation: if true and animation is enabled(globally, toggle_animation_on)
        then run with animation.
        Doesn't force animation to true if animation is not enabled.
        So it can only turn off current global animation
        :return:
        """
        if self._buffer is not None:
            is_annotation = isinstance(alg, AnnotationAlg)
            if is_annotation:
                # Flush buffer before annotation, then play annotation immediately
                self._flush_buffer()
                self._play(alg, inv, animation)
            else:
                # Buffer the alg (apply inv now so buffer contains resolved algs)
                if inv:
                    alg = alg.inv()
                self._buffer.append(alg)
        else:
            self._play(alg, inv, animation)

    @deprecated("Use play() instead")
    def op(self, alg: Alg, inv: bool = False, animation: bool = True) -> None:
        warnings.warn("Use play", DeprecationWarning, 2)

        self._play(alg, inv, animation)

    # noinspection PyMethodMayBeStatic
    def log(self, *s: Any):

        if ll := self._log_path:
            with open(ll, mode="a") as f:
                print(*(str(x) for x in s), file=f)

    def _play(self, alg: Alg, inv: Any = False, animation: Any = True) -> None:

        """
        deprecated, use play
        Animation can run only from top level, not from animation itself
        :param alg:
        :param inv:
        :param animation: if true and animation is enabled then run with animation.
        Doesn't force animation to true if animation is not enabled

        :return:
        """

        # noinspection PyUnusedLocal

        # if we clean signal here, then we have a problem, because
        # solver run op in loop, so we will miss the latest signal,
        # so maybe we need seperated method for single op and a long op

        # log("At entry, big alg:", str(alg))

        self.check_clear_rais_abort()

        op_current_running = self._animation_running

        is_annotation = isinstance(alg, AnnotationAlg)

        if not is_annotation:
            if inv:
                alg = alg.inv()

        if animation and self.animation_enabled and not op_current_running:

            def _do_animation() -> None:
                nonlocal alg
                with self._w_with_animation:

                    assert self._animation_manager
                    an: Callable[[Cube, OpProtocol, SimpleAlg], None] | None = self._animation_manager.run_animation
                    assert an  # just to make mypy happy

                    # TODO [#9]: Move single step mode handling into operator
                    algs: list[SimpleAlg] = [*alg.flatten()]

                    if self._app_state.single_step_mode:
                        self._app_state.debug(True,
                                              lambda: f"In SS mode: going to run: {' '.join([str(a) for a in algs])}")

                    cube = self.cube
                    op = self.play

                    for a in algs:
                        # --> this will call me again, but animation will self, so we reach the else branch
                        an(cube, op, a)
                        self.check_clear_rais_abort()

            do_self_ann = (self._app_state.config.operator_show_alg_annotation and
                           not self._self_annotation_running and not isinstance(alg, AnnotationAlg))

            if do_self_ann:

                # prevent recursion
                self._self_annotation_running = True
                try:
                    ann = self._annotation
                    with ann.annotate(h3=str(alg)):
                        _do_animation()
                finally:
                    self._self_annotation_running = False
            else:
                _do_animation()

        else:

            if is_annotation:
                if isinstance(alg, HeadingAlg):
                    # HeadingAlg survives in history for queue display
                    self._history.append(alg)
                return

            if self._recording is not None:
                self._recording.append(alg)

            self.log("Operator", alg)

            self._cube.sanity()
            alg.play(self._cube, False)
            self._cube.sanity()
            self._history.append(alg)
            # Note: redo queue is NOT cleared on manual moves.
            # Unlike text editors, clearing the solver's redo queue on an
            # accidental key press is destructive. The queue is only cleared
            # explicitly (reset, new scramble, new solve).

    def play_seq(self, algs: Reversible[Alg], inv: Any):

        if inv:
            for alg in reversed(algs):
                self.play(alg, True)
        else:
            for alg in algs:
                self.play(alg, inv)

    def undo(self, animation: bool = True) -> Alg | None:
        """Undo the last operation. Pushes undone alg to redo queue.

        :return: the undone alg, or None if history is empty
        """
        if self.history():
            alg = self._history.pop()
            _history = [*self._history]
            self._in_undo_redo = True
            try:
                self.play(alg, True, animation=animation)
            finally:
                self._in_undo_redo = False
            # Restore history (play() adds to it, but undo shouldn't grow history)
            self._history[:] = _history
            self._redo_queue.append(alg)
            return alg
        else:
            return None

    def redo(self, animation: bool = True) -> Alg | None:
        """Redo the last undone operation. Pops from redo queue and plays forward.

        :return: the redone alg, or None if redo queue is empty
        """
        if self._redo_queue:
            alg = self._redo_queue.pop()
            self._in_undo_redo = True
            try:
                self.play(alg, animation=animation)
            finally:
                self._in_undo_redo = False
            return alg
        else:
            return None

    @property
    def cube(self) -> Cube:
        return self._cube

    @property
    def sp(self) -> IServiceProvider:
        """Get the service provider."""
        return self.cube.sp


    def redo_queue(self) -> Sequence[Alg]:
        """Get the redo queue (operations available for redo)."""
        return self._redo_queue[:]

    def clear_redo(self) -> None:
        """Clear the redo queue."""
        self._redo_queue.clear()

    def enqueue_redo(self, algs: Sequence[Alg]) -> None:
        """Replace the redo queue with the given algorithms (e.g., solver solution).

        Stores in reversed order so that pop() (LIFO) yields the first step
        first — matching the same pop() semantics used by manual undo/redo.
        """
        self._redo_queue.clear()
        self._redo_queue.extend(reversed(algs))

    def history(self, *, remove_scramble: bool = False) -> Sequence[Alg]:
        """
        Remove top scrambles
        :param remove_scramble:
        :return:
        """

        history = self._history

        _is = Algs.is_scramble

        if remove_scramble:
            history = [a for a in history if not _is(a)]
        return history[:]

    def history_as_alg(self) -> Alg:
        return SeqAlg(None, *self.history())

    def toggle_recording(self) -> Sequence[Alg] | None:
        """
        If recording is on stop it nad return the recording, can be empty
        otherwise, start the recording and return None
        :return:
        """

        if self._recording is None:
            self._recording = []
            return None
        else:
            r = self._recording
            self._recording = None
            return r

    @property
    def is_recording(self) -> bool:
        return self._recording is not None

    @property
    def count(self):
        return functools.reduce(lambda n, a: n + a.count(), self._history, 0)

    def reset(self) -> None:
        """
        Reset the cube and clear the history and redo queue.
        So,:meth: `count` will return zero
        :return:
        """
        self._aborted = False
        self._cube.reset()
        self._history.clear()
        self._redo_queue.clear()

    @contextmanager
    def with_animation(self, animation: bool | None = None):

        """

        :param animation: None don't change current, False/True force False/True
        :return:
        """

        if animation is None:
            yield None  # leave the default
        else:
            an = self._animation_enabled
            self._animation_enabled = animation
            try:
                yield None
            finally:
                self._animation_enabled = an

    @contextmanager
    def save_history(self):
        _history = [*self._history]
        try:
            yield None
        finally:
            self._history[:] = _history

    def _flush_buffer(self) -> None:
        """Flush the buffer: simplify buffered algs, then play each one.

        Private — called by with_buffer().__exit__ and by play() when an AnnotationAlg
        is encountered while buffering.
        """
        buf = self._buffer
        if not buf:
            return

        # Build a single alg from buffer, simplify, then play each result
        combined = SeqAlg(None, *buf)
        simplified = combined.simplify()
        buf.clear()

        # Temporarily disable buffering to play the simplified algs
        # (self.play() won't re-buffer since _buffer is None)
        saved_buffer = self._buffer
        self._buffer = None
        try:
            for a in simplified.flatten():
                self.play(a)
        finally:
            self._buffer = saved_buffer

    @contextmanager
    def with_query_restore_state(self):
        """
        Context manager for "what-if" queries that auto-rollback cube state.

        Use this to test solving strategies, detect parity, or check conditions
        without permanently modifying the cube. All moves made inside the context
        are automatically undone on exit.

        Behavior:
            - If inside with_buffer(): flushes buffer first, disables buffering during query
            - Enables query mode (skips texture/GUI updates for performance)
            - Disables animation
            - Records history length on entry
            - On exit: undoes all moves back to original state, restores buffer state
            - Supports nesting

        Example:
            with op.with_query_restore_state():
                solver.solve()  # Try solving
                if cube.solved:
                    detected_parity = False
            # Cube is back to original state here

        Warning:
            Direct cube manipulation (cube.rotate() without operator) inside
            the context will NOT be rolled back - only operator moves are tracked.
        """
        # Flush and temporarily disable buffering — query needs accurate cube state
        saved_buffer = self._buffer
        saved_depth = self._buffer_depth
        if saved_buffer is not None:
            self._flush_buffer()
        self._buffer = None
        self._buffer_depth = 0

        cube = self._cube

        # Save original states
        was_in_query_mode = cube._in_query_mode
        history_len_before = len(self._history)
        saved_redo_queue = [*self._redo_queue]

        # CLAUDE [#8]: move the query mode context manager to cube itself, this is not OOP programming
        cube._in_query_mode = True

        with self.with_animation(animation=False):
            try:
                yield None
            finally:
                # Rollback: undo all moves made during query
                while len(self._history) > history_len_before:
                    self.undo(animation=False)

                # Restore redo queue — undo() above pollutes it with query moves
                self._redo_queue[:] = saved_redo_queue

                cube._in_query_mode = was_in_query_mode

                # Restore buffer state
                self._buffer = saved_buffer
                self._buffer_depth = saved_depth

    @property
    def is_animation_running(self):
        """

        :return: bool(True) when operator invokes animation hook
        """
        return self._animation_running

    @property  # type: ignore
    @contextmanager
    def _w_with_animation(self):
        b = self._animation_running
        self._animation_running = True

        try:
            yield None
        finally:
            self._animation_running = b

    @property
    def aborted(self):
        return self._aborted

    @property
    def animation_enabled(self) -> bool:
        """

        :return: converted to bool true if animation is enabled and animation manager is set
        """
        return bool(self._animation_enabled and self._animation_manager)

    def enter_single_step_mode(self, code: SSCode | None = None) -> None:
        """
        Enable single-step mode for debugging.

        When enabled, animation will pause after each algorithm and wait
        for user input (Space key or GUI button) before continuing.

        Args:
            code: Optional SSCode identifying the trigger point. If provided,
                  single-step mode is only enabled if the code is enabled in
                  config (SS_CODES). If None, always enters single-step mode.

        Use this at critical points in solver code to inspect cube state:
            self._op.enter_single_step_mode(SSCode.NxN_CORNER_PARITY_FIX)
        """
        if code is None or self._app_state.config.is_ss_code_enabled(code):
            self._app_state.single_step_mode = True

    def enable_animation(self, am: 'AnimationManager', animation_enabled: bool) -> None:
        """Inject animation support after construction.

        Called by App.enable_animation() when a GUI backend provides an
        AnimationManager.  Must only be called once (before any play() calls).
        """
        assert self._animation_manager is None, "enable_animation() called twice"
        self._animation_manager = am
        self._animation_enabled = animation_enabled

        from cube.application.commands.op_annotation import OpAnnotation
        self._annotation = OpAnnotation(self)

    def toggle_animation_on(self, enable: bool | None = None):

        if enable is None:
            self._animation_enabled = not self._animation_enabled
        else:
            self._animation_enabled = bool(enable)

    def abort(self):
        """
        When operator is back to main loop, it will raise an exception
        Only animation from top can be aborted
        :return:
        """
        self._app_state.debug(True, "Operator: raised an abort signal")
        self._aborted = True

    @property
    def annotation(self) -> AnnotationProtocol:
        return self._annotation
