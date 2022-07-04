from cube.algs import Algs
from cube.model.cube import Cube
from cube.operator.cube_operator import Operator
from cube.model.cube_queries import CubeQueries
from cube.solver import Solver


def main():


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

    assert CubeQueries.compare_state(cube, state)


if __name__ == '__main__':
    main()