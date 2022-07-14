import sys
import traceback
from typing import Any

from cube import config
from cube.algs import Algs
from cube.app_state import ApplicationAndViewState
from cube.model.cube import Cube
from cube.operator.cube_operator import Operator
from cube.solver import Solver, Solvers


def _scramble(op: Operator, _scramble_key: Any, _n=None):
    op.reset()

    _alg = Algs.scramble(op.cube.size, _scramble_key, _n)

    print(f"Running scramble, key={_scramble_key}, n={_n}, alg={_alg}")

    op.play(_alg, False)


def _run_test(op: Operator,
              slv: Solver,
              scramble_key,
              n, debug: bool,
              animation):
    # noinspection PyBroadException

    op.reset()  # also reset cube
    _scramble(op, scramble_key, n)

    try:
        slv.solve(animation=animation, debug=debug)
        # we ask solver, because in develop phase it wants to check what was implemented
        assert slv.is_solved

    except Exception:
        print()
        print(f"Failure on scramble key={scramble_key}, n={n} ")
        print("Alt T to repeat it, Ctrl T to repeat scramble")

        traceback.print_exc(file=sys.stdout)
        raise


def main():
    size = config.CUBE_SIZE

    cube = Cube(size=size)

    vs = ApplicationAndViewState()

    op: Operator = Operator(cube, vs)
    solver: Solver = Solvers.default(op)

    nn = config.AGGRESSIVE_TEST_NUMBER_OF_SCRAMBLE_ITERATIONS
    ll = 0
    count = 0
    n_loops = 0
    idx = 0
    for s in range(config.AGGRESSIVE_TEST_NUMBER_OF_SCRAMBLE_START,
                   config.AGGRESSIVE_TEST_NUMBER_OF_SCRAMBLE_START + nn):

        if s == -1:
            scramble_key = -1
            n = 5
        else:
            scramble_key = s
            n = None

        idx += 1

        print(str(idx) + f"/{nn} {scramble_key=}, {n=} ", end='')

        ll += 1
        if ll > 5:
            print()
            ll = 0

        n_loops += 1
        c0 = op.count
        _run_test(op, solver, scramble_key, n, False, False)
        count += op.count - c0

    print()
    print(f"Count={count}, average={count / n_loops}")


if __name__ == '__main__':
    main()
