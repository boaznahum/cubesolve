from abc import ABC
from typing import Collection, Self, Tuple, final

from cube.domain.algs._internal_utils import _inv
from cube.domain.algs.AnimationAbleAlg import AnimationAbleAlg
from cube.domain.algs.SimpleAlg import NSimpleAlg
from cube.domain.geometric.cube_layout import get_axis_face
from cube.domain.model import AxisName, Cube, FaceName, PartSlice


class WholeCubeAlg(AnimationAbleAlg, NSimpleAlg, ABC):
    """
    Whole cube rotation algorithms (X, Y, Z).
    All instances are frozen (immutable) after construction.
    """

    __slots__ = ("_axis_name",)

    def __init__(self, axis_name: AxisName, n: int = 1) -> None:
        # cast to satisfy numpy
        super().__init__(str(axis_name.value), n)
        self._axis_name = axis_name
        # Note: _freeze() is called by concrete subclasses

    def _create_with_n(self, n: int) -> Self:
        """Create a new WholeCubeAlg with the given n value."""
        instance: Self = object.__new__(type(self))
        object.__setattr__(instance, "_frozen", False)
        object.__setattr__(instance, "_code", self._code)
        object.__setattr__(instance, "_n", n)
        object.__setattr__(instance, "_axis_name", self._axis_name)
        object.__setattr__(instance, "_frozen", True)
        return instance

    def count(self) -> int:
        return 0

    @final
    def play(self, cube: Cube, inv: bool = False) -> None:
        cube.rotate_whole(self._axis_name, _inv(inv, self._n))

    def get_animation_objects(self, cube: Cube) -> Tuple[FaceName, Collection[PartSlice]]:
        face_name = self.get_face_name()
        return face_name, cube.get_all_part_slices()

    @property
    def axis_name(self) -> AxisName:
        return self._axis_name

    def get_face_name(self) -> FaceName:
        """
        Return the face that defines the positive rotation axis.

        Delegates to cube_layout.get_axis_face() which is the canonical source
        for axis-to-face mapping. See that function for detailed documentation.

        Returns:
            X axis → R face (rotation around L-R axis)
            Y axis → U face (rotation around U-D axis)
            Z axis → F face (rotation around F-B axis)
        """
        return get_axis_face(self._axis_name)


@final
class _X(WholeCubeAlg):

    def __init__(self) -> None:
        super().__init__(AxisName.X)
        self._freeze()


@final
class _Y(WholeCubeAlg):

    def __init__(self) -> None:
        super().__init__(AxisName.Y)
        self._freeze()


@final
class _Z(WholeCubeAlg):

    def __init__(self) -> None:
        super().__init__(AxisName.Z)
        self._freeze()
