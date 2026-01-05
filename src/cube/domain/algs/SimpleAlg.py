from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Self, final
from typing_extensions import override

from cube.domain.algs._internal_utils import _normalize_for_count, n_to_str
from cube.domain.algs.Alg import Alg
from cube.domain.algs.SeqAlg import SeqSimpleAlg


class SimpleAlg(Alg, ABC):

    __slots__ = ()  # No additional slots

    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def simple_inverse(self) -> Self: ...


class NSimpleAlg(SimpleAlg, ABC):
    """
    A simple alg with n property,
    Follows the rule of simple rotation n == N % 4

    All instances are frozen (immutable) after construction.
    Use with_n() to create modified copies.
    """

    __slots__ = ("_n", "_code")

    def __init__(self, code: str, n: int = 1) -> None:
        super().__init__()
        self._code = code
        self._n = n
        # Note: _freeze() is called by concrete subclasses, not here,
        # to allow intermediate classes to set additional attributes

    def with_n(self, n: int) -> Self:
        """Create a new instance with the given n value. Subclasses should override."""
        if n == self._n:
            return self
        return self._create_with_n(n)

    def _create_with_n(self, n: int) -> Self:
        """
        Create a new instance with the given n value.
        Subclasses must override to pass their specific constructor args.
        """
        # Default implementation - works for simple subclasses
        # that only need code and n
        instance = object.__new__(type(self))
        object.__setattr__(instance, "_frozen", False)
        object.__setattr__(instance, "_code", self._code)
        object.__setattr__(instance, "_n", n)
        object.__setattr__(instance, "_frozen", True)
        return instance

    def simple_mul(self, n: int) -> Self:
        """Return a new instance with n multiplied."""
        return self.with_n(self._n * n)

    def atomic_str(self) -> str:
        return n_to_str(self._code, self._n)

    def __str__(self) -> str:
        return self.atomic_str()

    def count(self) -> int:
        return _normalize_for_count(self._n)

    @property
    def n(self) -> int:
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
    def simple_inverse(self) -> Self:
        """
        Inverse but return simple alg
        Used by: class:`_Inv`
        :return:
        """
        return self.with_n(-self._n)

    # ---------------------------------
    # type of simple: face, axis, slice

    def same_form(self, a: "SimpleAlg") -> bool:
        return True

    @property
    def code(self) -> str:
        return self._code
