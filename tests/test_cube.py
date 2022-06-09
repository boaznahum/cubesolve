from algs.algs import Algs
from model.cube import Cube
from cube_operator import Operator
from solver import Solver


def main():


    n = 8

    cube = Cube(size=n)

    op: Operator = Operator(cube)
    solver: Solver = Solver(op)

    alg1 = Algs.scramble(cube.size, 4)
    alg2 = Algs.scramble(cube.size, 4)

    s1 = alg1.implify()

    alg2.play(cube)

    rs = solver.solve()

    assert cube.solved

    print("** corner swap:", rs.was_corner_swap)
    print("** even edge parity:", rs.was_even_edge_parity)
    print("** partial edge parity:", rs.was_partial_edge_parity)
    print("** count:", op.count)


if __name__ == '__main__':
    main()