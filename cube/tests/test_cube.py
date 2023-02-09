from cube.algs import Algs
from cube.app.app_state import ApplicationAndViewState
from cube.model.cube import Cube
from cube.operator.cube_operator import Operator
from cube.solver import Solver


def main() -> None:

    n = 3

    cube = Cube(size=n)

    vs = ApplicationAndViewState()
    op: Operator = Operator(cube, vs)
    solver: Solver = Solver(op)

    alg2 = Algs.scramble(cube.size, 4)

    alg2.play(cube)

    rs = solver.solve()

    assert cube.solved

    print("** corner swap:", rs.was_corner_swap)
    print("** even edge parity:", rs.was_even_edge_parity)
    print("** partial edge parity:", rs.was_partial_edge_parity)
    print("** count:", op.count)


if __name__ == '__main__':
    main()
