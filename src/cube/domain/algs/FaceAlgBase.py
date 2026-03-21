from abc import ABC, abstractmethod
from typing import Any, Collection, Iterable, Self, Sequence, Tuple

from cube.domain.algs._internal_utils import _format_slice_sequence, _inv, n_to_str
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

        None (unsliced)            → R (no prefix)
        slice(None, None) [:]      → [:]R (all layers)
        slice(1, 1)                → R (hidden for FaceAlg, [1:1]M for SliceAlg)
        slice(n, n)                → nR (SiGN, FaceAlg only: 2R, 3R)
        slice(start, None) [n:]    → [n:]R
        slice(None, stop)  [:n]    → [1:n]R
        slice(start, stop) [n:m]   → [n:m]R
        """
        slices = self.slices

        if slices is None:
            # Unsliced alg (plain R) — no prefix
            return s

        if isinstance(slices, slice):
            start = slices.start
            stop = slices.stop

            # [:] — all layers
            if start is None and stop is None:
                return "[:]" + s

            # Hide [1:1] for FaceAlg (R = R[1]), but show for SliceAlg (M ≠ M[1])
            if self._hide_single_slice and 1 == start and 1 == stop:
                return s

            # SiGN notation: single inner slice as nF (e.g., 2F, 3R)
            if self._hide_single_slice and start is not None and stop is not None and start == stop:
                return str(start) + s

            # [n:] — open end
            if start is not None and stop is None:
                return "[" + str(start) + ":" + "]" + s

            # [:n] — open start (display as [1:n])
            if start is None and stop is not None:
                return "[1:" + str(stop) + "]" + s

            # [n:m] — explicit range
            if start is not None and stop is not None:
                return "[" + str(start) + ":" + str(stop) + "]" + s

            raise InternalSWError(f"Unknown {start} {stop}")
        else:
            return "[" + _format_slice_sequence(slices) + "]" + s

    def atomic_str(self) -> str:
        return self._add_to_str(n_to_str(self._code, self._n))

    def normalize_slice_index(self, n_max: int, _default: Iterable[int]) -> Iterable[int]:
        """
        Normalize slice indices for cube operations.

        Converts 1-based slice specifications into 0-based cube coordinates.
        We have no way to know what is max n at definition time, so n_max
        is passed at play time (= cube.size for FaceAlg).

        Args:
            n_max: Maximum 1-based index for this cube size.
                   For FaceAlg: cube.size (1=face, 2..size-1=inner, size=opposite).
                   For SliceAlg: n_slices (inner slices only).
            _default: Default indices when self.slices is None (unsliced alg).
                      FaceAlg: [1] (just the face). SliceAlg: all slices.

        Slice resolution (1-based, before conversion to 0-based):
            slices=None (unsliced)     → _default
            slices=Sequence            → as-is (e.g., [1, 3] for discontinued)
            slices=slice(None, None)   → [1..n_max] (all layers, [:] syntax)
            slices=slice(start, None)  → [start..n_max] (open end, [n:] syntax)
            slices=slice(None, stop)   → [1..stop] (open start, [:n] syntax)
            slices=slice(start, stop)  → [start..stop] (explicit range)

        Returns:
            0-based indices: [i - 1 for each resolved index]
        """
        slices = self.slices
        res: Iterable[int]

        if slices is None:
            # Unsliced alg (plain R, plain M) — use default
            res = _default

        elif isinstance(slices, Sequence):
            # Discontinued slices (e.g., [1, 3]) — as-is
            res = slices

        elif isinstance(slices, slice):
            start = slices.start
            stop = slices.stop

            # Resolve None to boundaries: None start → 1, None stop → n_max
            _start = start if start is not None else 1
            _stop = stop if stop is not None else n_max

            assert _start >= 1, f"Slice start must be >= 1, got {_start}"
            assert _stop >= _start, f"Slice stop {_stop} < start {_start}"
            res = [*range(_start, _stop + 1)]
        else:
            res = _default

        return [i - 1 for i in res]

    def _resolve_slices(self, cube: Cube) -> Iterable[int]:
        """Resolve slice indices for this cube size.

        Index 1 = this face, 2..size-1 = inner slices, size = opposite face.
        """
        return self.normalize_slice_index(n_max=cube.size, _default=[1])

    def play(self, cube: Cube, inv: bool = False) -> None:
        """Play the face algorithm on the cube."""
        cube.rotate_face_and_slice(_inv(inv, self._n), self._face, self._resolve_slices(cube))

    def get_animation_objects(self, cube: Cube) -> Tuple[FaceName, Collection[PartSlice]]:
        """Get objects involved in this face algorithm for animation."""
        parts = cube.get_rotate_face_and_slice_involved_parts(self._face, self._resolve_slices(cube))
        return self._face, parts

    def _create_with_n(self, n: int) -> Self:
        """Create a new instance with the given n value. Subclasses must override."""
        raise NotImplementedError(
            f"{type(self).__name__} must implement _create_with_n()"
        )
