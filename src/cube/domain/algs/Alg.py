from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, Self, final

from cube.domain.model.Cube import Cube

if TYPE_CHECKING:
    from .SeqAlg import SeqAlg, SeqSimpleAlg
    from .SimpleAlg import SimpleAlg
    from .face_permutation import FacePermutation


class Alg(ABC):
    """
    Base class for all algorithms. All Alg subclasses are frozen (immutable)
    after construction. Use factory methods like `with_n()` to create modified copies.
    """

    __slots__ = ("_frozen",)

    def __init__(self) -> None:
        object.__setattr__(self, "_frozen", False)

    def _freeze(self) -> None:
        """Mark this instance as frozen. Called at end of subclass __init__."""
        object.__setattr__(self, "_frozen", True)

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_frozen", False):
            raise AttributeError(
                f"Cannot modify frozen {type(self).__name__}.{name}. "
                f"Use factory methods like with_n() to create modified copies."
            )
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        if getattr(self, "_frozen", False):
            raise AttributeError(
                f"Cannot delete attribute from frozen {type(self).__name__}.{name}"
            )

    @abstractmethod
    def play(self, cube: Cube, inv: bool = False): ...

    def inv(self) -> "Alg":
        from .Inv import _Inv
        return _Inv(self)

    @final
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

    @abstractmethod
    def transform_by(self, p: "FacePermutation", n_slices: int | None) -> "Alg":
        """Transform this algorithm by a face permutation.

        Internal method — each subclass remaps its own face/slice/axis.
        Use transform() for the public API.

        Args:
            p: The face permutation induced by whole-cube rotation W.
            n_slices: Number of inner slices (cube_size - 2). Required only
                when SlicedSliceAlg direction is negated (indices must be mirrored).
        """
        ...

    def transform(self, w: "Alg", cube_size: int | None = None) -> "Alg":
        """Transform this algorithm by whole-cube rotation W.

        Returns T(W, self) such that W' self W ≡ T(W, self).

        Args:
            w: Whole-cube rotation sequence (only X, Y, Z moves).
            cube_size: Required when self contains sliced slice moves AND
                the transform negates direction (see transform_by).

        Example:
            >>> Algs.F.transform(Algs.Y.prime)  # → R
        """
        from .alg_transform import compute_permutation
        p = compute_permutation(w)
        n_slices = cube_size - 2 if cube_size is not None else None
        return self.transform_by(p, n_slices)

    def flatten_alg(self) -> "SeqAlg":
        from .SeqAlg import SeqAlg
        return SeqAlg(None, *self.flatten())



    def __str__(self) -> str:
        return self.atomic_str()

    def __repr__(self) -> str:
        return self.__str__()

    def __neg__(self) -> "Alg":
        return self.inv()

    def __mul__(self, n: int) -> "Alg":
        from .Mul import _Mul

        if n < 0:
            return _Mul(self.inv(), -n) # _Mul doesnt support negative need to fix
        else:
            return _Mul(self, n)

    def __add__(self, other: "Alg") -> "SeqAlg":
        from .SeqAlg import SeqAlg
        return SeqAlg(None, self, other)

    def __sub__(self, other: "Alg") -> "SeqAlg":
        return self + other.prime

    def to_printable(self) -> Self:
        return self

    def count_simple(self) -> int:
        """
        Number of simple algs
        :return:
        """
        return 1







