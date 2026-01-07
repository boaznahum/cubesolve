from typing import TYPE_CHECKING, Self, Sequence, final

from cube.domain.algs.FaceAlgBase import FaceAlgBase
from cube.domain.model import FaceName

if TYPE_CHECKING:
    from cube.domain.algs.SimpleAlg import SimpleAlg


@final
class SlicedFaceAlg(FaceAlgBase):
    """
    A face algorithm that has been sliced (e.g., R[1:2]).

    This class CANNOT be sliced again - there is no __getitem__ method.
    This provides compile-time enforcement that slicing can only happen once.

    All instances are frozen (immutable) after construction.
    """

    __slots__ = ("_slices",)

    def __init__(
        self,
        face: FaceName,
        n: int,
        slices: "slice | Sequence[int]",
    ) -> None:
        """
        Create a sliced face algorithm.

        Args:
            face: The face name (R, L, U, D, F, B)
            n: The rotation count (1, -1, 2, etc.)
            slices: The slice specification (always set, never None)
        """
        super().__init__(face, n)
        self._slices: slice | Sequence[int] = slices
        self._freeze()

    @property
    def slices(self) -> "slice | Sequence[int]":
        """Return slice info. Always set for SlicedFaceAlg."""
        return self._slices

    def _create_with_n(self, n: int) -> Self:
        """Create a new SlicedFaceAlg with the given n value."""
        instance: Self = object.__new__(type(self))
        object.__setattr__(instance, "_frozen", False)
        object.__setattr__(instance, "_code", self._code)
        object.__setattr__(instance, "_n", n)
        object.__setattr__(instance, "_face", self._face)
        object.__setattr__(instance, "_slices", self._slices)
        object.__setattr__(instance, "_frozen", True)
        return instance

    def same_form(self, a: "SimpleAlg") -> bool:
        """Check if another alg has the same form (same face and slices).

        IMPORTANT: Unlike FaceAlg (which has concrete types _R, _L, etc.),
        SlicedFaceAlg is a single concrete type for ALL sliced face algs.
        Therefore, we MUST check self._face == a._face here because the
        optimizer's `type(prev) is type(a)` check will be True for any
        two SlicedFaceAlg instances (e.g., R[1:2] and L[1:2]).
        """
        if not isinstance(a, SlicedFaceAlg):
            return False

        # Must be same face - critical check since all sliced face algs share one type
        if self._face != a._face:
            return False

        my = self._slices
        other = a._slices

        if isinstance(my, slice) and isinstance(other, slice):
            s1, t1 = my.start, my.stop
            s2, t2 = other.start, other.stop
            return (
                (s1 is None and s2 is None or s1 == s2) and
                (t1 is None and t2 is None or t1 == t2)
            )
        elif isinstance(my, Sequence) and isinstance(other, Sequence):
            # they are sorted
            return list(my) == list(other)
        else:
            return False

    # NOTE: No __getitem__ method - this class cannot be sliced again!
    # This is intentional type-level enforcement.
