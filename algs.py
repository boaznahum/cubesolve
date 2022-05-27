import functools
from abc import ABC, abstractmethod
from collections.abc import MutableSequence
from random import Random
from typing import Sequence, Any, final, TypeVar, Tuple, Iterable

from app_exceptions import InternalSWError
from cube import Cube
from cube_slice import SliceName
from elements import FaceName, AxisName, PartSlice


def _inv(inv: bool, n) -> int:
    return -n if inv else n


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

    @abstractmethod
    def flatten(self) -> Iterable["SimpleAlg"]:
        pass

    @property
    def is_ann(self):
        return False


class _Inv(Alg):
    __slots__ = "_alg"

    def __init__(self, _a: Alg) -> None:
        super().__init__()
        self._alg = _a

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

        """
        Must returns SimpleAlg if _alg is SimpleAlg
        :return:
        """

        if isinstance(self._alg, _Inv):
            return self._alg.simplify()

        a = self._alg.simplify()  # can't be _Mul, nor Inv

        if isinstance(a, SimpleAlg):
            c = type(a)
            # noinspection PyArgumentList
            s = c()  # type: ignore # _n = 1
            s._n = -a.n  # inv
            return s.simplify()
        elif isinstance(a, _BigAlg):

            algs = [a.inv() for a in reversed(a.algs)]
            return _BigAlg(None, *algs).simplify()
        else:
            raise TypeError("Unknown type:", type(self))

    def flatten(self) -> Iterable["SimpleAlg"]:

        """
        Must returns SimpleAlg if _alg is SimpleAlg
        :return:
        """

        a = self.simplify()  # can't be _Mul, nor Inv

        return a.flatten()


@final
class _Mul(Alg, ABC):
    __slots__ = ["_alg", "_n"]

    def __init__(self, a: Alg, n: int) -> None:
        super().__init__()
        self._alg = a
        self._n = n

    def atomic_str(self):

        if isinstance(self._alg, SimpleAlg):
            return self.simplify().atomic_str()  # R3 -> R'

        s = self._alg.atomic_str()

        if self._n != 1:
            s += str(self._n)

        return s

    def play(self, cube: Cube, inv: bool):

        for _ in range(0, self._n):
            self._alg.play(cube, inv)

    def count(self) -> int:
        if not isinstance(self._alg, _BigAlg):
            return _normalize_for_count(self._n) * self._alg.count()
        else:
            return self._n * self._alg.count()

    def simplify(self) -> "Alg":

        a = self._alg.simplify()  # can't be _Mul

        if isinstance(a, SimpleAlg):
            c = type(a)
            # noinspection PyArgumentList
            # todo: every where we clone like this, there is a bug, beucase we added _a_slice, need to use clone method
            s = c()  # type: ignore # _n = 1
            s._n *= a._n * self._n
            return s.simplify()
        elif isinstance(self._alg, _BigAlg):
            algs = [a.simplify() for a in self._alg._algs] * self._n
            return _BigAlg(None, *algs).simplify()
        else:
            raise TypeError("Unknown type:", type(self))

    def flatten(self) -> Iterable["SimpleAlg"]:
        return self.simplify().flatten()


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


class SimpleAlg(Alg, ABC):
    __slots__ = ["_n", "_code"]

    def __init__(self, code: str, n: int = 1) -> None:
        super().__init__()
        self._code = code
        self._n = n

    def copy(self, other: "SliceAbleAlg"):
        self._n = other.n
        return self

    def atomic_str(self):
        return n_to_str(self._code, self._n)

    def __str__(self):
        return self.atomic_str()

    def count(self) -> int:
        if self.is_whole:
            return 0
        else:
            return _normalize_for_count(self._n)

    @property
    def n(self):
        return self._n

    @final
    def simplify(self) -> "Alg":
        return self

    def flatten(self) -> Iterable["SimpleAlg"]:
        return [self]

    # ---------------------------------
    # type of simple: face, axis, slice

    @property
    def face(self) -> FaceName | None:
        return None

    @property
    def is_whole(self):
        return False

    @property
    def axis_name(self) -> AxisName | None:
        # only if whole is true
        return None

    @property
    def slice_name(self) -> SliceName | None:
        """
        only for SliceAlg
        :return:
        """
        return None


class Annotation(SimpleAlg):

    def __init__(self, n: int = 1) -> None:
        super().__init__("ann", n)

    def play(self, cube: Cube, inv: bool):
        pass

    @property
    def is_ann(self):
        return True


