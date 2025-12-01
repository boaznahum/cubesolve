from typing import Iterator, Self

from cube.domain.algs.SimpleAlg import SimpleAlg
from cube.domain.model.Cube import Cube


class AnnotationAlg(SimpleAlg):
    """
        When played, it simply refreshes GUI
        So it used by annotation tools, after they changed some model(text, cube)
    """

    def __init__(self) -> None:
        super().__init__()

    def play(self, cube: Cube, inv: bool = False):
        pass

    def count(self) -> int:
        return 0

    def atomic_str(self) -> str:
        return ""  # to satisfy pyright

    def xsimplify(self) -> "SimpleAlg":
        return self

    def flatten(self) -> Iterator["SimpleAlg"]:
        yield self

    def simple_inverse(self) -> Self:
        return self # not really an alg

    def __str__(self) -> str:
        return "AnnotationAlg"
