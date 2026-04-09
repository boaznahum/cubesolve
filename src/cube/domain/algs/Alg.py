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
        """Move this algorithm to a different position on the cube.

        If this algorithm works on some pieces (e.g. edges LU, FU),
        transform gives you the same algorithm working on different
        pieces — wherever whole-cube rotation W would move them.

        Definition:  W  T(W, A)  W'  =  A

        W is a whole-cube rotation that moves positions POS1 to POS2.
        T(W, A) is the algorithm that does A's work at POS2.
        So if you apply T(W, A) alone (without W and W'), you get
        A's effect at POS2 instead of POS1.

        Example: algorithm A swaps edges {LU, FU} on the U face.
        We want an algorithm that swaps {FU, RU} instead.

        Pick W = Y', which maps L->F and F->R.
        So Y' moves {LU, FU} to {FU, RU}.
        A.transform(Y') gives us the algorithm that swaps {FU, RU}.

        U face (top-down view)::

            A acts on {LU, FU}:        A.transform(Y') acts on {FU, RU}:

                  B                          B
               +--+--+--+                +--+--+--+
               |  |  |  |                |  |  |  |
            L  +--+--+--+  R          L  +--+--+--+  R
               |* |  |  |                |  |  |* |
               +--+--+--+                +--+--+--+
               |  |* |  |                |  |* |  |
               +--+--+--+                +--+--+--+
                  F                          F

               * = edges swapped          * = edges swapped
                   (LU and FU)                (FU and RU)

        Usage::

            # F move under Y' rotation becomes R
            Algs.F.transform(Algs.Y.prime)          # -> R

            # A sexy move on R face becomes one on B face
            (R + U + R.prime + U.prime).transform(Algs.Y.prime)  # -> B U B' U'

            # For algorithms with inner slices, pass cube_size
            alg.transform(Algs.Y.prime, cube_size=5)

        Args:
            w: Whole-cube rotation (X, Y, Z or a sequence of them).
            cube_size: Only needed when the algorithm contains sliced
                slice moves (e.g. M[2:3]) and the transform flips direction.
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







