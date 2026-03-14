"""Middle slice algorithm — operates on the single center slice."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Self, final

from cube.domain.algs.SliceAlgBase import SliceAlgBase
from cube.domain.model.cube_slice import SliceName

if TYPE_CHECKING:
    from cube.domain.algs.SimpleAlg import SimpleAlg


@final
class MiddleSliceAlg(SliceAlgBase):
    """
    The single middle slice on a given axis (M, E, or S).

    Unlike SliceAlg (which represents ALL slices and can be indexed),
    this class represents exactly ONE slice — the geometric center.

    On odd cubes (3x3, 5x5, 7x7): the true middle slice.
    On even cubes (4x4, 6x6): not standard notation, uses floor-middle.

    str() = "M" / "E" / "S" (no prefix), parser "M" → this class.

    Index calculation (1-based):
        3x3: n_slices=1, middle=1
        5x5: n_slices=3, middle=2
        7x7: n_slices=5, middle=3
        Formula: (n_slices + 1) // 2
    """

    __slots__ = ()

    def __init__(self, slice_name: SliceName) -> None:
        super().__init__(slice_name)
        self._freeze()

    @staticmethod
    def _middle_1based(n_slices: int) -> int:
        """Return the 1-based index of the middle slice."""
        return (n_slices + 1) // 2

    @property
    def slices(self) -> None:
        """No static slice — middle is computed at play time from cube size."""
        return None

    def _add_to_str(self, s: str) -> str:
        """Display as 'M' / 'E' / 'S' (no slice prefix)."""
        return s

    def normalize_slice_index(self, n_max: int, _default: Iterable[int]) -> Iterable[int]:
        """Return only the middle slice, converted to 0-based."""
        mid = self._middle_1based(n_max)
        return [mid - 1]

    def _create_with_n(self, n: int) -> Self:
        instance: Self = object.__new__(type(self))
        object.__setattr__(instance, "_frozen", False)
        object.__setattr__(instance, "_code", self._code)
        object.__setattr__(instance, "_n", n)
        object.__setattr__(instance, "_slice_name", self._slice_name)
        object.__setattr__(instance, "_frozen", True)
        return instance

    def same_form(self, a: SimpleAlg) -> bool:
        """Only matches other MiddleSliceAlg with the same slice name."""
        if not isinstance(a, MiddleSliceAlg):
            return False
        return self._slice_name == a._slice_name

    def get_base_alg(self) -> SliceAlgBase:
        """Return the sliceable all-slices alg as the base."""
        from cube.domain.algs.Algs import Algs
        return Algs.of_slice(self._slice_name)
