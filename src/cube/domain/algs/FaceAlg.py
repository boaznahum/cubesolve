from typing import TYPE_CHECKING, Self, Sequence

from cube.domain.algs.FaceAlgBase import FaceAlgBase
from cube.domain.algs.SliceAbleAlg import SliceAbleAlg
from cube.domain.exceptions import InternalSWError
from cube.domain.model import FaceName

if TYPE_CHECKING:
    from cube.domain.algs.SlicedFaceAlg import SlicedFaceAlg
    from cube.domain.algs.SimpleAlg import SimpleAlg


class FaceAlg(FaceAlgBase, SliceAbleAlg):
    """
    Face algorithm that CAN be sliced. R[1:2] returns SlicedFaceAlg.

    This class represents an unsliced face algorithm (R, L, U, D, F, B).
    When sliced via __getitem__, it returns a SlicedFaceAlg which cannot
    be sliced again (type-level enforcement).

    One instance per FaceName, created in Algs._face_by_name.

    All instances are frozen (immutable) after construction.
    """

    __slots__ = ()  # No additional slots - _face is in FaceAlgBase

    def __init__(self, face: FaceName, n: int = 1) -> None:
        super().__init__(face, n)
        self._freeze()

    @property
    def slices(self) -> None:
        """Return slice info. Always None for unsliced FaceAlg."""
        return None

    def _create_with_n(self, n: int) -> Self:
        """Create a new FaceAlg with the given n value."""
        instance: Self = object.__new__(type(self))
        object.__setattr__(instance, "_frozen", False)
        object.__setattr__(instance, "_code", self._code)
        object.__setattr__(instance, "_n", n)
        object.__setattr__(instance, "_face", self._face)
        object.__setattr__(instance, "_frozen", True)
        return instance

    def __getitem__(self, items: int | slice | Sequence[int]) -> "SlicedFaceAlg":
        """
        Slice this face algorithm, returning a SlicedFaceAlg.

        The returned SlicedFaceAlg cannot be sliced again (no __getitem__).

        Args:
            items: Slice specification (int, slice, or sequence of ints)

        Returns:
            A new SlicedFaceAlg with the slice applied
        """
        from cube.domain.algs.SlicedFaceAlg import SlicedFaceAlg

        if not items:
            # Return a SlicedFaceAlg with default slice
            return SlicedFaceAlg(self._face, self._n, slice(1, 1))

        a_slice: slice | Sequence[int]
        if isinstance(items, int):
            a_slice = slice(items, items)  # start/stop the same
        elif isinstance(items, slice):
            a_slice = items
        elif isinstance(items, Sequence):
            a_slice = sorted(items)
        else:
            raise InternalSWError(f"Unknown type for slice: {items} {type(items)}")

        return SlicedFaceAlg(self._face, self._n, a_slice)

    def same_form(self, a: "SimpleAlg") -> bool:
        """Check if another alg has the same form (both unsliced, same face)."""
        if not isinstance(a, FaceAlg):
            return False
        return self._face == a._face
