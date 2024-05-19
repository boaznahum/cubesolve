from typing import TYPE_CHECKING, Iterator

import cube.algs.AnnoationAlg
from .Alg import Alg
from cube.model import Cube


if TYPE_CHECKING:
    from .SimpleAlg import SimpleAlg, NSimpleAlg
    from .SeqAlg import SeqSimpleAlg


class _Inv(Alg):

    from .SimpleAlg import NSimpleAlg
    from .SeqAlg import SeqAlg

    __slots__ = "_alg"

    def __init__(self, _a: Alg) -> None:
        super().__init__()
        self._alg = _a

    def __str__(self) -> str:
        return self._alg.atomic_str() + "'"

    def play(self, cube: Cube, inv: bool = False):
        self._alg.play(cube, not inv)

    def inv(self) -> Alg:
        return self._alg

    def atomic_str(self) -> str:
        return self._alg.atomic_str() + "'"

    def count(self) -> int:
        return self._alg.count()

    def simplify(self) -> "SimpleAlg|SeqSimpleAlg":

        """
        Must returns SimpleAlg if _alg is SimpleAlg
        :return:
        """

        if isinstance(self._alg, _Inv):
            # X'' = X
            return self._alg._alg.simplify()

        a = self._alg.simplify()  # can't be _Mul, nor Inv

        if isinstance(a, _Inv.NSimpleAlg):
            s = a.clone()
            s *= -1  # inv - that is my function
            return s.simplify()
        elif isinstance(a, cube.algs.AnnoationAlg.AnnotationAlg):
            return a
        elif isinstance(a, _Inv.SeqAlg):

            algs = [a.inv() for a in reversed(a.algs)]
            return _Inv.SeqAlg(None, *algs).simplify()
        else:
            raise TypeError("Unknown type:", type(self))

    def flatten(self) -> Iterator["SimpleAlg"]:

        """
        Must returns SimpleAlg if _alg is SimpleAlg
        :return:
        """

        a = self.simplify()  # can't be _Mul, nor Inv

        return a.flatten()
