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


        face_name = self.get_face_name()

        return face_name, cube.get_all_part_slices()

    def get_face_name(self) -> FaceName:
        """
        Return the face that defines the positive rotation axis.

        This is the face that rotates clockwise when the whole-cube rotation
        is applied (viewed from outside the cube looking at that face).

        In terms of the LTR coordinate system (see docs/face-coordinate-system/):
        - Clockwise rotation moves content: T→R→(-T)→(-R)→T
        - Content flows from the T (top/bottom) direction toward the R (left/right) direction

        Returns:
            X axis → R face (rotation around L-R axis)
            Y axis → U face (rotation around U-D axis)
            Z axis → F face (rotation around F-B axis)

        See also:
            - docs/face-coordinate-system/edge-face-coordinate-system.md
            - docs/face-coordinate-system/face-slice-rotation.md
        """
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
        return face_name


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
