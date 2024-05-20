from abc import ABC
from collections.abc import Iterator
from typing import final

from cube.algs.Alg import Alg
from cube.algs.AnnoationAlg import AnnotationAlg
from cube.algs.SeqAlg import SeqAlg, SeqSimpleAlg
from cube.algs.SimpleAlg import NSimpleAlg, SimpleAlg
from cube.algs._internal_utils import _normalize_for_count
from cube.model import Cube


@final
class _Mul(Alg, ABC):
    __slots__ = ["_alg", "_n"]

    def __init__(self, a: Alg, n: int) -> None:

        assert n >= 0  # otherwise, I don't know how to simplify it
        super().__init__()
        self._alg = a
        self._n = n

    def atomic_str(self) -> str:

        if isinstance(self._alg, NSimpleAlg):
            return self.simplify().atomic_str()  # R3 -> R'

        s = self._alg.atomic_str()

        if self._n != 1:
            s += str(self._n)

        return s

    def play(self, cube: Cube, inv: bool = False):

        for _ in range(0, self._n):
            self._alg.play(cube, inv)

    def count(self) -> int:
        if not isinstance(self._alg, SeqAlg):
            return _normalize_for_count(self._n) * self._alg.count()
        else:
            return self._n * self._alg.count()

    def xsimplify(self) -> "SimpleAlg|SeqSimpleAlg":

        a = self._alg.simplify()  # can't be _Mul

        if isinstance(a, NSimpleAlg):
            s = a.clone()
            s *= self._n  # multipy by me - that is my function
            return s.simplify()
        elif isinstance(a, AnnotationAlg):
            return a
        elif isinstance(self._alg, SeqAlg):
            # noinspection PyProtectedMember
            algs = [a.simplify() for a in self._alg._algs] * self._n
            return SeqAlg(None, *algs).simplify()
        else:
            raise TypeError("Unknown type:", type(self))

    def flatten(self) -> Iterator["SimpleAlg"]:
        me = [* self._alg.flatten() ]
        for _ in range(0, self._n):
            yield from me


