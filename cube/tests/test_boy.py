from cube import algs
from cube.app.abstract_ap import AbstractApp
from cube.app.app_state import ApplicationAndViewState
from cube.model.cube import Cube
from cube.operator.cube_operator import Operator
from cube.solver import Solver


def test1() -> None:
    size = 7

    cube = Cube(size)

    a: algs.Alg = algs.Algs.scramble1(cube.size)

    a.play(cube)

    assert cube.is_boy


def test2() -> None:
    size = 4

    app = AbstractApp.create_non_default(size)

    cube = app.cube

    a: algs.Alg = algs.Algs.scramble1(cube.size)
    a.play(cube)

    app.slv.solve(animation=False)

    assert cube.is_boy


if __name__ == '__main__':
    test1()
    test2()