class AnimationAbleAlg(SimpleAlg, ABC):

    @abstractmethod
    def get_animation_objects(self, cube: Cube) -> Tuple[FaceName, Sequence[PartSlice]]:
        """

        :param cube:
        :return: The face for rotation Axis and all cube elements involved in this animation
        """
        pass


SL = TypeVar("SL", bound="SliceAbleAlg")


class SliceAbleAlg(SimpleAlg, ABC):

    def __init__(self, code: str, n: int = 1) -> None:
        super().__init__(code, n)
        self.a_slice: slice | None = None  # [1 n]

    def copy(self, other: "SliceAbleAlg"):
        super(SliceAbleAlg, self).copy(other)
        self.a_slice = other.a_slice
        return self

    @final
    def clone(self) -> "SliceAbleAlg":
        cl = SimpleAlg.__new__(type(self))
        # noinspection PyArgumentList
        cl.__init__()  # type: ignore
        cl.copy(self)

        return cl

    def __getitem__(self: SL, items) -> SL:

        if not items:
            return self

        if self.a_slice is not None:
            raise InternalSWError(f"Already sliced: {self}")
        if isinstance(items, int):
            a_slice = slice(items)  # start/stop the same
        elif isinstance(items, slice):
            a_slice = items
        else:
            raise InternalSWError(f"Unknown type for slice: {items} {type(items)}")

        clone: SliceAbleAlg = self.clone()
        clone.a_slice = a_slice

        return clone  # type: ignore

    @property
    def start(self):
        if not self.a_slice:
            return None

        sl = self.a_slice

        start = sl.start
        stop = sl.stop

        if stop and not start:
            return 1
        else:
            return start  # maybe be None

    @property
    def stop(self):
        if not self.a_slice:
            return None

        sl = self.a_slice

        return sl.stop  # may be NOne

    def __str__(self):
        s = super().__str__()

        if not self.a_slice:
            return s

        start = self.start
        stop = self.stop

        if not start and not stop:
            return s

        if start == stop or not stop:
            if start == 1:
                return s
            else:
                return str(start) + s
        else:
            return "[" + str(start) + "," + str(stop) + "]" + s


class FaceAlg(SliceAbleAlg, AnimationAbleAlg, ABC):

    def __init__(self, face: FaceName, n: int = 1) -> None:
        super().__init__(face.value, n)
        self._face: FaceName = face

    @property
    def face(self) -> FaceName:
        return self._face

    @final
    def play(self, cube: Cube, inv: bool):

        start_stop = self.normalize_slice_index()

        cube.rotate_face_and_slice(_inv(inv, self._n), self._face, start_stop)

    def get_animation_objects(self, cube) -> Tuple[FaceName, Sequence[PartSlice]]:

        face = self._face

        start_stop = self.normalize_slice_index()

        parts: Sequence[Any] = cube.get_rotate_face_and_slice_involved_parts(face, start_stop)

        return face, parts

    def normalize_slice_index(self) -> slice:

        """

        :return: [start, stop] in cube coordinates [0, size-2]
        """
        start = self.start
        stop = self.stop

        _stop = None
        _start = None

        if not start and not stop:

            _start, _stop = (1, 1)

        elif start and not stop:
            _start, _stop = (start, start)

        elif not start and stop:
            _start, _stop = (1, stop)

        else:
            _start, _stop = (start, stop)

        assert _start
        assert _stop

        return slice(_start-1, _stop-1)


class WholeCubeAlg(SimpleAlg, ABC):

    def __init__(self, axis_name: AxisName, n: int = 1) -> None:
        super().__init__(axis_name.value, n)
        self._axis_name = axis_name

    @property
    def axis_name(self) -> AxisName:
        return self._axis_name

    @final
    def play(self, cube: Cube, inv: bool):
        cube.rotate_whole(self.axis_name, _inv(inv, self._n))

    @final
    @property
    def is_whole(self):
        return True


class SliceAlg(SliceAbleAlg, ABC):

    def __init__(self, slice_name: SliceName, n: int = 1) -> None:
        super().__init__(slice_name.value, n)
        self._slice_name = slice_name

    @property
    def slice_name(self) -> SliceName | None:
        return self._slice_name

    @final
    def play(self, cube: Cube, inv: bool):
        cube.rotate_slice(self._slice_name, _inv(inv, self._n))


@final
class _U(FaceAlg):

    def __init__(self) -> None:
        super().__init__(FaceName.U)


