from algs import algs
from app_state import ApplicationAndViewState
from model.cube import Cube
from cube_operator import Operator
from solver import Solver


def test1():
    size = 7

    cube = Cube(size)

    a: algs.Alg = algs.Algs.scramble1(cube.size)

    a.play(cube)

    assert cube.is_boy


def test2():
    size = 4

    cube = Cube(size)

    a: algs.Alg = algs.Algs.scramble1(cube.size)
    a.play(cube)

    vs = ApplicationAndViewState()
    op: Operator = Operator(cube, vs, False)
    slv: Solver = Solver(op)

    slv.solve()

    assert cube.is_boy


if __name__ == '__main__':
    test2()
