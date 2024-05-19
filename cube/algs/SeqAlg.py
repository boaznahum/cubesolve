import functools
import typing
from collections.abc import MutableSequence, Iterator, Sequence

from cube.algs.Alg import Alg
from cube.model import Cube

if typing.TYPE_CHECKING:
    from cube.algs.SimpleAlg import SimpleAlg, NSimpleAlg


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

    def atomic_str(self) -> str:
        if self._name:
            return "{" + self._name + "}"
        else:
            if len(self._algs) == 1:
                return self._algs[0].atomic_str()
            else:
                return "[" + " ".join([str(a) for a in self._algs]) + "]"

    def simplify(self) -> "SeqSimpleAlg":

        from cube.algs.SimpleAlg import SimpleAlg
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

    def inv_and_flatten(self) -> Iterator["SimpleAlg"]:
        algs = [a.inv() for a in reversed(self.algs)]
        yield from SeqAlg(None, *algs).flatten()

    @staticmethod
    def _combine(algs: Sequence["SimpleAlg"]) -> Sequence["SimpleAlg"]:

        from cube.algs.SimpleAlg import NSimpleAlg, SimpleAlg

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

    @classmethod
    def empty(cls) -> "SeqAlg":
        return SeqAlg(None)


class SeqSimpleAlg(SeqAlg):
    """
    A big alg composed of SimpleAlg s only
    """

    def __init__(self, name: str | None, *algs: "SimpleAlg") -> None:
        super().__init__(name, *algs)

    @property
    def algs(self) -> Sequence["SimpleAlg"]:
        return super().algs  # type: ignore