@final
class _D(FaceAlg):

    def __init__(self) -> None:
        super().__init__(FaceName.D)


@final
class _F(FaceAlg):

    def __init__(self) -> None:
        super().__init__(FaceName.F)


@final
class _B(FaceAlg):

    def __init__(self) -> None:
        super().__init__(FaceName.B)


@final
class _R(FaceAlg):

    def __init__(self) -> None:
        super().__init__(FaceName.R)


@final
class _L(FaceAlg):

    def __init__(self) -> None:
        super().__init__(FaceName.L)


@final
class _M(SliceAlg):

    def __init__(self) -> None:
        super().__init__(SliceName.M)


@final
class _X(WholeCubeAlg):

    def __init__(self) -> None:
        super().__init__(AxisName.X)


@final
class _E(SliceAlg):
    """
    Middle slice over D
    """

    def __init__(self) -> None:
        super().__init__(SliceName.E)


@final
class _Y(WholeCubeAlg):

    def __init__(self) -> None:
        super().__init__(AxisName.Y)


@final
class _S(SliceAlg):
    """
    Middle slice over F
    """

    def __init__(self) -> None:
        super().__init__(SliceName.S)


@final
class _Z(WholeCubeAlg):

    def __init__(self) -> None:
        super().__init__(AxisName.Z)


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
            cube.sanity()
            for i, a in enumerate(self._algs):
                # cube.sanity()
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

            if isinstance(a, SimpleAlg):
                flat_algs.append(a)
            elif isinstance(a, _BigAlg):
                flat_algs.extend(a._algs)
            else:
                raise TypeError("Unexpected type", type(a))

        combined = self._combine(flat_algs)
        return _BigAlg(self._name, *combined)

    def flatten(self) -> Iterable["SimpleAlg"]:
        for a in self._algs:
            yield from a.flatten()

    @staticmethod
    def _combine(algs: Sequence[Alg]) -> Sequence[Alg]:

        work_to_do = bool(algs)
        while work_to_do:
            work_to_do = False
            new_algs = []
            prev: Alg | None = None
            for a in algs:
                if not isinstance(a, SimpleAlg):
                    raise TypeError("Unexpected type", type(a))

                if prev:
                    if type(prev) == type(a):

                        assert isinstance(prev, SimpleAlg)

                        c = type(a)
                        # noinspection PyArgumentList
                        a2 = c()  # type: ignore # _n = 1
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

    @property
    def algs(self):
        return self._algs


class _Scramble(_BigAlg):

    def __init__(self, name: str | None, *algs: Alg) -> None:
        super().__init__(name, *algs)

    def count(self) -> int:
        return 0


def _scramble(cube_size: int, seed: Any, n: int | None = None) -> Alg:
    rnd: Random = Random(seed)

    if not n:
        n = rnd.randint(400, 800)
    # n = rnd.randint(5, 6)

    s = Algs.Simple

    algs: list[Alg] = []

    for i in range(n):
        a = rnd.choice(s)

        if isinstance(a, FaceAlg) and rnd.randint(1, 6):  # 1/6 percentage
            sta = rnd.randint(1, cube_size - 1)
            if sta == cube_size - 1:
                sto = sta
            else:
                left = cube_size - 1 - sta

                if left == 0 or rnd.random() > 0.5:
                    sto = sta
                else:
                    sto = rnd.randint(1, left) + sta

            a = a[sta:sto]

        algs.append(a)

    name: str
    if seed:
        name = str(seed)
    else:
        # noinspection SpellCheckingInspection
        name = "random-scrm"

    return _Scramble(name + "[" + str(n) + "]", *algs)


class Algs:
    AN = Annotation()
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
              R, X, M,
              U, E, Y,
              F, Z, S,
              B,
              D,
              ]

    RU = _BigAlg("RU(top)", R, U, -R, U, R, U * 2, -R, U)

    UR = _BigAlg("UR(top)", U, R, -U, -L, U, -R, -U, L)

    RD = _BigAlg("RD(top)", ((R.prime + D.prime + R + D) * 2 + U) * 3)

    @staticmethod
    def lib() -> Sequence[Alg]:
        return [
            Algs.RU,
            Algs.UR
        ]

    @classmethod
    def scramble1(cls, cube_size):
        return _scramble(cube_size, "scramble1")

    @classmethod
    def scramble(cls, cube_size, seed=None, n: int | None = None):
        return _scramble(cube_size, seed, n)

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
    _a = alg.simplify()
    print(_a.__str__())
    print(alg.simplify())
