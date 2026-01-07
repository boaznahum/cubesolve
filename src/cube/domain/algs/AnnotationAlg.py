from typing import Iterator, Self

from cube.domain.algs.SimpleAlg import SimpleAlg
from cube.domain.model.Cube import Cube


class AnnotationAlg(SimpleAlg):
    """
    When played, it simply refreshes GUI.
    Used by annotation tools after they changed some model (text, cube).

    All instances are frozen (immutable) after construction.
    """

    __slots__ = ()  # No additional slots

    def __init__(self) -> None:
        super().__init__()
        self._freeze()

    def play(self, cube: Cube, inv: bool = False) -> None:
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
        return self  # not really an alg

    def __str__(self) -> str:
        return "AnnotationAlg"
