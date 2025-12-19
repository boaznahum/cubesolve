from abc import ABC
from typing import final, Iterable, Tuple, Collection, Any

from cube.domain.algs.AnimationAbleAlg import AnimationAbleAlg
from cube.domain.algs.SliceAbleAlg import SliceAbleAlg
from cube.domain.algs._internal_utils import _inv
from cube.domain.model import FaceName, Cube, PartSlice


class FaceAlg(SliceAbleAlg, AnimationAbleAlg, ABC):

    """
    How face is sliced:
    Assume cube size is NxN, N-2 middle slices
    R == R[1]
    R[1:] == R[1:N-1] # all but last slice

    You can slice face in range [1:cube.n_slices+1] == [1:N-1]

    So in the case of 5x5:
    R[1:4] is OK.
    R[1:5] is an error.

    """

    def __init__(self, face: FaceName, n: int = 1) -> None:
        # we know it is str, still we need to cast for mypy
        super().__init__(str(face.value), n)
        self._face: FaceName = face

    @final
    def play(self, cube: Cube, inv: bool = False):
        start_stop: Iterable[int] = self.normalize_slice_index(n_max=1 + cube.n_slices, _default=[1])
        cube.rotate_face_and_slice(_inv(inv, self._n), self._face, start_stop)

    def get_animation_objects(self, cube) -> Tuple[FaceName, Collection[PartSlice]]:
        face = self._face

        slices: Iterable[int] = self.normalize_slice_index(n_max=1 + cube.n_slices, _default=[1])

        parts: Collection[Any] = cube.get_rotate_face_and_slice_involved_parts(face, slices)

        return face, parts


@final
class _U(FaceAlg):

    def __init__(self) -> None:
        super().__init__(FaceName.U)


@final
class _D(FaceAlg):

    def __init__(self) -> None:
        super().__init__(FaceName.D)


@final
class _F(FaceAlg):

    def __init__(self) -> None:
        super().__init__(FaceName.F)


@final
class _B(FaceAlg):

    def __init__(self) -> None:
        super().__init__(FaceName.B)


@final
class _R(FaceAlg):

    def __init__(self) -> None:
        super().__init__(FaceName.R)


@final
class _L(FaceAlg):

    def __init__(self) -> None:
        super().__init__(FaceName.L)
