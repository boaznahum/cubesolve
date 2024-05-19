from typing import Tuple, Collection, Self

from cube.algs.AnimationAbleAlg import AnimationAbleAlg
from cube.algs.FaceAlg import FaceAlg
from cube.algs.SeqAlg import SeqSimpleAlg
from cube.algs.SimpleAlg import NSimpleAlg, SimpleAlg
from cube.model import Cube, FaceName, PartSlice


class DoubleLayerAlg(AnimationAbleAlg):
    """
    A double layer of given FaceAlg,
    For example, Rw is a double layer of R
    In case of S > 3, it all layers, but the last
    Rw == R[1: size-1]
    """

    def __init__(self, of_face_alg: FaceAlg, n: int = 1) -> None:
        super().__init__(of_face_alg._code + "w", n)
        self._of_face_alg: FaceAlg = of_face_alg

    def get_animation_objects(self, cube: Cube) -> Tuple[FaceName, Collection[PartSlice]]:
        return self.compose_base_alg(cube).get_animation_objects(cube)

    def play(self, cube: Cube, inv: bool = False):
        self.compose_base_alg(cube).play(cube, inv)

    def compose_base_alg(self, cube: Cube) -> FaceAlg:
        fa: FaceAlg = self._of_face_alg
        cube_size = cube.size

        if self._n != fa._n:
            fa = fa.clone()
            fa._n = self._n

        # size-1: 3x3 -> R[1:2], 4x4 [1:3]
        return fa[1: cube_size - 1]

    def xsimplify(self) -> "NSimpleAlg|SeqSimpleAlg":
        """
        TODO: simplify Rw == R[1: size-1]
        :return:
        """
        return super().simplify()

    def same_form(self, a: "SimpleAlg"):
        if not isinstance(a, DoubleLayerAlg):
            return False

        return self._of_face_alg._face == a._of_face_alg._face

    #meanwhile


    def _basic_clone(self) -> Self:
        cl = DoubleLayerAlg.__new__(type(self))
        # noinspection PyArgumentList
        cl.__init__(self._of_face_alg)  # type: ignore

        return cl
