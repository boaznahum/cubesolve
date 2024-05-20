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
    # n = rnd.randint(5, 6)

    from cube.algs.Algs import Algs
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
