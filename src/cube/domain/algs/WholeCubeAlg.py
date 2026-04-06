from abc import ABC
from typing import TYPE_CHECKING, Collection, Self, Tuple, final

from cube.domain.algs._internal_utils import _inv
from cube.domain.algs.AnimationAbleAlg import AnimationAbleAlg
from cube.domain.algs.SimpleAlg import NSimpleAlg
from cube.domain.model import AxisName, Cube, FaceName, PartSlice

if TYPE_CHECKING:
    from cube.domain.algs.Alg import Alg
    from cube.domain.algs.face_permutation import FacePermutation


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
        face_name = cube.layout.get_axis_face(self._axis_name)
        return face_name, cube.get_all_part_slices()

    @property
    def axis_name(self) -> AxisName:
        return self._axis_name

    def transform_by(self, p: "FacePermutation", n_slices: int | None) -> "Alg":
        from cube.domain.algs.Algs import Algs
        from cube.domain.algs.face_permutation import transform_axis
        new_axis, new_n = transform_axis(p, self._axis_name, self._n)
        if new_axis == AxisName.X:
            return Algs.X.with_n(new_n)
        elif new_axis == AxisName.Y:
            return Algs.Y.with_n(new_n)
        else:
            return Algs.Z.with_n(new_n)


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
