import functools
import warnings
from abc import ABC, abstractmethod
from collections.abc import MutableSequence, Collection
from random import Random
from typing import Sequence, Any, final, TypeVar, Tuple, Iterable, Iterator, Self

from cube.algs._parser import parse_alg
from cube.app_exceptions import InternalSWError
from cube.model.cube import Cube
from cube.model.cube_slice import SliceName
from cube.model import FaceName, AxisName

__all__ = ["Algs", "Alg", "SimpleAlg", "AnimationAbleAlg", "AnnotationAlg",
           "NSimpleAlg",
           "SliceAbleAlg", "SeqAlg", "SliceAlg", "FaceAlg", "WholeCubeAlg"]

from cube.model import PartSlice


def _inv(inv: bool, n) -> int:
    return -n if inv else n


class Alg(ABC):

    @abstractmethod
    def play(self, cube: Cube, inv: bool = False): ...

    def inv(self) -> "Alg":
        return _Inv(self)

    @property
    def prime(self) -> "Alg":
        return _Inv(self)

    @property
    def p(self) -> "Alg":
        return _Inv(self)

    @abstractmethod
    def count(self) -> int:
        """
            return number of 90 moves, nn = n % 4, nn:1 -> 1 nn:2 -> 2 nn:3 -> 1
        """
        pass

    @abstractmethod
    def atomic_str(self):
        pass

    @abstractmethod
    def simplify(self) -> "SimpleAlg|SeqSimpleAlg":
        """
        In case of big alg, try to simplify R+R2 == R
        :return:
        """
        pass

    @abstractmethod
    def flatten(self) -> Iterator["SimpleAlg"]:
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
        return SeqAlg(None, self, other)

    def __iadd__(self, other: "Alg"):
        return SeqAlg(None, self, other)

    def __sub__(self, other: "Alg"):
        return SeqAlg(None, self, other.prime)


class _Inv(Alg):
    __slots__ = "_alg"

    def __init__(self, _a: Alg) -> None:
        super().__init__()
        self._alg = _a

    def __str__(self) -> str:
        return self._alg.atomic_str() + "'"

    def play(self, cube: Cube, inv: bool = False):
        self._alg.play(cube, not inv)

    def inv(self) -> Alg:
        return self._alg

    def atomic_str(self):
        return self._alg.atomic_str() + "'"

    def count(self) -> int:
        return self._alg.count()

    def simplify(self) -> "SimpleAlg|SeqSimpleAlg":

        """
        Must returns SimpleAlg if _alg is SimpleAlg
        :return:
        """

        if isinstance(self._alg, _Inv):
            # X'' = X
            return self._alg._alg.simplify()

        a = self._alg.simplify()  # can't be _Mul, nor Inv

        if isinstance(a, NSimpleAlg):
            s = a.clone()
            s *= -1  # inv - that is my function
            return s.simplify()
        elif isinstance(a, AnnotationAlg):
            return a
        elif isinstance(a, SeqAlg):

            algs = [a.inv() for a in reversed(a.algs)]
            return SeqAlg(None, *algs).simplify()
        else:
            raise TypeError("Unknown type:", type(self))

    def flatten(self) -> Iterator["SimpleAlg"]:

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

        if isinstance(self._alg, NSimpleAlg):
            return self.simplify().atomic_str()  # R3 -> R'

        s = self._alg.atomic_str()

        if self._n != 1:
            s += str(self._n)

        return s

    def play(self, cube: Cube, inv: bool = False):

        for _ in range(0, self._n):
            self._alg.play(cube, inv)

    def count(self) -> int:
        if not isinstance(self._alg, SeqAlg):
            return _normalize_for_count(self._n) * self._alg.count()
        else:
            return self._n * self._alg.count()

    def simplify(self) -> "SimpleAlg|SeqSimpleAlg":

        a = self._alg.simplify()  # can't be _Mul

        if isinstance(a, NSimpleAlg):
            s = a.clone()
            s *= self._n  # multipy by me - that is my function
            return s.simplify()
        elif isinstance(a, AnnotationAlg):
            return a
        elif isinstance(self._alg, SeqAlg):
            # noinspection PyProtectedMember
            algs = [a.simplify() for a in self._alg._algs] * self._n
            return SeqAlg(None, *algs).simplify()
        else:
            raise TypeError("Unknown type:", type(self))

    def flatten(self) -> Iterator["SimpleAlg"]:
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


