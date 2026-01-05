from typing import Collection, Self, Tuple

from cube.domain.algs.AnimationAbleAlg import AnimationAbleAlg
from cube.domain.algs.FaceAlg import FaceAlg
from cube.domain.algs.SeqAlg import SeqSimpleAlg
from cube.domain.algs.SimpleAlg import NSimpleAlg, SimpleAlg
from cube.domain.model.Cube import Cube, FaceName, PartSlice


class DoubleLayerAlg(AnimationAbleAlg):
    """
    A double layer of given FaceAlg,
    For example, Rw is a double layer of R
    In case of S > 3, it all layers, but the last
    Rw == R[1: size-1]

    All instances are frozen (immutable) after construction.
    """

    __slots__ = ("_of_face_alg",)

    def __init__(self, of_face_alg: FaceAlg, n: int = 1) -> None:
        super().__init__(of_face_alg._code + "w", n)
        self._of_face_alg: FaceAlg = of_face_alg
        self._freeze()

    def _create_with_n(self, n: int) -> Self:
        """Create a new DoubleLayerAlg with the given n value."""
        instance: Self = object.__new__(type(self))
        object.__setattr__(instance, "_frozen", False)
        object.__setattr__(instance, "_code", self._code)
        object.__setattr__(instance, "_n", n)
        object.__setattr__(instance, "_of_face_alg", self._of_face_alg)
        object.__setattr__(instance, "_frozen", True)
        return instance

    def get_animation_objects(self, cube: Cube) -> Tuple[FaceName, Collection[PartSlice]]:
        return self.compose_base_alg(cube).get_animation_objects(cube)

    def play(self, cube: Cube, inv: bool = False) -> None:
        self.compose_base_alg(cube).play(cube, inv)

    def compose_base_alg(self, cube: Cube) -> FaceAlg:
        fa: FaceAlg = self._of_face_alg
        cube_size = cube.size

        if self._n != fa._n:
            fa = fa.with_n(self._n)

        # size-1: 3x3 -> R[1:2], 4x4 [1:3]
        return fa[1: cube_size - 1]

    def xsimplify(self) -> "NSimpleAlg|SeqSimpleAlg":
        """
        TODO: simplify Rw == R[1: size-1]
        :return:
        """
        return super().simplify()

    def same_form(self, a: "SimpleAlg") -> bool:
        if not isinstance(a, DoubleLayerAlg):
            return False

        return self._of_face_alg._face == a._of_face_alg._face
