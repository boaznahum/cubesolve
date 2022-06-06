import algs
import config
from algs import Algs
from cube import Cube
from cube_queries import CubeQueries


def test1():
    # Faild on [5:5]B
    # [{good} [3:3]R [3:4]D S [2:2]L]

    cube = Cube(6)

    alg = Algs.R[3:3] + Algs.D[3:4] + Algs.S + Algs.L[2:2]
    print(alg)
    alg.play(cube)

    alg = Algs.B[5:5]
    print(alg)
    alg.play(cube)


def test2():
    # Faild on [5:5]B
    # [{good} [3:3]R [3:4]D S [2:2]L]

    cube = Cube(7)

    alg = Algs.R[3:3]
    print(alg)
    alg.play(cube)


def __test_simplify(alg, n):

    config.CHECK_CUBE_SANITY = False

    cube = Cube(n)
    scramble=Algs.scramble(cube.size, "1")
    # alg = Algs.scramble("1")
    print("Alg=", alg)
    scramble.play(cube)
    alg.play(cube)
    s1 = CubeQueries.get_sate(cube)
    alg_s = alg.simplify()
#    flattern = algs._BigAlg(None, *alg_s)
#    flattern = algs._BigAlg(None, *alg_s)
    flattern = alg_s
    print("simplify=", alg_s)


    cube.reset()
    scramble.play(cube)
    flattern.play(cube)


    assert CubeQueries.compare_state(cube, s1)
    print("Passed")
    print("================================")

def __test_flattern(alg, n):

    config.CHECK_CUBE_SANITY = False

    cube = Cube(n)
    scramble=Algs.scramble(cube.size, "1")
    # alg = Algs.scramble("1")
    print("Alg=", alg)
    scramble.play(cube)
    alg.play(cube)
    s1 = CubeQueries.get_sate(cube)
    alg_s = alg.flatten()
    flattern = algs._BigAlg(None, *alg_s)
#    flattern = alg_s
    print("simplify=", alg_s)


    cube.reset()
    scramble.play(cube)
    flattern.play(cube)


    assert CubeQueries.compare_state(cube, s1)
    print("Passed")
    print("================================")


def test_flattern():
    # Faild on [5:5]B
    # [{good} [3:3]R [3:4]D S [2:2]L]

    # cube_size = 5
    # alg = Algs.R
    #
    # __test_flattern(alg, cube_size)
    #

    #===============================
    #
    cube_size = 5
    alg = Algs.M[2:2].prime*2
    __test_simplify(alg, cube_size)


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
    __test_simplify(algs._BigAlg(None, *_algs), cube_size)
    __test_simplify(algs._BigAlg(None, *_algs).inv(), cube_size)
    #
    # a = Algs.B[1:cube.n_slices + 1]
    # __test_flattern(a, cube_size)

    a = Algs.scramble(cube_size, "aaa")
    __test_simplify(a, cube_size)

    a = Algs.R[1:2] + Algs.R[2:3]
    __test_simplify(a, cube_size)

    a = Algs.R[1:2] + Algs.R[1:2]
    __test_simplify(a, cube_size)

if __name__ == '__main__':
    test_flattern()
