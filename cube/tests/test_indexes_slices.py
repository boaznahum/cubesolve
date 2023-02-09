from cube.algs import Algs
from cube.model.cube import Cube
from cube.operator.cube_operator import Operator
from cube.solver import Solver


def main() -> None:


    n = 8

    cube = Cube(size=n)

    op: Operator = Operator(cube)
    solver: Solver = Solver(op)

    alg = Algs.scramble(cube.size, 4)

    alg.play(cube)

    state = CubeQueries.get_sate(cube)

    slices=[1, 2,  5, 6]
    slice_alg = Algs.M[slices]

    slice_alg.play(cube)
    slice_alg.prime.play(cube)

    assert cube.cqr.compare_state(state)


if __name__ == '__main__':
    main()