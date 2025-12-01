from abc import ABC, abstractmethod
from collections.abc import Iterator, MutableSequence, Sequence
from typing import TYPE_CHECKING, final, Self

from cube.domain.model.Cube import Cube

if TYPE_CHECKING:
    from .Inv import _Inv
    from .Mul import _Mul
    from .SeqAlg import SeqSimpleAlg, SeqAlg
    from .SimpleAlg import SimpleAlg


class Alg(ABC):

    @abstractmethod
    def play(self, cube: Cube, inv: bool = False): ...

    def inv(self) -> "Alg":
        from .Inv import _Inv
        return _Inv(self)

    @property
    def prime(self) -> "Alg":
        return self.inv()

    @property
    def p(self) -> "Alg":
        return self.inv()

    @abstractmethod
    def count(self) -> int:
        """
            return number of 90 moves, nn = n % 4, nn:1 -> 1 nn:2 -> 2 nn:3 -> 1
        """
        pass

    @abstractmethod
    def atomic_str(self) -> str:
        pass

    @final
    def simplify(self) -> "SeqSimpleAlg":

        from . import optimizer

        return optimizer.simplify(self)

    @abstractmethod
    def flatten(self) -> Iterator["SimpleAlg"]:
        pass

    def flatten_alg(self) -> "SeqAlg":
        from .SeqAlg import SeqAlg
        return SeqAlg(None, *self.flatten())



    def __str__(self) -> str:
        return self.atomic_str()

    def __repr__(self) -> str:
        return self.__str__()

    def __neg__(self):
        return self.inv()

    def __mul__(self, n: int):
        from .Mul import _Mul
        return _Mul(self, n)

    def __add__(self, other: "Alg"):
        from .SeqAlg import SeqAlg
        return SeqAlg(None, self, other)

    def __sub__(self, other: "Alg"):
        return self + other.prime

    def to_printable(self) -> Self:
        return self

    def count_simple(self) -> int:
        """
        Number of simple algs
        :return:
        """
        return 1







