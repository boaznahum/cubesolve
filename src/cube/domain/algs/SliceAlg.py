from abc import ABC, abstractmethod
from typing import Collection, Iterable, Tuple, final

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

    See Also:
        - SliceAbleAlg: Parent class with slicing/indexing logic
        - Face2FaceTranslator: Uses 1-based indices when computing slice algorithms
    """

    def __init__(self, slice_name: SliceName, n: int = 1) -> None:
        # we know it is str, still we need to cast for mypy
        super().__init__(slice_name.value.__str__(), n)
        self._slice_name = slice_name

    @property
    def slice_name(self) -> SliceName | None:
        return self._slice_name

    @final
    def play(self, cube: Cube, inv: bool = False):
        # cube.rotate_slice(self._slice_name, _inv(inv, self._n))

        # See class description for explanation
        slices = self.normalize_slice_index(n_max=cube.n_slices, _default=range(1, cube.n_slices + 1))

        cube.rotate_slice(self._slice_name, _inv(inv, self._n), slices)

    def get_animation_objects(self, cube: Cube) -> Tuple[FaceName, Collection[PartSlice]]:

        face_name = self.get_face_name()

        start_stop: Iterable[int] = self.normalize_slice_index(n_max=cube.n_slices,
                                                               _default=range(1, cube.n_slices + 1))

        return face_name, cube.get_rotate_slice_involved_parts(self._slice_name, start_stop)

    def get_face_name(self) -> FaceName:
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
        match self._slice_name:

            case SliceName.S:  # over F
                return FaceName.F

            case SliceName.M:  # over L
                return FaceName.L

            case SliceName.E:  # over D
                return FaceName.D

            case _:
                raise RuntimeError(f"Unknown Slice {self._slice_name}")

    @abstractmethod
    def get_base_alg(self) -> SliceAbleAlg:
        """ return whole slice alg that is not yet sliced"""
        pass


@final
class _M(SliceAlg):

    def __init__(self) -> None:
        super().__init__(SliceName.M)

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

    def get_base_alg(self) -> SliceAbleAlg:
        from cube.domain.algs.Algs import Algs
        return Algs.E
