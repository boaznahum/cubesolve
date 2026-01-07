from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self, Sequence, final

from cube.domain.algs.SliceAbleAlg import SliceAbleAlg
from cube.domain.algs.SliceAlgBase import SliceAlgBase
from cube.domain.exceptions import InternalSWError
from cube.domain.model.cube_slice import SliceName

if TYPE_CHECKING:
    from cube.domain.algs.SlicedSliceAlg import SlicedSliceAlg
    from cube.domain.algs.SimpleAlg import SimpleAlg


class SliceAlg(SliceAlgBase, SliceAbleAlg, ABC):
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
    def slice_name(self) -> SliceName:
        return self._slice_name

    @final
    def play(self, cube: Cube, inv: bool = False):
        # cube.rotate_slice(self._slice_name, _inv(inv, self._n))

        # See class description for explanation
        slices = self.normalize_slice_index(n_max=cube.n_slices, _default=range(1, cube.n_slices + 1))

        cube.rotate_slice(self._slice_name, _inv(inv, self._n), slices)

    def get_animation_objects(self, cube: Cube) -> Tuple[FaceName, Collection[PartSlice]]:

    def _create_with_n(self, n: int) -> Self:
        """Create a new SliceAlg with the given n value."""
        instance: Self = object.__new__(type(self))
        object.__setattr__(instance, "_frozen", False)
        object.__setattr__(instance, "_code", self._code)
        object.__setattr__(instance, "_n", n)
        object.__setattr__(instance, "_slice_name", self._slice_name)
        object.__setattr__(instance, "_frozen", True)
        return instance

        start_stop: Iterable[int] = self.normalize_slice_index(n_max=cube.n_slices,
                                                               _default=range(1, cube.n_slices + 1))

        return face_name, cube.get_rotate_slice_involved_parts(self._slice_name, start_stop)

    def get_face_name(self, cube: Cube) -> FaceName:
        """
        Return the face that defines the positive rotation direction for this slice.

        This is the face that the slice rotates "over" - when the slice rotates,
        it moves content in the same direction as rotating I think that face clockwise
        (viewed from outside the cube looking at that face).

        In terms of the LTR coordinate system (see docs/face-coordinate-system/):
        - Clockwise rotation moves content: T→R→(-T)→(-R)→T
        - Content flows from the T (top/bottom) direction toward the R (left/right) direction

        Returns:
            M slice → L face (middle layer between L and R, rotates like L)
            E slice → D face (middle layer between U and D, rotates like D)
            S slice → F face (middle layer between F and B, rotates like F)

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

        return cube.layout.get_slice(self._slice_name).get_face_name()
        # match self._slice_name:
        #
        #     case SliceName.S:  # over F
        #         return FaceName.F
        #
        #     case SliceName.M:  # over L
        #         return FaceName.L
        #
        #     case SliceName.E:  # over D
        #         return FaceName.D
        #
        #     case _:
        #         raise RuntimeError(f"Unknown Slice {self._slice_name}")

    @abstractmethod
    def get_base_alg(self) -> SliceAbleAlg:
        """ return whole slice alg that is not yet sliced"""
        pass

    def same_form(self, a: "SimpleAlg") -> bool:
        """Check if another alg has the same form (both unsliced).

        Note: We don't need to check self._slice_name == a._slice_name here
        because each slice has its own concrete type (_M, _E, _S).
        The optimizer uses `type(prev) is type(a)` which already ensures
        we only compare algs of the same slice type.
        """
        if not isinstance(a, SliceAlg):
            return False
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
