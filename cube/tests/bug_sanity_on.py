from typing import Iterable

from cube import config, algs as algs
from cube.algs import Algs, Alg
from cube.model.cube import Cube
from cube.tests.test_utils import Tests


def test1():

    config.CHECK_CUBE_SANITY = True

    cube = Cube(3)

    alg = Algs.U
    print(alg)
    alg.play(cube)


tests: Tests = [  test1 ]


if __name__ == '__main__':
    test1()
