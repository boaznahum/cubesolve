from abc import ABC
from typing import Collection, Tuple, final

from cube.domain.algs._internal_utils import _inv
from cube.domain.algs.AnimationAbleAlg import AnimationAbleAlg
from cube.domain.algs.SimpleAlg import NSimpleAlg
from cube.domain.exceptions import InternalSWError
from cube.domain.model import AxisName, Cube, FaceName, PartSlice


class WholeCubeAlg(AnimationAbleAlg, NSimpleAlg, ABC):

    def __init__(self, axis_name: AxisName, n: int = 1) -> None:
        # cast to satisfy numpy
        super().__init__(str(axis_name.value), n)
        self._axis_name = axis_name

    def count(self) -> int:
        return 0

    @final
    def play(self, cube: Cube, inv: bool = False):
        cube.rotate_whole(self._axis_name, _inv(inv, self._n))

    def get_animation_objects(self, cube: Cube) -> Tuple[FaceName, Collection[PartSlice]]:

        face_name: FaceName
        match self._axis_name:

            case AxisName.X:
                face_name = FaceName.R

            case AxisName.Y:
                face_name = FaceName.U

            case AxisName.Z:
                face_name = FaceName.F

            case _:
                raise InternalSWError(f"Unknown Axis {self._axis_name}")

        return face_name, cube.get_all_parts()


@final
class _X(WholeCubeAlg):

    def __init__(self) -> None:
        super().__init__(AxisName.X)


@final
class _Y(WholeCubeAlg):

    def __init__(self) -> None:
        super().__init__(AxisName.Y)


@final
class _Z(WholeCubeAlg):

    def __init__(self) -> None:
        super().__init__(AxisName.Z)
