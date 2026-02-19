from abc import ABC, abstractmethod
from typing import Any, Collection, Iterable, Self, Sequence, Tuple

from cube.domain.algs._internal_utils import _inv, n_to_str
from cube.domain.algs.AnimationAbleAlg import AnimationAbleAlg
from cube.domain.exceptions import InternalSWError
from cube.domain.model import Cube, FaceName, PartSlice


class FaceAlgBase(AnimationAbleAlg, ABC):
    # Note: AnimationAbleAlg already inherits from NSimpleAlg
    """
    Base class for all face-related algorithms (both sliced and unsliced).

    This provides common functionality for FaceAlg (sliceable) and
    SlicedFaceAlg (not sliceable).

    How face slicing works:
    Assume cube size is NxN, N-2 middle slices
    R == R[1]
    R[1:] == R[1:N-1] # all but last slice

    You can slice face in range [1:cube.n_slices+1] == [1:N-1]

    So in the case of 5x5:
    R[1:4] is OK.
    R[1:5] is an error.

    All instances are frozen (immutable) after construction.
    """

    __slots__ = ("_face",)

    def __init__(self, face: FaceName, n: int = 1) -> None:
        # we know it is str, still we need to cast for mypy
        super().__init__(str(face.value), n)
        self._face: FaceName = face
        # Note: _freeze() is called by concrete subclasses

    @property
    def face_name(self) -> FaceName:
        return self._face

    @property
    @abstractmethod
    def slices(self) -> "slice | Sequence[int] | None":
        """Return slice info. None for unsliced FaceAlg, set for SlicedFaceAlg."""
        ...

    @property
    def _hide_single_slice(self) -> bool:
        """Hide [1] because R = R[1] for FaceAlg."""
        return True

    def _add_to_str(self, s: str) -> str:
        """
        Format slice info for string representation.

        None -> default = R
        (None, None) -> default R
        (1, 1) -> default R (hidden for FaceAlg)
        (start, None) -> [start:]R
        (None, stop) -> [:stop] == [1:stop]
        (start, stop) -> [start:stop]
        """
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

        We have no way to know what is max n at definition time.
        :param n_max: Maximum slice index for this cube size
        :param _default: Default in [1,n] space
        :return: Indices in cube coordinates [0, size-2]

        [i] -> (i, i)  - by get_item
        None -> (None, None)

        (None, None) -> default
        (start, None) -> (start, n_max)
        (None, Stop) -> (1, stop)
        (start, stop) -> (start, stop)

        :return: [start, stop] in cube coordinates [0, size-2]
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
        """Play the face algorithm on the cube."""
        start_stop: Iterable[int] = self.normalize_slice_index(
            n_max=1 + cube.n_slices, _default=[1]
        )
        cube.rotate_face_and_slice(_inv(inv, self._n), self._face, start_stop)

    def get_animation_objects(self, cube: Cube) -> Tuple[FaceName, Collection[PartSlice]]:
        """Get objects involved in this face algorithm for animation."""
        face = self._face
        slices: Iterable[int] = self.normalize_slice_index(
            n_max=1 + cube.n_slices, _default=[1]
        )
        parts: Collection[Any] = cube.get_rotate_face_and_slice_involved_parts(face, slices)
        return face, parts

    def _create_with_n(self, n: int) -> Self:
        """Create a new instance with the given n value. Subclasses must override."""
        raise NotImplementedError(
            f"{type(self).__name__} must implement _create_with_n()"
        )
