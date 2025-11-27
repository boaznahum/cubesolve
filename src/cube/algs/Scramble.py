from random import Random
from typing import Any

from cube.algs.Inv import _Inv
from cube.algs.Mul import _Mul
from cube.algs.SimpleAlg import SimpleAlg
from cube.algs.Alg import Alg
from cube.algs.FaceAlg import FaceAlg
from cube.algs.SeqAlg import SeqAlg
from cube.algs.SliceAbleAlg import SliceAbleAlg


class _Scramble(SeqAlg):

    def __init__(self, name: str | None, *algs: Alg) -> None:
        super().__init__(name, *algs)

    def count(self) -> int:
        return 0


_PROB_SLICE_AN_ALG = 1.0 / 3.0
_PROB_SEQ = 1.0 / 2.0
_PROB_INV = 1.0 / 5.0
_PROB_MUL = 1.0 / 5.0
_SEQ_LEN = 30


def _count(a: Alg) -> int:
    if isinstance(a, SimpleAlg):
        return 1
    elif isinstance(a, _Inv):
        return _count(a._alg)
    elif isinstance(a, SeqAlg):
        return sum(_count(x) for x in a.algs)
    elif isinstance(a, _Mul):
        return _count(a._alg) * a._n
    else:
        raise RuntimeError(f"Unknown Alg {type(a)}")


def _scramble(cube_size: int, seed: Any, n: int | None = None) -> SeqAlg:
    """

    :param cube_size:
    :param seed: if not None, it is used as seed for random generator, and it is repeatable
    :param n:
    :return:
    """

    rnd: Random = Random(seed)
    if not n:
        n = rnd.randint(400, 800)

    algs = __scramble(cube_size, rnd, n, 3)

    name: str
    if seed:
        name = f"scrmbl{seed}/{n}"
    else:
        # noinspection SpellCheckingInspection
        name = f"random-scrm{n}"

    a = _Scramble(name + "[" + str(n) + "]", *algs)

    # print(f"Scramble: {name} {n} moves {_count(a)}")
    # print(SeqAlg(None, *algs))
    #
    # s = str(SeqAlg(None, *algs))
    # print(s)
    # if "]''" in s:
    #     assert False, "Found ]'' in scramble"

    return a


def __scramble(cube_size: int, rnd: Random, n: int, nest) -> list[Alg]:
    def prob(p: float) -> bool:
        return rnd.random() < p

    # n = rnd.randint(5, 6)

    from cube.algs.Algs import Algs
    s = Algs.Simple

    algs: list[Alg] = []

    k = n
    while k > 0:

        is_simple = False
        a: Alg

        if prob(_PROB_SEQ) and nest > 0:
            seq_len = rnd.randint(1, min(k, _SEQ_LEN))
            _algs = __scramble(cube_size, rnd, seq_len, nest - 1)

            #Not scramble, but SeqAlg, we want it to be printed
            a = SeqAlg(None, *_algs)

            k -= seq_len

        else:

            a = rnd.choice(s)
            k -= 1
            is_simple = True

            if isinstance(a, SliceAbleAlg) and prob(_PROB_SLICE_AN_ALG):

                if isinstance(a, FaceAlg):
                    max_slice = cube_size - 1  # see :class:`FaceAlg`
                elif isinstance(a, SliceAbleAlg):
                    max_slice = cube_size - 2  # see :class:`SliceAlg`
                else:
                    raise RuntimeError("Unknown SliceAbleAlg")

                slice_start = rnd.randint(1, max_slice)
                if slice_start == max_slice:
                    slice_stop = slice_start
                else:
                    left = max_slice - slice_start

                    if left == 0 or rnd.random() > 0.5:
                        slice_stop = slice_start
                    else:
                        slice_stop = rnd.randint(1, left) + slice_start

                a = a[slice_start:slice_stop]

        if prob(_PROB_INV):
            a = a.inv()

        if prob(_PROB_MUL):

            max = 3 if is_simple else 4  # for simple * 4 = 4, so we get []
            mul = rnd.randint(2, max)
            a_count = _count(a)
            # we can add up to k
            while mul > 1 and (a_count * (mul - 1)) > k:
                mul -= 1

            if (mul > 1):
                a = a * mul
                k -= a_count * (mul - 1)

        algs.append(a)

    return algs
