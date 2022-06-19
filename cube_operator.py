import functools
from collections.abc import MutableSequence, Sequence, Iterable
from contextlib import contextmanager
from typing import Callable, Any, List

from algs.algs import Alg, SimpleAlg
from app_exceptions import OpAborted
from app_state import AppandViewState
from model.cube import Cube


class Operator:
    __slots__ = ["_cube", "_history", "_animation_hook", "_animation_running",
                 "_aborted", "_animation_enabled",
                 "_app_state"]

    def __init__(self, cube: Cube,
                 app_state: AppandViewState,  #PATCH PATCH, operator should hold SS mode
                 animation_enabled: bool = False) -> None:
        super().__init__()
        self._aborted: Any = None
        self._cube = cube
        self._history: MutableSequence[Alg] = []
        self._animation_hook: Callable[["Operator", SimpleAlg], None] | None = None
        self._animation_running = False
        self._animation_enabled: bool = animation_enabled
        self._app_state = app_state

    def op(self, alg: Alg, inv: bool = False, animation=True):

        """
        Animation can run only from top level, not from animation itself
        :param alg:
        :param inv:
        :param animation:
        :return:
        """

        # if we clean signal here, then we have a problem, because
        # solver run op in loop, so we will miss the latest signal,
        # so maybe we need seperated method for single op and a long op

        if self._aborted:
            self._aborted = False
            print(f"A signal abort was raise, not in loop, raising an exception {OpAborted}")
            raise OpAborted()

        if animation and self.animation_enabled:

            with self._w_with_animation:

                an: Callable[[Operator, SimpleAlg], None] | None = self._animation_hook
                assert an  # just to make mypy happy
                if inv:
                    alg = alg.inv()

                # todo: Patch - move singlestep mode into operator
                algs: list[SimpleAlg] = [ * alg.flatten() ]

                if self._app_state.single_step_mode:
                    print(f"In SS mode: going to run: {' '.join([ str(a) for a in algs ])}")

                for a in algs:
                    an(self, a)  # --> this will call me again, but animation will self, so we reach the else branch
                    if self._aborted:
                        self._aborted = False
                        print(f"A signal abort was raise, raising an exception {OpAborted}")
                        raise OpAborted()
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
        with self.suspended_animation(False):
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
    def suspended_animation(self, suspend=True):

        if suspend:
            an = self._animation_hook
            self._animation_hook = None
            try:
                yield None
            finally:
                self._animation_hook = an
        else:
            yield None

    @contextmanager
    def save_history(self):
        _history = [*self._history]
        try:
            yield None
        finally:
            self._history[:] = _history

    @property
    def is_with_animation(self):
        return self._animation_hook and self._animation_hook

    @property
    def is_animation_running(self):
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
        return self._animation_enabled and self._animation_hook

    def toggle_animation_on(self, enable: bool|None =None):

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