TNSimpleAlg = TypeVar("TNSimpleAlg", bound="NSimpleAlg")


class SimpleAlg(Alg, ABC):

    def __init__(self) -> None:
        super().__init__()


class NSimpleAlg(SimpleAlg, ABC):
    """
    A simple alg with n property,
    Follows the rule of simple rotation n == N % 4
    """

    __slots__ = ["_n", "_code"]

    # todo: most of the code in this lags should be moved into NSimpleAlg

    def __init__(self, code: str, n: int = 1) -> None:
        super().__init__()
        self._code = code
        self._n = n

    def simple_mul(self, n: int):
        c = self.clone()
        c._n *= n

        return c

    def _basic_clone(self: Self) -> Self:
        cl = NSimpleAlg.__new__(type(self))
        # noinspection PyArgumentList
        cl.__init__()  # type: ignore

        return cl

    @final
    def clone(self) -> Self:
        cl = self._basic_clone()

        cl.copy(self)

        return cl

    def copy(self, other: Self):
        self._n = other.n
        return self

    def atomic_str(self):
        return n_to_str(self._code, self._n)

    def __str__(self):
        return self.atomic_str()

    def count(self) -> int:
        return _normalize_for_count(self._n)

    @property
    def n(self):
        return self._n

    def simplify(self) -> "NSimpleAlg|SeqSimpleAlg":
        if self._n % 4:
            return self
        else:
            return SeqSimpleAlg(None)

    def flatten(self) -> Iterator["SimpleAlg"]:
        yield self

    # ---------------------------------
    # type of simple: face, axis, slice

    def same_form(self, a: "SimpleAlg"):
        return True

    def __imul__(self, other: int):
        """
        For simple algorithm inv and mul
        :param other:
        :return:
        """
        self._n *= other
        return self

    @property
    def code(self):
        return self._code


class AnnotationAlg(SimpleAlg):

    def __init__(self) -> None:
        super().__init__()

    def play(self, cube: Cube, inv: bool = False):
        pass

    def count(self) -> int:
        return 0

    def atomic_str(self):
        pass

    def simplify(self) -> "SimpleAlg":
        return self

    def flatten(self) -> Iterator["SimpleAlg"]:
        yield self

    def __str__(self) -> str:
        return "AnnotationAlg"


class AnimationAbleAlg(NSimpleAlg, ABC):

    @abstractmethod
    def get_animation_objects(self, cube: Cube) -> Tuple[FaceName, Collection[PartSlice]]:
        """

        :param cube:
        :return: The face for rotation Axis and all cube elements involved in this animation
        """
        pass


SL = TypeVar("SL", bound="SliceAbleAlg")


