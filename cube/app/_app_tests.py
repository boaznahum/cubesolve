import sys
import traceback
from typing import Any

from cube.algs import Algs
from cube.app.abstract_ap import AbstractApp
from cube.operator.cube_operator import Operator


def _scramble(op: Operator,
              scramble_key: Any,
              scramble_size: Any,
              animation: bool,
                verbose=True
              ):
    op.reset()

    _alg = Algs.scramble(op.cube.size, scramble_key, scramble_size)

    if verbose:
        print(f"Running scramble, cube size={op.cube.size} key={scramble_key}, n={scramble_size}, alg={_alg}")

    op.play(_alg, False, animation=animation)


def run_single_test(app: AbstractApp,
                    scramble_key,
                    scramble_size: int | None,
                    debug: bool,
                    animation: bool,
                    verbose=True):
    # noinspection PyBroadException

    slv = app.slv
    op: Operator = app.op

    op.reset()  # also reset cube
    _scramble(op, scramble_key, scramble_size, animation, verbose=verbose)

    try:
        slv.solve(animation=animation, debug=debug)
        # we ask solver, because in develop phase it wants to check what was implemented
        assert slv.is_solved

    except Exception:
        print()
        print(f"Failure on scramble cube_size={op.cube.size} key={scramble_key}, n={scramble_size} ")
        print("Alt T to repeat it, Ctrl T to repeat scramble")

        traceback.print_exc(file=sys.stdout)
        raise


def run_tests(app: AbstractApp,
              first_key: int,
              number_of_loops: int):
    op: Operator = app.op

    nn = number_of_loops
    # ll = 0
    count = 0
    n_loops = 0
    idx = 0
    for s in range(first_key,
                   first_key + nn):

        if s == -1:
            scramble_key = -1
            n = 5
        else:
            scramble_key = s
            n = None

        idx += 1

        print(str(idx) + f"/{nn} solver={app.slv.name} cube size: {op.cube.size} scramble_key={scramble_key}, {n=} ")

        # ll += 1
        # if ll > 5:
        #     print()
        #     ll = 0

        n_loops += 1
        c0 = op.count
        run_single_test(app, scramble_key, n, False, False,
                        verbose=False  # I will do the printing
                        )
        count += op.count - c0

    print()
    print(f"Count={count}, average={count / n_loops}")
