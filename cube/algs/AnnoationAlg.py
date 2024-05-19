from typing import Iterator

from cube.algs.SimpleAlg import SimpleAlg
from cube.model import Cube


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

    def simplify(self) -> "SimpleAlg":
        return self

    def flatten(self) -> Iterator["SimpleAlg"]:
        yield self

    def inv_and_flatten(self) -> Iterator["SimpleAlg"]:
        yield self  # not really an alg

    def __str__(self) -> str:
        return "AnnotationAlg"
