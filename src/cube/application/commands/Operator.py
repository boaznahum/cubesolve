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
from cube.domain.algs.SeqAlg import SeqAlg
from cube.domain.algs.SimpleAlg import SimpleAlg
from cube.domain.model.Cube import Cube
from cube.utils.SSCode import SSCode

from ...domain.solver.protocols.AnnotationProtocol import AnnotationProtocol
from ...domain.solver.protocols.OperatorProtocol import OperatorProtocol
from ...utils.service_provider import IServiceProvider

if TYPE_CHECKING:
    from ..animation.AnimationManager import AnimationManager, OpProtocol


class Operator(OperatorProtocol):
    __slots__ = ["_cube",
                 "_history",
                 "_recording",
                 "_self_annotation_running",
                 "_aborted",
                 "_animation_running",
                 "_animation_enabled",
                 "_animation_manager",
                 "_app_state",
                 "_annotation",
                 "_log_path"]

    def __init__(self, cube: Cube,
                 app_state: ApplicationAndViewState,
                 animation_manager: 'AnimationManager | None' = None,
                 animation_enabled: bool = False) -> None:
        super().__init__()

        self._aborted: Any = None
        self._cube = cube
        self._history: MutableSequence[Alg] = []

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
            self._annotation = NoopAnnotation()

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
        deprecated, use play
        Animation can run only from top level, not from animation itself
        :param alg:
        :param inv:
        :param animation: if true and animation is enabled(globally, toggle_animation_on)
        then run with animation.
        Doesn't force animation to true if animation is not enabled.
        So it can only turn off current global animation
        :return:
        """
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
                return

            if self._recording is not None:
                self._recording.append(alg)

            self.log("Operator", alg)

            self._cube.sanity()
            alg.play(self._cube, False)
            self._cube.sanity()
            self._history.append(alg)

    def play_seq(self, algs: Reversible[Alg], inv: Any):

        if inv:
            for alg in reversed(algs):
                self.play(alg, True)
        else:
            for alg in algs:
                self.play(alg, inv)

    def undo(self, animation=True) -> Alg | None:

        """
        :return: the undo alg
        """
        # with self.with_animation(animation=False):
        if self.history():
            alg = self._history.pop()
            _history = [*self._history]
            self.play(alg, True, animation=animation)
            # do not add to history !!! otherwise history will never shrink
            # because op may break big algs to steps, and add more than one , we can't just pop
            # self._history.pop()
            self._history[:] = _history
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

    def reset(self):
        """
        Reset the cube and clear the history.
        So,:meth: `count` will return zero
        :return:
        """
        self._aborted = False
        self._cube.reset()
        self._history.clear()

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

    @contextmanager
    def with_query_restore_state(self):
        """
        Context manager for "what-if" queries that auto-rollback cube state.

        Use this to test solving strategies, detect parity, or check conditions
        without permanently modifying the cube. All moves made inside the context
        are automatically undone on exit.

        Behavior:
            - Enables query mode (skips texture/GUI updates for performance)
            - Disables animation
            - Records history length on entry
            - On exit: undoes all moves back to original state
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

        See Also:
            CubeQueries2.rotate_and_check: Similar but operates directly on cube
            without operator (no history tracking).
        """
        cube = self._cube

        # Save original states
        was_in_query_mode = cube._in_query_mode
        history_len_before = len(self._history)

        # CLAUDE [#8]: move the query mode context manager to cube itself, this is not OOP programming
        cube._in_query_mode = True

        with self.with_animation(animation=False):
            try:
                yield None
            finally:
                # Rollback: undo all moves made during query
                while len(self._history) > history_len_before:
                    self.undo(animation=False)

                cube._in_query_mode = was_in_query_mode

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
