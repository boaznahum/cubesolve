from abc import ABC, abstractmethod
from typing import Sequence

from cube import Cube


def _inv(inv: bool) -> int:
    return -1 if inv else 1


def _invinv(inv: bool) -> int:
    return 1 if inv else -1


class Alg(ABC):

    @abstractmethod
    def play(self, cube: Cube, inv: bool = False): ...


class U(Alg):
    def play(self, cube: Cube, inv: bool = False):
        cube.up.rotate(_inv(inv))

    def __str__(self):
        return "U"


class UT(Alg):
    def play(self, cube: Cube, inv: bool = False):
        cube.up.rotate(_invinv(inv))

    def __str__(self):
        return "U'"


class F(Alg):
    def play(self, cube: Cube, inv: bool = False):
        cube.front.rotate(_inv(inv))

    def __str__(self):
        return "F"


class FT(Alg):
    def play(self, cube: Cube, inv: bool = False):
        cube.front.rotate(_invinv(inv))

    def __str__(self):
        return "F'"


class R(Alg):
    def play(self, cube: Cube, inv: bool = False):
        cube.right.rotate(_inv(inv))

    def __str__(self):
        return "R"


class RT(Alg):
    def play(self, cube: Cube, inv: bool = False):
        cube.right.rotate(_invinv(inv))

    def __str__(self):
        return "R'"


class L(Alg):
    def play(self, cube: Cube, inv: bool = False):
        cube.left.rotate(_inv(inv))

    def __str__(self):
        return "L"


class LT(Alg):
    def play(self, cube: Cube, inv: bool = False):
        cube.left.rotate(_invinv(inv))

    def __str__(self):
        return "L'"


class _BigAlg(Alg):

    def __init__(self, name: str, *algs: Alg) -> None:
        super().__init__()
        self._name = name
        self._algs: list[Alg] = [*algs]

    def play(self, cube: Cube, inv: bool = False):

        if inv:

            for a in reversed(self._algs):
                a.play(cube, True)
        else:
            for a in self._algs:
                a.play(cube)

    def __str__(self):
        return self._name


class Algs:
    RU = _BigAlg("RU(top)", R(), U(), RT(), U(), R(), U(), U(), RT(), U())

    UR = _BigAlg("UR(top)", U(), R(), UT(), LT(), U(), RT(), UT(), L())

    @staticmethod
    def lib() -> Sequence[Alg]:
        return [
            Algs.RU,
            Algs.UR
        ]
