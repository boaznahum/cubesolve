from cube import algs
from cube.app.abstract_ap import AbstractApp
from cube.model.cube import Cube
from cube.tests.test_utils import Tests


def test1() -> None:
    size = 7

    cube = Cube(size)

    a: algs.Alg = algs.Algs.scramble1(cube.size)

    a.play(cube)

    assert cube.is_boy


def test2() -> None:
    size = 4

    app = AbstractApp.create_non_default(size, animation=False)

    cube = app.cube

    a: algs.Alg = algs.Algs.scramble1(cube.size)
    a.play(cube)

    app.slv.solve()

    assert cube.is_boy


tests: Tests = [test1, test2]

if __name__ == '__main__':
    test1()
    test2()
