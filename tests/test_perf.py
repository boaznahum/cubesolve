import traceback

from algs import Algs
from cube_operator import Operator
from solver import Solver


def main():

    n_loops = 20

    ll = 0 # n plots per line
    count = 0
    n_executed_tests = 0

    from model.cube import Cube

    cube = Cube(5)
    op: Operator = Operator(cube)
    slv: Solver = Solver(op)

    for s in range(-1, n_loops):
        print(str(s + 2) + f"/{n_loops + 1}, ", end='')
        ll += 1
        if ll > 15:
            print()
            ll = 0

        op.reset()  # also reset cube
        if s == -1:
            scramble_key = -1
            n = 5
        else:
            scramble_key = s
            n = None

        alg = Algs.scramble(cube.size, scramble_key, n)

        op.op(alg, animation=False)

        # noinspection PyBroadException
        try:
            c0 = op.count
            slv.solve(animation=False, debug=False)
            assert slv.is_solved
            count += op.count - c0
            n_executed_tests += 1

        except Exception:
            print(f"Failure on scramble key={scramble_key}, n={n} ")
            traceback.print_exc()
            raise
    print()
    print(f"Count={count}, average={count / n_executed_tests}")


if __name__ == '__main__':
    main()