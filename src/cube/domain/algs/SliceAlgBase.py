from abc import ABC, abstractmethod
from typing import Collection, Iterable, Self, Sequence, Tuple

from cube.domain.algs._internal_utils import _inv, n_to_str
from cube.domain.algs.AnimationAbleAlg import AnimationAbleAlg
from cube.domain.exceptions import InternalSWError
from cube.domain.model.Cube import Cube, FaceName, PartSlice
from cube.domain.model.cube_slice import SliceName


class SliceAlgBase(AnimationAbleAlg, ABC):
    # Note: AnimationAbleAlg already inherits from NSimpleAlg
    """
    Base class for all slice-related algorithms (both sliced and unsliced).

    This provides common functionality for SliceAlg (sliceable) and
    SlicedSliceAlg (not sliceable).

    Slice Indexing Convention (1-based):
        Slice indices are 1-based, ranging from 1 to n_slices (where n_slices = cube_size - 2).
        This is the PUBLIC API convention used when indexing slice algorithms.

        For an NxN cube:
            - n_slices = N - 2 (number of inner slices)
            - Valid indices: 1, 2, ..., n_slices

        Example for 5x5 cube (n_slices = 3):
            E[1]  - first inner slice (closest to U face)
            E[2]  - middle slice
            E[3]  - last inner slice (closest to D face)
            E     - all slices (E[1:3] equivalent)
            E[1:] - slices 1 to n_slices
            E[:2] - slices 1 to 2

    Internal Conversion:
        normalize_slice_index() converts 1-based indices to 0-based
        for internal cube operations. See that method for details.

    All instances are frozen (immutable) after construction.
    """

    __slots__ = ("_slice_name",)

    def __init__(self, slice_name: SliceName, n: int = 1) -> None:
        super().__init__(slice_name.value.__str__(), n)
        self._slice_name = slice_name
        # Note: _freeze() is called by concrete subclasses

    @property
    def slice_name(self) -> SliceName:
        return self._slice_name

    @property
    @abstractmethod
    def slices(self) -> "slice | Sequence[int] | None":
        """Return slice info. None for unsliced SliceAlg, set for SlicedSliceAlg."""
        ...

    @property
    def _hide_single_slice(self) -> bool:
        """Don't hide [1] because M ≠ M[1] for SliceAlg."""
        return False

    def _add_to_str(self, s: str) -> str:
        """Format slice info for string representation."""
        slices = self.slices

        if slices is None:
            return s

        if isinstance(slices, slice):
            start = slices.start
            stop = slices.stop

            if not start and not stop:
                return s

            # Hide [1:1] for FaceAlg (R = R[1]), but show for SliceAlg (M ≠ M[1])
            if self._hide_single_slice and 1 == start and 1 == stop:
                return s

            if start and not stop:
                return "[" + str(start) + ":" + "]" + s

            if not start and stop:
                return "[1:" + str(stop) + "]" + s

            if start and stop:
                return "[" + str(start) + ":" + str(stop) + "]" + s

            raise InternalSWError(f"Unknown {start} {stop}")
        else:
            return "[" + ",".join(str(i) for i in slices) + "]" + s

    def atomic_str(self) -> str:
        return self._add_to_str(n_to_str(self._code, self._n))

    def normalize_slice_index(self, n_max: int, _default: Iterable[int]) -> Iterable[int]:
        """
        Normalize slice indices for cube operations.

        See class description for explanation of 1-based indexing convention.

        :param n_max: Maximum slice index for this cube size
        :param _default: Default in [1,n] space
        :return: Indices in cube coordinates [0, size-2]
        """
        slices = self.slices
        res: Iterable[int]

        if slices is None:
            res = _default

        elif isinstance(slices, Sequence):
            res = slices

        elif isinstance(slices, slice):
            start = slices.start
            stop = slices.stop

            _stop = None
            _start = None

            if not start and not stop:
                res = _default
            else:
                if start and not stop:
                    _start, _stop = (start, n_max)
                elif not start and stop:
                    _start, _stop = (1, stop)
                else:
                    _start, _stop = (start, stop)

                assert _start
                assert _stop
                res = [*range(_start, _stop + 1)]
        else:
            res = _default

        return [i - 1 for i in res]

    def play(self, cube: Cube, inv: bool = False) -> None:
        """Play the slice algorithm on the cube."""
        slices = self.normalize_slice_index(
            n_max=cube.n_slices,
            _default=range(1, cube.n_slices + 1)
        )
        cube.rotate_slice(self._slice_name, _inv(inv, self._n), slices)

    def get_animation_objects(self, cube: Cube) -> Tuple[FaceName, Collection[PartSlice]]:
        """Get objects involved in this slice algorithm for animation."""
        face_name = self.get_face_name(cube)
        start_stop: Iterable[int] = self.normalize_slice_index(
            n_max=cube.n_slices,
            _default=range(1, cube.n_slices + 1)
        )
        return face_name, cube.get_rotate_slice_involved_parts(self._slice_name, start_stop)

    def get_face_name(self, cube: Cube) -> FaceName:
        """
        Return the face that defines the positive rotation direction for this slice.

        Returns:
            M slice → L face (middle layer between L and R, rotates like L)
            E slice → D face (middle layer between U and D, rotates like D)
            S slice → F face (middle layer between F and B, rotates like F)
        """
        return cube.layout.get_slice(self._slice_name).get_face_name()

    def _create_with_n(self, n: int) -> Self:
        """Create a new instance with the given n value. Subclasses must override."""
        raise NotImplementedError(
            f"{type(self).__name__} must implement _create_with_n()"
        )
