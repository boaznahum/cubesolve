from typing import TYPE_CHECKING, Self, Sequence, final

from cube.domain.algs.SliceAlgBase import SliceAlgBase
from cube.domain.model.cube_slice import SliceName

if TYPE_CHECKING:
    from cube.domain.algs.SimpleAlg import SimpleAlg


@final
class SlicedSliceAlg(SliceAlgBase):
    """
    A slice algorithm that has been sliced (e.g., M[1:2]).

    This class CANNOT be sliced again - there is no __getitem__ method.
    This provides compile-time enforcement that slicing can only happen once.

    All instances are frozen (immutable) after construction.
    """

    __slots__ = ("_slices",)

    def __init__(
        self,
        slice_name: SliceName,
        n: int,
        slices: "slice | Sequence[int]",
    ) -> None:
        """
        Create a sliced slice algorithm.

        Args:
            slice_name: The slice name (M, E, S)
            n: The rotation count (1, -1, 2, etc.)
            slices: The slice specification (always set, never None)
        """
        super().__init__(slice_name, n)
        self._slices: slice | Sequence[int] = slices
        self._freeze()

    @property
    def slices(self) -> "slice | Sequence[int]":
        """Return slice info. Always set for SlicedSliceAlg."""
        return self._slices

    def _create_with_n(self, n: int) -> Self:
        """Create a new SlicedSliceAlg with the given n value."""
        instance: Self = object.__new__(type(self))
        object.__setattr__(instance, "_frozen", False)
        object.__setattr__(instance, "_code", self._code)
        object.__setattr__(instance, "_n", n)
        object.__setattr__(instance, "_slice_name", self._slice_name)
        object.__setattr__(instance, "_slices", self._slices)
        object.__setattr__(instance, "_frozen", True)
        return instance

    def same_form(self, a: "SimpleAlg") -> bool:
        """Check if another alg has the same form (same slices)."""
        if not isinstance(a, SlicedSliceAlg):
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

    def get_base_alg(self) -> "SliceAlgBase":
        """Return the base unsliced alg. For sliced algs, we construct it."""
        from cube.domain.algs.Algs import Algs
        match self._slice_name:
            case SliceName.M:
                return Algs.M
            case SliceName.E:
                return Algs.E
            case SliceName.S:
                return Algs.S

    # NOTE: No __getitem__ method - this class cannot be sliced again!
    # This is intentional type-level enforcement.