class SliceAbleAlg(NSimpleAlg, ABC):

    def __init__(self, code: str, n: int = 1) -> None:
        super().__init__(code, n)
        # sorted sequence
        self.slices: slice | Sequence[int] | None = None  # [1 n]

    def copy(self, other: Self):
        assert isinstance(other, SliceAbleAlg)
        super(SliceAbleAlg, self).copy(other)
        self.slices = other.slices
        return self

    def __getitem__(self: SL, items) -> SL:

        if not items:
            return self

        a_slice: slice | Sequence[int]
        if self.slices is not None:
            raise InternalSWError(f"Already sliced: {self}")
        if isinstance(items, int):
            a_slice = slice(items, items)  # start/stop the same
        elif isinstance(items, slice):
            a_slice = items
        elif isinstance(items, Sequence):
            a_slice = sorted(items)
        else:
            raise InternalSWError(f"Unknown type for slice: {items} {type(items)}")

        clone: SliceAbleAlg = self.clone()
        clone.slices = a_slice

        return clone  # type: ignore

    @property
    def start(self):
        if not self.slices:
            return None

        return self.slices.start

    @property
    def stop(self):
        if not self.slices:
            return None
        return self.slices.stop

    def _add_to_str(self, s):
        """
                    None -> default = R
                    (None, None) -> default R
                    (1, 1) -> default R
                    (start, None) -> [start:]R
                    (None, stop) -> [:stop] == [1:stop]
                    (start, stop) -> [start:stop]

                :param s:
                :return:
                """

        slices = self.slices

        if slices is None:
            return s

        if isinstance(slices, slice):

            start = self.start
            stop = self.stop

            if not start and not stop:
                return s

            if 1 == start and 1 == stop:
                return s

            if start and not stop:
                return "[" + str(start) + ":" + "]" + s

            if not start and stop:
                return "[1:" + str(stop) + "]" + s

            if start and stop:
                return "[" + str(start) + ":" + str(stop) + "]" + s

            raise InternalSWError(f"Unknown {start} {stop}")
        else:
            return "[" + ",".join(str(i) for i in slices) + "]" + s

    def atomic_str(self):
        return self._add_to_str(super().atomic_str())

    def normalize_slice_index(self, n_max: int, _default: Iterable[int]) -> Iterable[int]:

        """
        We have no way to no what is max n
        :default in [1,n] space
        :return: below - (1,1)

            [i] -> (i,i)  - by  get_item
            None -> (None, None)

            (None, None) -> default
            (start, None) -> (start, n_max)
            (None, Stop) -> (1, stop)
            (start, stop) -> (1, stop)



        :return: [start, stop] in cube coordinates [0, size-2]
        """

        slices = self.slices

        res: Iterable[int]

        if slices is None:
            res = _default

        elif isinstance(slices, Sequence):
            res = slices

        else:

            start = self.start
            stop = self.stop

            _stop = None
            _start = None

            if not start and not stop:

                res = _default

            else:
                if start and not stop:
                    _start, _stop = (start, n_max)

                elif not start and stop:
                    _start, _stop = (1, stop)

                else:
                    _start, _stop = (start, stop)

                assert _start
                assert _stop
                res = [*range(_start, stop + 1)]

        return [i - 1 for i in res]

    def same_form(self, a: "SimpleAlg") -> bool:

        if not isinstance(a, SliceAbleAlg):
            return False

        my = self.slices
        other = a.slices
        if my is None and other is None:
            return True

        # todo: optimize it, [1:2] are the same as [1,2]
        # but it become more complicated when it is [1: ] because we don't know
        # the size of the cube
        if type(my) != type(other):
            return False

        if isinstance(my, slice):
            s1 = self.start
            t1 = self.stop

            s2 = a.start
            t2 = a.stop

            return (s1 is None and s2 is None or s1 == s2) and (t1 is None and t2 is None or t1 == t2)
        elif isinstance(my, Sequence):
            assert isinstance(other, Sequence)  # for my py
            # they are sorted
            return my == other
        else:
            raise InternalSWError(f"Unknown type for slices object {my}")


class FaceAlg(SliceAbleAlg, AnimationAbleAlg, ABC):

    def __init__(self, face: FaceName, n: int = 1) -> None:
        # we know it is str, still we need to cast for mypy
        super().__init__(str(face.value), n)
        self._face: FaceName = face



    @final
    def play(self, cube: Cube, inv: bool = False):
        start_stop: Iterable[int] = self.normalize_slice_index(n_max=1 + cube.n_slices, _default=[1])

        cube.rotate_face_and_slice(_inv(inv, self._n), self._face, start_stop)

    def get_animation_objects(self, cube) -> Tuple[FaceName, Collection[PartSlice]]:
        face = self._face

        slices: Iterable[int] = self.normalize_slice_index(n_max=1 + cube.n_slices, _default=[1])

        parts: Collection[Any] = cube.get_rotate_face_and_slice_involved_parts(face, slices)

        return face, parts


