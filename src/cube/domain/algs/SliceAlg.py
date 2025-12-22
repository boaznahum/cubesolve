from abc import ABC
from typing import Collection, Iterable, Tuple, final

from cube.domain.algs._internal_utils import _inv
from cube.domain.algs.AnimationAbleAlg import AnimationAbleAlg
from cube.domain.algs.SliceAbleAlg import SliceAbleAlg
from cube.domain.model.Cube import Cube, FaceName, PartSlice
from cube.domain.model.cube_slice import SliceName


class SliceAlg(SliceAbleAlg, AnimationAbleAlg, ABC):

    """
    How M, S and E are sliced:

    Assume cube size is NxN, N-2 middle slices, e.g N=5
    E == E[1:] = R[1:N-2] # all (3) middle slices

    So 1 is index of the second lice, and you can rotate up to N-2 Slices
    E[1:3] # N =5
    E[1:4] # is an error.

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

        face_name: FaceName

        name = self._slice_name
        match name:

            case SliceName.S:  # over F
                face_name = FaceName.F

            case SliceName.M:  # over L
                face_name = FaceName.L

            case SliceName.E:  # over D
                face_name = FaceName.D

            case _:
                raise RuntimeError(f"Unknown Slice {name}")

        start_stop: Iterable[int] = self.normalize_slice_index(n_max=cube.n_slices,
                                                               _default=range(1, cube.n_slices + 1))

        return face_name, cube.get_rotate_slice_involved_parts(name, start_stop)


@final
class _M(SliceAlg):

    def __init__(self) -> None:
        super().__init__(SliceName.M)



@final
class _E(SliceAlg):
    """
    Middle slice over D
    """

    def __init__(self) -> None:
        super().__init__(SliceName.E)

@final
class _S(SliceAlg):
    """
    Middle slice over F
    """

    def __init__(self) -> None:
        super().__init__(SliceName.S)
