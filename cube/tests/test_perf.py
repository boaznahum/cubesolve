import time
import traceback

from cube.algs import Algs
from cube.app.app_state import ApplicationAndViewState
from cube.operator.cube_operator import Operator
from cube.solver import Solver, Solvers


def main():
    n_loops = 3
    cube_size = 10

    ll = 0  # n plots per line
    count = 0
    n_executed_tests = 0

    from cube.model.cube import Cube

    cube = Cube(cube_size)
    vs = ApplicationAndViewState()
    op: Operator = Operator(cube, vs)
    slv: Solver = Solvers.default(op)

    start = time.time_ns()

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

    period = ( time.time_ns()- start ) / 1e9

    print()
    s = cube.size
    print(f"Cube size={s}")
    print(f"Count={count}, average={count / n_executed_tests} average={count / n_executed_tests / (s*s + 12*s)}")
    print(f"Time(s)={period}, average={period / n_executed_tests} average={period / n_executed_tests / (s*s + 12*s)}")


if __name__ == '__main__':
    main()
