from abc import ABC
from collections.abc import Iterator
from typing import final
from typing_extensions import override

from cube.domain.algs._internal_utils import _normalize_for_count
from cube.domain.algs.Alg import Alg
from cube.domain.algs.AnnotationAlg import AnnotationAlg
from cube.domain.algs.SeqAlg import SeqAlg, SeqSimpleAlg
from cube.domain.algs.SimpleAlg import NSimpleAlg, SimpleAlg
from cube.domain.model.Cube import Cube


@final
class _Mul(Alg, ABC):
    """
    Multiplication (repetition) of an algorithm.
    All instances are frozen (immutable) after construction.
    """

    __slots__ = ("_alg", "_n")

    def __init__(self, a: Alg, n: int) -> None:

        assert n >= 0  # otherwise, I don't know how to simplify it
        super().__init__()
        self._alg = a
        self._n = n
        self._freeze()

    def atomic_str(self) -> str:

        if isinstance(self._alg, NSimpleAlg):
            return self.simplify().atomic_str()  # R3 -> R'

        s = self._alg.atomic_str()

        if self._n != 1:
            # Avoid ambiguity: if inner str ends with a digit (e.g., "r'3"),
            # appending "2" would produce "r'32" (parsed as r'*32 not (r'*3)*2).
            # Wrap in parentheses: "(r'3)2"
            if s and s[-1].isdigit():
                s = "(" + s + ")"
            s += str(self._n)

        return s

    def play(self, cube: Cube, inv: bool = False) -> None:

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
            # Use simple_mul() instead of clone() * self._n
            s = a.simple_mul(self._n)
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
        me = [*self._alg.flatten()]
        if len(me) == 1 and isinstance(me[0], NSimpleAlg):
            # Single move: B*2 -> B2 (combine n), not B, B
            result = me[0].simple_mul(self._n)
            if result.n % 4:
                yield result
            # else: identity (e.g., B*4), yield nothing
        else:
            # Sequence: (A B)*2 -> A B A B
            for _ in range(0, self._n):
                yield from me

    @override
    def count_simple(self) -> int:
        return self._n * self._alg.count_simple()




