from typing import TYPE_CHECKING, Iterator

from cube.domain.algs.AnnotationAlg import AnnotationAlg
from cube.domain.model.Cube import Cube

from .Alg import Alg

if TYPE_CHECKING:
    from .SeqAlg import SeqSimpleAlg
    from .SimpleAlg import SimpleAlg


class _Inv(Alg):
    """
    Inverse of an algorithm.
    All instances are frozen (immutable) after construction.
    """
    from .SeqAlg import SeqAlg
    from .SimpleAlg import NSimpleAlg

    __slots__ = ("_alg",)

    def __init__(self, _a: Alg) -> None:
        super().__init__()
        self._alg = _a
        self._freeze()

    def __str__(self) -> str:
        return self._alg.atomic_str() + "'"

    def play(self, cube: Cube, inv: bool = False) -> None:
        self._alg.play(cube, not inv)

    def inv(self) -> Alg:
        return self._alg

    def atomic_str(self) -> str:
        return self._alg.atomic_str() + "'"

    def count(self) -> int:
        return self._alg.count()

    def xsimplify(self) -> "SimpleAlg|SeqSimpleAlg":

        """
        Must returns SimpleAlg if _alg is SimpleAlg
        :return:
        """

        if isinstance(self._alg, _Inv):
            # X'' = X
            return self._alg._alg.simplify()

        a = self._alg.simplify()  # can't be _Mul, nor Inv

        if isinstance(a, _Inv.NSimpleAlg):
            # Use simple_inverse() instead of clone() * -1
            s = a.simple_inverse()
            return s.simplify()
        elif isinstance(a, AnnotationAlg):
            return a
        elif isinstance(a, _Inv.SeqAlg):

            algs = [a.inv() for a in reversed(a.algs)]
            return _Inv.SeqAlg(None, *algs).simplify()
        else:
            raise TypeError("Unknown type:", type(self))

    def flatten(self) -> Iterator["SimpleAlg"]:

        # can't reverse Iterator
        flat = [*self._alg.flatten()]

        for a in reversed(flat):
            yield a.simple_inverse()

    def count_simple(self) -> int:
        return self._alg.count_simple()



