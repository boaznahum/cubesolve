from abc import ABC
from typing import ClassVar, Collection, Self, Tuple, final

from cube.domain.algs._internal_utils import _inv
from cube.domain.algs.AnimationAbleAlg import AnimationAbleAlg
from cube.domain.algs.SimpleAlg import NSimpleAlg
from cube.domain.exceptions import InternalSWError
from cube.domain.model import AxisName, Cube, FaceName, PartSlice


class WholeCubeAlg(AnimationAbleAlg, NSimpleAlg, ABC):
    """
    Whole cube rotation algorithms (X, Y, Z).
    All instances are frozen (immutable) after construction.

    When ALG_CACHE_ENABLED is True, only 4 instances exist per axis (n=0,1,2,3).
    The with_n() method returns cached instances instead of creating new ones.
    """

    __slots__ = ("_axis_name",)

    # Cache: (concrete_class, n % 4) -> instance
    # Shared across all WholeCubeAlg subclasses
    _instance_cache: ClassVar[dict[tuple[type, int], "WholeCubeAlg"]] = {}

    def __init__(self, axis_name: AxisName, n: int = 1) -> None:
        # cast to satisfy numpy
        super().__init__(str(axis_name.value), n)
        self._axis_name = axis_name
        # Note: _freeze() is called by concrete subclasses

    def _register_in_cache(self) -> None:
        """Register this instance in the cache. Called after _freeze()."""
        from cube.application import _config as config
        if config.ALG_CACHE_ENABLED:
            key = (type(self), self._n % 4)
            if key not in self._instance_cache:
                self._instance_cache[key] = self

    def with_n(self, n: int) -> Self:
        """
        Return instance with given n value.

        When ALG_CACHE_ENABLED: Returns cached instance (only 4 per axis).
        When disabled: Creates new instance each time.
        """
        from cube.application import _config as config

        n_norm = n % 4

        if config.ALG_CACHE_ENABLED:
            key = (type(self), n_norm)
            cached = self._instance_cache.get(key)
            if cached is not None:
                return cached  # type: ignore[return-value]
            # Create, cache, and return
            instance = self._create_with_n(n_norm)
            self._instance_cache[key] = instance
            return instance
        else:
            # Original behavior
            if n == self._n:
                return self
            return self._create_with_n(n)

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

    def __init__(self, n: int = 1) -> None:
        super().__init__(AxisName.X, n)
        self._freeze()
        self._register_in_cache()


@final
class _Y(WholeCubeAlg):

    def __init__(self, n: int = 1) -> None:
        super().__init__(AxisName.Y, n)
        self._freeze()
        self._register_in_cache()


@final
class _Z(WholeCubeAlg):

    def __init__(self, n: int = 1) -> None:
        super().__init__(AxisName.Z, n)
        self._freeze()
        self._register_in_cache()
