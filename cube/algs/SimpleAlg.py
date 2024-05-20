from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Self, final, override

from cube.algs.Alg import Alg
from cube.algs.SeqAlg import SeqSimpleAlg
from cube.algs._internal_utils import n_to_str, _normalize_for_count


class SimpleAlg(Alg, ABC):

    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def simple_inverse(self) -> Self: ...


class NSimpleAlg(SimpleAlg, ABC):
    """
    A simple alg with n property,
    Follows the rule of simple rotation n == N % 4
    """

    __slots__ = ["_n", "_code"]

    # todo: most of the code in this lags should be moved into NSimpleAlg

    def __init__(self, code: str, n: int = 1) -> None:
        super().__init__()
        self._code = code
        self._n = n

    def simple_mul(self, n: int):
        c = self.clone()
        c._n *= n

        return c

    def _basic_clone(self: Self) -> Self:
        cl = NSimpleAlg.__new__(type(self))
        # noinspection PyArgumentList
        cl.__init__()  # type: ignore

        return cl

    @final
    def clone(self) -> Self:
        cl = self._basic_clone()

        cl.copy(self)

        return cl

    def copy(self, other: Self):
        self._n = other.n
        return self

    def atomic_str(self) -> str:
        return n_to_str(self._code, self._n)

    def __str__(self) -> str:
        return self.atomic_str()

    def count(self) -> int:
        return _normalize_for_count(self._n)

    @property
    def n(self):
        return self._n

    def xsimplify(self) -> "NSimpleAlg|SeqSimpleAlg":
        if self._n % 4:
            return self
        else:
            return SeqSimpleAlg(None)

    def flatten(self) -> Iterator["SimpleAlg"]:
        if self._n % 4:
            yield self
        # otherwise, it is empty

    @override
    def simple_inverse(self)-> Self:
        """
        Inverse but return simple alg
        Used by: class:`_Inv`
        :return:
        """
        s = self.clone()
        s._n *= -1
        return s

    # ---------------------------------
    # type of simple: face, axis, slice

    def same_form(self, a: "SimpleAlg") -> bool:
        return True

    def __imul__(self, other: int):
        """
        For simple algorithm inv and mul
        :param other:
        :return:
        """
        self._n *= other
        return self

    @property
    def code(self):
        return self._code
