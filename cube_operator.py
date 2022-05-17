import functools
from collections.abc import MutableSequence, Sequence, Iterable
from contextlib import contextmanager
from typing import Callable


from algs import Alg, SimpleAlg
from cube import Cube


class Operator:
    __slots__ = ["_cube", "_history", "_animation_hook", "_animation_running"]

    def __init__(self, cube: Cube) -> None:
        super().__init__()
        self._cube = cube
        self._history: MutableSequence[Alg] = []
        self._animation_hook: Callable[["Operator", SimpleAlg], None] | None = None
        self._animation_running = False

    def op(self, alg: Alg, inv: bool = False, animation=True):

        if animation and self._animation_hook:

            with self._w_with_animation:

                an = self._animation_hook
                if inv:
                    alg = alg.inv()

                algs: Iterable[SimpleAlg] = alg.flatten()

                algs = [*algs]  # for debug only
                for a in algs:
                    an(self, a)  # --> this will call me again, but animation will self, so we reach the else branch
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
                _history = [ * self._history ]
                self.op(alg, True, animation)
                # do not add to history !!! otherwise history will never shrink
                # becuase op may break big algs to steps, and add more than one , we can't just pop
                #self._history.pop()
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
        _history = [* self._history ]
        try:
            yield None
        finally:
            self._history[:] = _history

    @property
    def is_with_animation(self):
        return self._animation_hook

    @property
    def is_animation_running(self):
        return self._animation_running

    @property
    @contextmanager
    def _w_with_animation(self):
        b = self._animation_running
        self._animation_running = True

        try:
            yield None
        finally:
            self._animation_running=b

