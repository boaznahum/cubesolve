from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self, Sequence, final

from cube.domain.algs.SliceAlgBase import SliceAlgBase
from cube.domain.exceptions import InternalSWError
from cube.domain.model.cube_slice import SliceName

if TYPE_CHECKING:
    from cube.domain.algs.SlicedSliceAlg import SlicedSliceAlg
    from cube.domain.algs.SimpleAlg import SimpleAlg


class SliceAlg(SliceAlgBase, ABC):
    """
    Slice algorithm that CAN be sliced. M[1:2] returns SlicedSliceAlg.

    This class represents an unsliced slice algorithm (M, E, S).
    When sliced via __getitem__, it returns a SlicedSliceAlg which cannot
    be sliced again (type-level enforcement).

    All instances are frozen (immutable) after construction.

    See SliceAlgBase for documentation on slice indexing conventions.
    """

    __slots__ = ()  # No additional slots - _slice_name is in SliceAlgBase

    def __init__(self, slice_name: SliceName, n: int = 1) -> None:
        super().__init__(slice_name, n)
        # Note: _freeze() is called by concrete subclasses

    @property
    def slices(self) -> None:
        """Return slice info. Always None for unsliced SliceAlg."""
        return None

    def _create_with_n(self, n: int) -> Self:
        """Create a new SliceAlg with the given n value."""
        instance: Self = object.__new__(type(self))
        object.__setattr__(instance, "_frozen", False)
        object.__setattr__(instance, "_code", self._code)
        object.__setattr__(instance, "_n", n)
        object.__setattr__(instance, "_slice_name", self._slice_name)
        object.__setattr__(instance, "_frozen", True)
        return instance

    def __getitem__(self, items: int | slice | Sequence[int]) -> "SlicedSliceAlg":
        """
        Slice this slice algorithm, returning a SlicedSliceAlg.

        The returned SlicedSliceAlg cannot be sliced again (no __getitem__).

        Args:
            items: Slice specification (int, slice, or sequence of ints)

        Returns:
            A new SlicedSliceAlg with the slice applied
        """
        from cube.domain.algs.SlicedSliceAlg import SlicedSliceAlg

        if not items:
            # Return self unchanged for empty slice? Or default?
            # Original behavior returned self, but we need to return SlicedSliceAlg
            # For empty items, return with default all slices
            return SlicedSliceAlg(self._slice_name, self._n, slice(None, None))

        a_slice: slice | Sequence[int]
        if isinstance(items, int):
            a_slice = slice(items, items)  # start/stop the same
        elif isinstance(items, slice):
            a_slice = items
        elif isinstance(items, Sequence):
            a_slice = sorted(items)
        else:
            raise InternalSWError(f"Unknown type for slice: {items} {type(items)}")

        return SlicedSliceAlg(self._slice_name, self._n, a_slice)

    @abstractmethod
    def get_base_alg(self) -> "SliceAlgBase":
        """Return whole slice alg that is not yet sliced."""
        pass

    def same_form(self, a: "SimpleAlg") -> bool:
        """Check if another alg has the same form (both unsliced)."""
        if not isinstance(a, SliceAlg):
            return False
        # Both are unsliced SliceAlg - same form
        return True


@final
class _M(SliceAlg):

    def __init__(self) -> None:
        super().__init__(SliceName.M)
        self._freeze()

    def get_base_alg(self) -> SliceAlgBase:
        from cube.domain.algs.Algs import Algs
        return Algs.M


@final
class _E(SliceAlg):
    """
    Middle slice over D
    """

    def __init__(self) -> None:
        super().__init__(SliceName.E)
        self._freeze()

    def get_base_alg(self) -> SliceAlgBase:
        from cube.domain.algs.Algs import Algs
        return Algs.E


@final
class _S(SliceAlg):
    """
    Middle slice over F
    """

    def __init__(self) -> None:
        super().__init__(SliceName.S)
        self._freeze()

    def get_base_alg(self) -> SliceAlgBase:
        from cube.domain.algs.Algs import Algs
        return Algs.S
