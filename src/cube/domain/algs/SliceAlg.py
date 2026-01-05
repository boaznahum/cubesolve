from abc import ABC, abstractmethod
from typing import Collection, Iterable, Self, Sequence, Tuple, final

from cube.domain.algs._internal_utils import _inv
from cube.domain.algs.AnimationAbleAlg import AnimationAbleAlg
from cube.domain.algs.SliceAbleAlg import SliceAbleAlg
from cube.domain.model.Cube import Cube, FaceName, PartSlice
from cube.domain.model.cube_slice import SliceName


class SliceAlg(SliceAbleAlg, AnimationAbleAlg, ABC):
    """
    Base class for slice algorithms (M, E, S).

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
        SliceAbleAlg.normalize_slice_index() converts 1-based indices to 0-based
        for internal cube operations. See that method for details.

    Why 1-based?
        - Matches standard cube notation (E[1] is the first middle slice)
        - Outer layers (0 and N-1) are face rotations, not slice moves
        - Inner slices start at layer 1 from the reference face

    All instances are frozen (immutable) after construction.

    See Also:
        - SliceAbleAlg: Parent class with slicing/indexing logic
        - Face2FaceTranslator: Uses 1-based indices when computing slice algorithms
    """

    __slots__ = ("_slice_name",)

    def __init__(self, slice_name: SliceName, n: int = 1) -> None:
        # we know it is str, still we need to cast for mypy
        super().__init__(slice_name.value.__str__(), n)
        self._slice_name = slice_name
        # Note: _freeze() is called by concrete subclasses

    def _create_with_n(self, n: int) -> Self:
        """Create a new SliceAlg with the given n value."""
        instance: Self = object.__new__(type(self))
        object.__setattr__(instance, "_frozen", False)
        object.__setattr__(instance, "_code", self._code)
        object.__setattr__(instance, "_n", n)
        object.__setattr__(instance, "_slices", self._slices)
        object.__setattr__(instance, "_slice_name", self._slice_name)
        object.__setattr__(instance, "_frozen", True)
        return instance

    def _create_with_slices(self, slices: "slice | Sequence[int] | None") -> Self:
        """Create a new SliceAlg with the given slices."""
        instance: Self = object.__new__(type(self))
        object.__setattr__(instance, "_frozen", False)
        object.__setattr__(instance, "_code", self._code)
        object.__setattr__(instance, "_n", self._n)
        object.__setattr__(instance, "_slices", slices)
        object.__setattr__(instance, "_slice_name", self._slice_name)
        object.__setattr__(instance, "_frozen", True)
        return instance

    @property
    def slice_name(self) -> SliceName:
        return self._slice_name

    @final
    def play(self, cube: Cube, inv: bool = False) -> None:
        # cube.rotate_slice(self._slice_name, _inv(inv, self._n))

        # See class description for explanation
        slices = self.normalize_slice_index(n_max=cube.n_slices, _default=range(1, cube.n_slices + 1))

        cube.rotate_slice(self._slice_name, _inv(inv, self._n), slices)

    def get_animation_objects(self, cube: Cube) -> Tuple[FaceName, Collection[PartSlice]]:

        face_name = self.get_face_name(cube)

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

        See also:
            - WholeCubeAlg.get_face_name() for whole-cube rotation equivalent
            - docs/face-coordinate-system/face-slice-rotation.md
        """

        return cube.layout.get_slice(self._slice_name).get_face_name()

    @abstractmethod
    def get_base_alg(self) -> SliceAbleAlg:
        """ return whole slice alg that is not yet sliced"""
        pass


@final
class _M(SliceAlg):

    def __init__(self) -> None:
        super().__init__(SliceName.M)
        self._freeze()

    def get_base_alg(self) -> SliceAbleAlg:
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

    def get_base_alg(self) -> SliceAbleAlg:
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

    def get_base_alg(self) -> SliceAbleAlg:
        from cube.domain.algs.Algs import Algs
        return Algs.S
