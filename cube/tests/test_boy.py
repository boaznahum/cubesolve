from cube import algs
from cube.app.abstract_ap import AbstractApp
from cube.model.cube import Cube


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


if __name__ == '__main__':
    test1()
    test2()
