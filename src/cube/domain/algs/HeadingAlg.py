from typing import Iterator, Self

from cube.domain.algs.AnnotationAlg import AnnotationAlg
from cube.domain.algs.SimpleAlg import SimpleAlg


class HeadingAlg(AnnotationAlg):
    """An annotation that carries heading text (h1).

    Unlike plain AnnotationAlg, HeadingAlg survives in the operator's history
    even when animation is off. This allows heading labels to appear in the
    WebGL queue display as section separators.
    """

    __slots__ = ("_h1",)

    def __init__(self, h1: str) -> None:
        # AnnotationAlg.__init__ calls _freeze(), so we need to set _h1 first
        # We bypass the parent __init__ and do it manually
        super(AnnotationAlg, self).__init__()  # call SimpleAlg.__init__
        self._h1 = h1
        self._freeze()

    @property
    def h1(self) -> str:
        return self._h1

    def flatten(self) -> Iterator["SimpleAlg"]:
        yield self

    def xsimplify(self) -> "SimpleAlg":
        return self

    def simple_inverse(self) -> Self:
        return self  # heading is symmetric

    def __str__(self) -> str:
        return f"HeadingAlg({self._h1!r})"
