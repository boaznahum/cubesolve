import functools
from collections.abc import MutableSequence, Sequence
from contextlib import contextmanager
from typing import Callable, Any, TYPE_CHECKING

from .. import config
from ..algs import Alg, SimpleAlg, Annotation
from ..animation.animation_manager import AnimationManager
from ..animation.animation_manager import OpProtocol
from ..app_exceptions import OpAborted
from ..app_state import ApplicationAndViewState
from ..model.cube import Cube

if TYPE_CHECKING:
    from cube.operator.op_annotation import OpAnnotation


class Operator:
    __slots__ = ["_cube", "_history",
                 "_self_annotation_running",
                 "_aborted",
                 "_animation_running",
                 "_animation_enabled",
                 "_animation_manager",
                 "_app_state",
                 "_annotation"]

    def __init__(self, cube: Cube,
                 app_state: ApplicationAndViewState,  # PATCH, operator should hold SS mode
                 animation_manager: AnimationManager = None,
                 animation_enabled: bool = False) -> None:
        super().__init__()
        self._aborted: Any = None
        self._cube = cube
        self._history: MutableSequence[Alg] = []

        # why we need both
        self._animation_running = False
        self._animation_manager = animation_manager
        self._animation_enabled: bool = animation_enabled

        self._app_state = app_state
        self._self_annotation_running = False

        from cube.operator.op_annotation import OpAnnotation
        self._annotation: OpAnnotation = OpAnnotation(self)

    def check_clear_rais_abort(self):
        if self._aborted:
            self._aborted = False
            print(f"A signal abort was raise, not in loop, raising an exception {OpAborted}")
            raise OpAborted()

    def op(self, alg: Alg, inv: bool = False, animation=True):

        """
        Animation can run only from top level, not from animation itself
        :param alg:
        :param inv:
        :param animation:
        :return:
        """

        log_path = config.OPERATION_LOG_PATH if config.OPERATION_LOG else None

        # noinspection PyUnusedLocal
        def log(*s: Any):
            if log_path:
                with open(log_path, mode="a") as f:
                    print(*(str(x) for x in s), file=f)

        # if we clean signal here, then we have a problem, because
        # solver run op in loop, so we will miss the latest signal,
        # so maybe we need seperated method for single op and a long op

        # log("At entry, big alg:", str(alg))

        self.check_clear_rais_abort()

        if animation and self.animation_enabled and not self._animation_running:

            def _do_animation():
                nonlocal alg
                with self._w_with_animation:

                    an: Callable[[Cube, OpProtocol, SimpleAlg], None] | None = self._animation_manager.run_animation
                    assert an  # just to make mypy happy
                    if inv:
                        alg = alg.inv()

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
                           not self._self_annotation_running and not isinstance(alg, Annotation))

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

            if alg.is_ann:
                return

            if inv:
                alg = alg.inv()

            self._cube.sanity()
            alg.play(self._cube, False)
            self._cube.sanity()
            self._history.append(alg)

    def undo(self, animation=True) -> Alg | None:

        """
        :return: the undo alg
        """
        with self.with_animation(animation=False):
            if self.history:
                alg = self._history.pop()
                _history = [*self._history]
                self.op(alg, True, animation)
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
    def history(self) -> Sequence[Alg]:
        return self._history

    @property
    def count(self):
        return functools.reduce(lambda n, a: n + a.count(), self._history, 0)

    def reset(self):
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
    def animation_enabled(self):
        return self._animation_enabled and self._animation_manager

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
