from cube.algs import Algs
from cube.app.abstract_ap import AbstractApp
from cube.model.cube_queries2 import CubeQueries2


def main() -> None:


    n = 8

    app = AbstractApp.create_non_default(n)

    cube = app.cube

    alg = Algs.scramble(cube.size, 4)

    alg.play(cube)

    state = CubeQueries2(cube).get_sate()

    slices=[1, 2,  5, 6]
    slice_alg = Algs.M[slices]

    slice_alg.play(cube)
    slice_alg.prime.play(cube)

    assert cube.cqr.compare_state(state)


if __name__ == '__main__':
    main()