class DoubleLayerAlg(AnimationAbleAlg):
    """
    A double layer of given FaceAlg
    For example Rw is double layer of R
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

    def _basic_clone(self) -> Self:
        cl = DoubleLayerAlg.__new__(type(self))
        # noinspection PyArgumentList
        cl.__init__(self._of_face_alg)  # type: ignore

        return cl


class WholeCubeAlg(AnimationAbleAlg, NSimpleAlg, ABC):

    def __init__(self, axis_name: AxisName, n: int = 1) -> None:
        # cast to satisfy numpy
        super().__init__(str(axis_name.value), n)
        self._axis_name = axis_name

    def count(self) -> int:
        return 0

    @final
    def play(self, cube: Cube, inv: bool = False):
        cube.rotate_whole(self._axis_name, _inv(inv, self._n))

    def get_animation_objects(self, cube: Cube) -> Tuple[FaceName, Collection[PartSlice]]:

        face_name: FaceName
        match self._axis_name:

            case AxisName.X:
                face_name = FaceName.R

            case AxisName.Y:
                face_name = FaceName.U

            case AxisName.Z:
                face_name = FaceName.F

            case _:
                raise InternalSWError(f"Unknown Axis {self._axis_name}")

        return face_name, cube.get_all_parts()


class SliceAlg(SliceAbleAlg, AnimationAbleAlg, ABC):

    def __init__(self, slice_name: SliceName, n: int = 1) -> None:
        # we know it is str, still we need to cast for mypy
        super().__init__(slice_name.value.__str__(), n)
        self._slice_name = slice_name

    @property
    def slice_name(self) -> SliceName | None:
        return self._slice_name

    @final
    def play(self, cube: Cube, inv: bool = False):
        # cube.rotate_slice(self._slice_name, _inv(inv, self._n))

        slices = self.normalize_slice_index(n_max=cube.n_slices, _default=range(1, cube.n_slices + 1))

        cube.rotate_slice(self._slice_name, _inv(inv, self._n), slices)

    def get_animation_objects(self, cube: Cube) -> Tuple[FaceName, Collection[PartSlice]]:

        face_name: FaceName

        name = self._slice_name
        match name:

            case SliceName.S:  # over F
                face_name = FaceName.F

            case SliceName.M:  # over L
                face_name = FaceName.L

            case SliceName.E:  # over D
                face_name = FaceName.D

            case _:
                raise RuntimeError(f"Unknown Slice {name}")

        start_stop: Iterable[int] = self.normalize_slice_index(n_max=cube.n_slices,
                                                               _default=range(1, cube.n_slices + 1))

        return face_name, cube.get_rotate_slice_involved_parts(name, start_stop)



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


class SeqAlg(Alg):

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

    def simplify(self) -> "SeqSimpleAlg":

        flat_algs: MutableSequence[SimpleAlg] = []

        for a in self._algs:
            a = a.simplify()

            if isinstance(a, SimpleAlg):
                flat_algs.append(a)
            elif isinstance(a, SeqSimpleAlg):
                flat_algs.extend(a.algs)
            else:
                raise TypeError("Unexpected type", type(a))

        combined = self._combine(flat_algs)
        return SeqSimpleAlg(self._name, *combined)

    def flatten(self) -> Iterator["SimpleAlg"]:
        for a in self._algs:
            yield from a.flatten()

    @staticmethod
    def _combine(algs: Sequence[SimpleAlg]) -> Sequence[SimpleAlg]:

        work_to_do = bool(algs)
        while work_to_do:
            work_to_do = False
            new_algs = []
            prev: NSimpleAlg | None = None
            for a in algs:
                if not isinstance(a, NSimpleAlg):
                    raise TypeError("Unexpected type", type(a))

                if not a.n % 4:  # get rid of R4
                    continue

                if prev:
                    if type(prev) == type(a) and prev.same_form(a):

                        assert isinstance(prev, SimpleAlg)

                        #                        c = type(a)
                        # noinspection PyArgumentList
                        a2 = a.clone()  # type: ignore # _n = 1
                        a2._n = prev.n + a.n
                        if a2.n % 4:
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

        if isinstance(other, SeqAlg) and not other._name:
            return SeqAlg(None, *[*self._algs, *other._algs])
        else:
            return SeqAlg(None, *[*self._algs, other])

    @property
    def algs(self) -> Sequence[Alg]:
        return self._algs


class SeqSimpleAlg(SeqAlg):
    """
    A big alg composed of SimpleAlg s only
    """

    def __init__(self, name: str | None, *algs: SimpleAlg) -> None:
        super().__init__(name, *algs)

    @property
    def algs(self) -> Sequence[SimpleAlg]:
        return super().algs  # type: ignore


class _Scramble(SeqAlg):

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
        name = f"scrmbl{seed}/{n}"
    else:
        # noinspection SpellCheckingInspection
        name = f"random-scrm{n}"

    return _Scramble(name + "[" + str(n) + "]", *algs)


class Algs:
    """
    About Notations
    https://alg.cubing.net/

    E, S, M is according to the above


    X - OK
    Y - OK
    Z - OK


    """
    # When played, it simply refreshes GUI
    # So it used by annotation tools, after they changed some model(text, cube)
    AN = AnnotationAlg()

    L = _L()
    # noinspection PyPep8Naming
    Lw = DoubleLayerAlg(L)

    B = _B()
    Bw = DoubleLayerAlg(B)

    D = _D()
    Dw = DoubleLayerAlg(D)

    R = _R()
    Rw = DoubleLayerAlg(R)
    X = _X()  # Entire cube or R
    M = _M()  # Middle over L
    _MM = _M().simple_mul(-1)  # Middle over L

    # noinspection PyPep8Naming
    @staticmethod
    def MM() -> SliceAlg:
        warnings.warn("Use M'", DeprecationWarning, 2)

        return Algs._MM

    U: FaceAlg = _U()
    Uw = DoubleLayerAlg(U)
    Y = _Y()  # Entire over U
    E = _E()  # Middle slice over D

    F = _F()
    Fw = DoubleLayerAlg(F)
    Z = _Z()  # Entire over F
    S = _S()  # Middle over F

    _NO_OP = SeqAlg(None)

    @staticmethod
    def seq_alg(name: str | None, *algs: Alg) -> SeqAlg:
        return SeqAlg(name, *algs)

    Simple: Sequence[NSimpleAlg] = [L, Lw,
                                    R, Rw, X, M,
                                    U, Uw, E, Y,
                                    F, Fw, Z, S,
                                    B, Bw,
                                    D, Dw,
                                    ]

    RU = SeqAlg("RU(top)", R, U, -R, U, R, U * 2, -R, U)

    UR = SeqAlg("UR(top)", U, R, -U, -L, U, -R, -U, L)

    RD = SeqAlg("RD(top)", ((R.prime + D.prime + R + D) * 2 + U) * 3)

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
    def is_scramble(cls, alg: Alg):
        return isinstance(alg, _Scramble)

    @classmethod
    def alg(cls, name, *algs: Alg) -> Alg:
        return SeqAlg(name, *algs)

    @classmethod
    def simplify(cls, *algs: Alg) -> Alg:
        return cls.alg(None, *algs).simplify()

    @classmethod
    def count(cls, *algs: Alg) -> int:
        return cls.alg(None, *algs).count()

    @classmethod
    def of_face(cls, face: FaceName) -> FaceAlg:

        match face:

            case FaceName.F:
                return cls.F

            case FaceName.B:
                return cls.B

            case FaceName.L:
                return cls.L

            case FaceName.R:
                return cls.R

            case FaceName.U:
                return cls.U

            case FaceName.D:
                return cls.D

            case _:
                raise InternalSWError(f"Unknown face name {face}")

    @classmethod
    def of_slice(cls, slice_name: SliceName) -> SliceAbleAlg:

        match slice_name:

            case SliceName.E:
                return cls.E

            case SliceName.S:
                return cls.S

            case SliceName.M:
                return cls.M

            case _:
                raise InternalSWError(f"Unknown slice name {slice_name}")

    @classmethod
    def no_op(cls) -> Alg:
        return Algs._NO_OP

    @classmethod
    def parse(cls, alg: str) -> Alg:
        return parse_alg(alg)


def _test_prime_prime():
    a = Algs.F.prime.prime
    ap = a.simplify()
    print(f"{a} {ap=}")


if __name__ == '__main__':
    # alg = Algs.alg(None, _R(), (_R().prime * 2 + Algs.R * 2))
    # print(alg)
    # print(alg.simplify())
    #
    # alg = Algs.R + Algs.U + Algs.U + Algs.U + Algs.U
    # _a = alg.simplify()
    # print(_a.__str__())
    # print(alg.simplify())

    _test_prime_prime()

    # m = Algs.M[2:3] * 2
    # print(m)
    # print(m.prime)
    # flatten = m.flatten()
    # print(flatten)
