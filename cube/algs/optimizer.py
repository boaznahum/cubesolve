from collections.abc import MutableSequence, Iterator
from typing import Sequence

# todo: understand why mypy and pyright don't like this import
#from cube.algs  import Alg
from cube.algs.Alg import Alg
from cube.algs.SimpleAlg import SimpleAlg
from cube.algs.SeqAlg import SeqSimpleAlg


def simplify(self: Alg) -> SeqSimpleAlg:
    from cube.algs.SimpleAlg import SimpleAlg
    from cube.algs.SeqAlg import SeqSimpleAlg
    flat_algs: MutableSequence[SimpleAlg] = []

    algs: Iterator[SimpleAlg] = self.flatten()

    for a in algs:
        flat_algs.append(a)

    combined = _combine(flat_algs)
    return SeqSimpleAlg(None, *combined)


def _combine(algs: Sequence[SimpleAlg]) -> Sequence[SimpleAlg]:

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
