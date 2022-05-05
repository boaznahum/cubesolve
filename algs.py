from abc import ABC, abstractmethod
from random import Random
from typing import Sequence, Any

from cube import Cube


def _inv(inv: bool) -> int:
    return -1 if inv else 1


class Alg(ABC):

    @abstractmethod
    def play(self, cube: Cube, inv: bool): ...

    def inv(self) -> "Alg":
        return _Inv(self)

    @abstractmethod
    def atomic_str(self):
        pass

    def __str__(self) -> str:
        return self.atomic_str()

    def __repr__(self) -> str:
        return self.__str__()

    def __neg__(self):
        return self.inv()

    def __mul__(self, n: int):
        return _Mul(self, n)

    def __add__(self, other: "Alg"):
        return _BigAlg(None, self, other)


class _Inv(Alg):
    __slots__ = "_alg"

    def __init__(self, a: Alg) -> None:
        super().__init__()
        self._alg = a

    def __str__(self) -> str:
        return self._alg.atomic_str() + "'"

    def play(self, cube: Cube, inv: bool):
        self._alg.play(cube, not inv)

    def inv(self) -> Alg:
        return self._alg

    def atomic_str(self):
        return self._alg.atomic_str() + "'"


class _Mul(Alg, ABC):
    __slots__ = ["_alg", "_n"]

    def __init__(self, a: Alg, n: int) -> None:
        super().__init__()
        self._alg = a
        self._n = n

    def atomic_str(self):
        s = self._alg.atomic_str()

        if self._n != 1:
            s += str(self._n)

        return s

    def play(self, cube: Cube, inv: bool):

        for _ in range(0, self._n):
            self._alg.play(cube, inv)

    def inv(self) -> Alg:
        return self._alg


class _SimpleAlg(Alg, ABC):
    __slots__ = ["_n", "_code"]

    def __init__(self, code: str, n: int = 1) -> None:
        super().__init__()
        self._code = code
        self._n = n

    def atomic_str(self):
        s = self._code
        if self._n != 1:
            s += str(self._n)

        return s

    def __str__(self):
        return self.atomic_str()


class _U(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("U")

    def play(self, cube: Cube, inv: bool = False):
        cube.up.rotate(_inv(inv))

    def __str__(self):
        return "U"


class _F(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("F")

    def play(self, cube: Cube, inv: bool = False):
        cube.front.rotate(_inv(inv))


class _R(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("R")

    def play(self, cube: Cube, inv: bool = False):
        cube.right.rotate(_inv(inv))


class _L(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("L")

    def play(self, cube: Cube, inv: bool = False):
        cube.left.rotate(_inv(inv))


class _B(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("B")

    def play(self, cube: Cube, inv: bool = False):
        cube.back.rotate(_inv(inv))


class _D(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("D")

    def play(self, cube: Cube, inv: bool = False):
        cube.down.rotate(_inv(inv))


class _M(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("M")

    def play(self, cube: Cube, inv: bool = False):
        cube.m_rotate(_inv(inv))


class _X(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("X")

    def play(self, cube: Cube, inv: bool = False):
        cube.x_rotate(_inv(inv))


class _E(_SimpleAlg):
    """
    Middle slice over D
    """

    def __init__(self) -> None:
        super().__init__("E")

    def play(self, cube: Cube, inv: bool = False):
        cube.e_rotate(_inv(inv))


class _Y(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("Y")

    def play(self, cube: Cube, inv: bool = False):
        cube.y_rotate(_inv(inv))


class _BigAlg(Alg):

    def __init__(self, name: str | None, *algs: Alg) -> None:
        super().__init__()
        self._name = name
        self._algs: list[Alg] = [*algs]

    def play(self, cube: Cube, inv: bool = False):

        if inv:

            for a in reversed(self._algs):
                a.play(cube, True)
        else:
            for i, a in enumerate(self._algs):
                cube.sanity()
                a.play(cube, False)
                cube.sanity()

    def atomic_str(self):
        if self._name:
            return "{" + self._name + "}"
        else:
            if len(self._algs) == 1:
                return self._algs[0].atomic_str()
            else:
                return "[" + " ".join([str(a) for a in self._algs]) + "]"

    def __add__(self, other: "Alg"):

        if self._name:
            # we can't combine
            return super().__add__(other)

        if isinstance(other, _BigAlg) and not other._name:
            return _BigAlg(None, *[*self._algs, * other._algs])
        else:
            return _BigAlg(None, *[ *self._algs, other])



def _scramble(seed: Any) -> Alg:
    rnd: Random = Random(seed)

    n = rnd.randint(400, 800)

    s = Algs.Simple

    algs: list[Alg] = [rnd.choice(s) for _ in range(0, n)]

    name: str
    if seed:
        name = str(seed)
    else:
        name = "random-scrm"

    return _BigAlg(name + "[" + str(n) + "]", *algs)


class Algs:
    L = _L()
    R = _R()
    U = _U()
    F = _F()
    B = _B()
    D = _D()

    M = _M()
    X = _X()

    # Middle slice over D
    E = _E()
    # entire over U
    Y = _Y()

    Simple = [L, R, U, F, B, D, M, X, U]

    RU = _BigAlg("RU(top)", R, U, -R, U, R, U * 2, -R, U)

    UR = _BigAlg("UR(top)", U, R, -U, -L, U, -R, -U, L)

    @staticmethod
    def lib() -> Sequence[Alg]:
        return [
            Algs.RU,
            Algs.UR
        ]

    @classmethod
    def scramble1(cls):
        return _scramble("scramble1")

    @classmethod
    def scramble(cls):
        return _scramble(None)
