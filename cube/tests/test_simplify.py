from typing import Iterable, Any

from cube import config, algs as algs
from cube.algs import Algs, Alg
from cube.model.cube import Cube
from cube.tests import test_utils
from cube.tests.test_utils import Tests, Test




def _compare_two_algs(cube_size: int, algs1: Iterable[Alg], algs2: Iterable[Alg]):
    cube = Cube(cube_size)

    for alg in algs1:
        alg.play(cube)

    s1 = cube.cqr.get_sate()

    cube.reset()
    for alg in algs2:
        alg.play(cube)

    s2 = cube.cqr.get_sate()

    # print(f"{s1=}")
    # print(f"{s2=}")

    assert cube.cqr.compare_states(s1, s2)


def _compare_inv(cube_size: int, algs: Iterable[Alg]):
    cube = Cube(cube_size)

    scramble = Algs.scramble(cube_size)

    scramble.play(cube)

    s1 = cube.cqr.get_sate()

    for alg in algs:
        alg.play(cube)

    inv = Algs.seq_alg(None, *algs).inv()

    inv.play(cube)

    # should return to same state

    assert cube.cqr.compare_state(s1)


def __test_simplify(alg, cube_size):
    """
    Check play alg then random sequence
    Then compare it to alg + random simplified
    """

    cube = Cube(cube_size)
    scramble = Algs.no_op() # .empty #Algs.scramble(cube.size, "1")
    # alg = Algs.scramble("1")

    simplified = alg.simplify()

    print("Alg=     ", [*alg.flatten()])
    print("simplify=", [*simplified.flatten()])
    #
    # print("Alg=     ", [*alg.algs])
    # print("simplify=", [*simplified.algs])

    _compare_two_algs(cube_size, (scramble, alg), (scramble, simplified))

    print("Simplify passed")
    print("================================")

    _compare_inv(cube_size, (scramble, alg))

    print("Inv passed")
    print("================================")


def __test_simplify_n(cube_size, seq_length: int | None, sanity_check: bool | None, seed: Any = None):
    """

    :param cube_size:
    :param seq_length:
    :param sanity_check: if none that :attr:`config.CHECK_CUBE_SANITY` will not modified
    :return:
    """
    if sanity_check is not None:
        config.CHECK_CUBE_SANITY = sanity_check
    alg = Algs.scramble(cube_size, seq_length=seq_length, seed=seed)
    __test_simplify(alg, cube_size)


def test_simplify1():
    cube_size = 8
    seq_length = None
    sanity_check = False

    __test_simplify_n(cube_size, seq_length, sanity_check)

def test_simplify2():
    cube_size = 8
    seq_length = None
    sanity_check = False

    alg = (Algs.R * 2).inv()

    __test_simplify(alg, cube_size)

    __test_flatten(alg, cube_size)


def __test_flatten(alg, cube_size):
    config.CHECK_CUBE_SANITY = False

    cube = Cube(cube_size)
    scramble = Algs.scramble(cube.size, "1")
    # alg = Algs.scramble("1")
    print("Alg=", [*alg.flatten()])
    scramble.play(cube)
    alg.play(cube)
    s1 = cube.cqr.get_sate()
    alg_s = alg.flatten()
    flat = algs.SeqAlg(None, *alg_s)
    #    flat = alg_s
    print("flatten=", [*flat.flatten()])

    cube.reset()
    scramble.play(cube)
    flat.play(cube)

    assert cube.cqr.compare_state(s1)
    print("Passed")
    print("================================")

def _test_simplify_flatten(alg, cube_size):
    __test_simplify(alg, cube_size)
    __test_flatten(alg, cube_size)


def test_flattern():
    # Faild on [5:5]B
    # [{good} [3:3]R [3:4]D S [2:2]L]

    # cube_size = 5
    # alg = Algs.R
    #
    # __test_flattern(alg, cube_size)
    #

    # ===============================
    #
    cube_size = 5
    alg = Algs.M[2:2].prime * 2
    __test_flatten(alg, cube_size)

    # #---------------------------------
    cube_size = 7

    cube = Cube(cube_size)
    inv = cube.inv

    c = 2
    cc = 4

    rotate_on_cell = Algs.M[inv(c) + 1:inv(c) + 1]
    rotate_on_second = Algs.M[inv(cc) + 1:inv(cc) + 1]

    on_front_rotate = Algs.F.prime

    r1_mul = 2

    _algs = [rotate_on_cell.prime * r1_mul,
             on_front_rotate,
             rotate_on_second.prime * r1_mul,
             on_front_rotate.prime,
             rotate_on_cell * r1_mul,
             on_front_rotate,
             rotate_on_second * r1_mul,
             on_front_rotate.prime]
    #
    # for a in _algs:
    __test_flatten(algs.SeqAlg(None, *_algs), cube_size)
    __test_flatten(algs.SeqAlg(None, *_algs).inv(), cube_size)
    #
    # a = Algs.B[1:cube.n_slices + 1]
    # __test_flattern(a, cube_size)

    a = Algs.scramble(cube_size, "aaa")
    __test_flatten(a, cube_size)

    a = Algs.R[1:2] + Algs.R[2:3]
    __test_flatten(a, cube_size)

    a = Algs.R[1:2] + Algs.R[1:2]
    __test_flatten(a, cube_size)

def test1():
    # Faild on [5:5]B
    # [{good} [3:3]R [3:4]D S [2:2]L]

    cube = Cube(6)

    alg = Algs.R[3:3] + Algs.D[3:4] + Algs.S + Algs.L[2:2]

    _test_simplify_flatten(alg,cube.size)
    alg = Algs.B[5:5]
    _test_simplify_flatten(alg,cube.size)

    alg = Algs.R[3:3]
    _test_simplify_flatten(alg,cube.size)





tests: Tests = [
    test_simplify1,
    test_simplify2,
    test_flattern,
    test1

]

if __name__ == '__main__':
    test_utils.run_tests(tests)
    #__test_simplify_n(3, 100, True, seed=3)
