from collections.abc import MutableSequence, Sequence

from algs import Alg
from cube import Cube


class Operator:
    __slots__ = ["_cube", "_history"]

    def __init__(self, cube: Cube) -> None:
        super().__init__()
        self._cube = cube
        self._history: MutableSequence[Alg] = []

    def op(self, alg: Alg, inv: bool = False):
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

    def reset(self):
        self._cube.reset()
        self._history.clear()

    def undo(self):
        if self.history:
            alg = self._history.pop()
            alg.play(self._cube, True)

