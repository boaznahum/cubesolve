import functools
from abc import ABC, abstractmethod
from collections.abc import MutableSequence
from random import Random
from typing import Sequence, Any, final

from cube import Cube


def _inv(inv: bool) -> int:
    return -1 if inv else 1


class Alg(ABC):

    @abstractmethod
    def play(self, cube: Cube, inv: bool): ...

    def inv(self) -> "Alg":
        return _Inv(self)

    @property
    def prime(self) -> "Alg":
        return _Inv(self)

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def atomic_str(self):
        pass

    @abstractmethod
    def simplify(self) -> "Alg":
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

    def count(self) -> int:
        return self._alg.count()

    def simplify(self) -> "Alg":

        a = self._alg.simplify()  # can't be _Mul

        if isinstance(a, _SimpleAlg):
            c = type(a)
            s = c()  # _n = 1
            s._n = -a._n  # inv
            return s.simplify()
        elif isinstance(a, _BigAlg):

            algs = [a.inv() for a in reversed(a._algs)]
            return _BigAlg(None, *algs).simplify()
        else:
            raise TypeError("Unknown type:", type(self))


@final
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

    def count(self) -> int:
        if not isinstance(self._alg, _BigAlg):
            return _normalize_for_count(self._n) * self._alg.count()
        else:
            return self._n * self._alg.count()

    def simplify(self) -> "Alg":

        a = self._alg.simplify()  # can't be _Mul

        if isinstance(a, _SimpleAlg):
            c = type(a)
            s = c()  # _n = 1
            s._n *= a._n * self._n
            return s.simplify()
        elif isinstance(self._alg, _BigAlg):
            algs = [a.simplify() for a in self._alg._algs] * self._n
            return _BigAlg(None, *algs).simplify()
        else:
            raise TypeError("Unknown type:", type(self))


def _normalize_for_str(n) -> int:
    n %= 4
    return n


def _normalize_for_count(n) -> int:
    n %= 4

    if n == 3:
        n = 1

    return n


def n_to_str(alg_code, n):
    s = alg_code
    n = _normalize_for_str(n)

    if n != 1:
        if n == 0:
            return alg_code + "4"
        elif n == 3:
            return s + "'"
        else:
            return s + str(2)  # 2
    else:
        return s


class _SimpleAlg(Alg, ABC):
    __slots__ = ["_n", "_code"]

    def __init__(self, code: str, n: int = 1) -> None:
        super().__init__()
        self._code = code
        self._n = n

    def atomic_str(self):
        return n_to_str(self._code, self._n)

    def __str__(self):
        return self.atomic_str()

    @property
    def is_whole(self):
        return False

    def count(self) -> int:
        if self.is_whole:
            return 0
        else:
            return _normalize_for_count(self._n)

    @final
    def simplify(self) -> "Alg":
        return self


