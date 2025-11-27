import functools
import warnings
from collections.abc import MutableSequence, Sequence, Reversible
from contextlib import contextmanager
from typing import Callable, Any, TYPE_CHECKING

from .. import config
from ..algs import Alg, AnnotationAlg, SimpleAlg, Algs, SeqAlg
from cube.app.app_exceptions import OpAborted
from cube.app.app_state import ApplicationAndViewState
from ..model.cube import Cube

if TYPE_CHECKING:
    from ..animation.animation_manager import AnimationManager, OpProtocol
    from cube.operator.op_annotation import OpAnnotation


class Operator:
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
                 app_state: ApplicationAndViewState | None = None, # will be created if None
                 animation_manager: 'AnimationManager | None' = None,
                 animation_enabled: bool = False) -> None:
        super().__init__()

        if app_state is None:
            app_state = ApplicationAndViewState()

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

        from cube.operator.op_annotation import OpAnnotation
        self._annotation: OpAnnotation = OpAnnotation(self)

        self._log_path = config.OPERATION_LOG_PATH if config.OPERATION_LOG else None

    def check_clear_rais_abort(self):
        if self._aborted:
            self._aborted = False
            print(f"A signal abort was raise, not in loop, raising an exception {OpAborted}")
            raise OpAborted()

    def play(self, alg: Alg, inv: Any = False, animation: Any = True):
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
        return self._play(alg, inv, animation)

    def op(self, alg: Alg, inv: bool = False, animation=True):
        warnings.warn("Use play", DeprecationWarning, 2)

        return self._play(alg, inv, animation)

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

                    # todo: Patch - move single step mode into operator
                    algs: list[SimpleAlg] = [*alg.flatten()]

                    if self._app_state.single_step_mode:
                        print(f"In SS mode: going to run: {' '.join([str(a) for a in algs])}")

                    cube = self.cube
                    op = self.op

                    for a in algs:
                        # --> this will call me again, but animation will self, so we reach the else branch
                        an(cube, op, a)
                        self.check_clear_rais_abort()

            do_self_ann = (config.OPERATOR_SHOW_ALG_ANNOTATION and
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
                self.op(alg, True)
        else:
            for alg in algs:
                self.op(alg, inv)

    def undo(self, animation=True) -> Alg | None:

        """
        :return: the undo alg
        """
        # with self.with_animation(animation=False):
        if self.history():
            alg = self._history.pop()
            _history = [*self._history]
            self.op(alg, True, animation=animation)
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
        print("Operator: raised an abort signal")
        self._aborted = True

    @property
    def app_state(self) -> ApplicationAndViewState:
        return self._app_state

    @property
    def annotation(self) -> "OpAnnotation":
        return self._annotation
