import functools
from abc import ABC, abstractmethod
from collections.abc import MutableSequence, Sequence, Iterable
from contextlib import contextmanager
from typing import Callable

from algs import Alg, SimpleAlg
from cube import Cube




class Operator:
    __slots__ = ["_cube", "_history", "_animation_hook"]

    def __init__(self, cube: Cube) -> None:
        super().__init__()
        self._cube = cube
        self._history: MutableSequence[Alg] = []
        self._animation_hook: Callable[["Operator", SimpleAlg], None] |None = None

    def op(self, alg: Alg, inv: bool = False, animation=True):

        if animation and self._animation_hook:
            an = self._animation_hook

            # just in case
            self._animation_hook = None
            try:
                if inv:
                    alg = alg.inv()

                algs: Iterable[SimpleAlg] = alg.flatten()

                algs = [* algs ] # for debug only
                for a in algs:
                    an(self, a)
            finally:
                self._animation_hook = an
        else:
            if inv:
                alg = alg.inv()

            self._cube.sanity()
            alg.play(self._cube, False)
            self._cube.sanity()
            self._history.append(alg)

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

    def undo(self) -> Alg | None:
        """

        :return: the undo alg
        """
        if self.history:
            alg = self._history.pop()
            alg.play(self._cube, True)
            return alg
        else:
            return None

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