@final
class _U(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("U")

    def play(self, cube: Cube, inv: bool = False):
        cube.up.rotate(_inv(inv))


@final
class _F(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("F")

    def play(self, cube: Cube, inv: bool = False):
        cube.front.rotate(_inv(inv))


@final
class _R(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("R")

    def play(self, cube: Cube, inv: bool = False):
        cube.right.rotate(_inv(inv))


@final
class _L(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("L")

    def play(self, cube: Cube, inv: bool = False):
        cube.left.rotate(_inv(inv))


@final
class _B(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("B")

    def play(self, cube: Cube, inv: bool = False):
        cube.back.rotate(_inv(inv))


@final
class _D(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("D")

    def play(self, cube: Cube, inv: bool = False):
        cube.down.rotate(_inv(inv))


@final
class _M(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("M")

    def play(self, cube: Cube, inv: bool = False):
        cube.m_rotate(_inv(inv))


@final
class _X(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("X")

    def play(self, cube: Cube, inv: bool = False):
        cube.x_rotate(_inv(inv))

    @property
    def is_whole(self):
        return True


@final
class _E(_SimpleAlg):
    """
    Middle slice over D
    """

    def __init__(self) -> None:
        super().__init__("E")

    def play(self, cube: Cube, inv: bool = False):
        cube.e_rotate(_inv(inv))


@final
class _Y(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("Y")

    def play(self, cube: Cube, inv: bool = False):
        cube.y_rotate(_inv(inv))

    @property
    def is_whole(self):
        return True


@final
class _S(_SimpleAlg):
    """
    Middle slice over F
    """

    def __init__(self) -> None:
        super().__init__("S")

    def play(self, cube: Cube, inv: bool = False):
        cube.s_rotate(_inv(inv))


@final
class _Z(_SimpleAlg):

    def __init__(self) -> None:
        super().__init__("Y")

    def play(self, cube: Cube, inv: bool = False):
        cube.z_rotate(_inv(inv))

    @property
    def is_whole(self):
        return True


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

    def simplify(self) -> "Alg":

        flat_algs: MutableSequence[Alg] = []

        for a in self._algs:
            a = a.simplify()

            if isinstance(a, _SimpleAlg):
                flat_algs.append(a)
            elif isinstance(a, _BigAlg):
                flat_algs.extend(a._algs)
            else:
                raise TypeError("Unexpected type", type(a))

        combined = self._combine(flat_algs)
        return _BigAlg(self._name, *combined)

    def _combine(self, algs: Sequence[Alg]) -> Sequence[Alg]:

        work_to_do = bool(algs)
        while work_to_do:
            work_to_do = False
            new_algs = []
            prev: Alg | None = None
            for a in algs:
                if not isinstance(a, _SimpleAlg):
                    raise TypeError("Unexpected type", type(a))

                if prev:
                    if type(prev) == type(a):

                        assert isinstance(prev, _SimpleAlg)

                        c = type(a)
                        a2 = c()  # _n = 1
                        a2._n = prev._n + a._n
                        if a2._n:
                            prev = a2
                        else:
                            prev = None  # R0 is a None
                        work_to_do = True  # really ?
                    else:
                        new_algs.append(prev)
                        prev = a

                else:
                    prev = a

            if prev:
                new_algs.append(prev)

            algs = new_algs

        return algs

    def count(self) -> int:
        return functools.reduce(lambda n, a: n + a.count(), self._algs, 0)

    def __add__(self, other: "Alg"):

        if self._name:
            # we can't combine
            return super().__add__(other)

        if isinstance(other, _BigAlg) and not other._name:
            return _BigAlg(None, *[*self._algs, *other._algs])
        else:
            return _BigAlg(None, *[*self._algs, other])


class _Scramble(_BigAlg):

    def __init__(self, name: str | None, *algs: Alg) -> None:
        super().__init__(name, *algs)

    def count(self) -> int:
        return 0


def _scramble(seed: Any) -> Alg:
    rnd: Random = Random(seed)

    n = rnd.randint(400, 800)

    s = Algs.Simple

    algs: list[Alg] = [rnd.choice(s) for _ in range(0, n)]

    name: str
    if seed:
        name = str(seed)
    else:
        # noinspection SpellCheckingInspection
        name = "random-scrm"

    return _Scramble(name + "[" + str(n) + "]", *algs)


class Algs:
    L = _L()
    B = _B()
    D = _D()

    R = _R()
    X = _X()  # Entire cube or R
    M = _M()  # Middle over R

    U = _U()
    Y = _Y()  # Entire over U
    E = _E()  # Middle slice over D

    F = _F()
    Z = _Z()  # Entire over F
    S = _S()  # Middle over F

    Simple = [L,
              R,  X, M,
              U,  E, Y,
              F,  Z, S,
              B,
              D,
              ]

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
    def scramble(cls, seed=None):
        return _scramble(seed)

    @classmethod
    def alg(cls, name, *algs: Alg):
        return _BigAlg(name, *algs)

    @classmethod
    def simplify(cls, *algs: Alg) -> Alg:
        return cls.alg(None, *algs).simplify()

    @classmethod
    def count(cls, *algs: Alg) -> int:
        return cls.alg(None, *algs).count()


if __name__ == '__main__':
    alg = Algs.alg(None, _R(), (_R().prime * 2 + Algs.R * 2))
    print(alg)
    print(alg.simplify())

    alg = Algs.R + Algs.U + Algs.U + Algs.U + Algs.U
    a = alg.simplify()
    print(a.__str__())
    print(alg.simplify())
