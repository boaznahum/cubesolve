import sys
import traceback
from typing import Any

from cube.algs import Algs, Alg
from cube.app.AbstractApp import AbstractApp
from cube.operator.Operator import Operator


def scramble(app:AbstractApp,
             scramble_key: Any,
             scramble_size: Any,
             animation: Any,
             verbose=True
             ) -> Alg:

    op = app.op

    op.reset()

    alg = Algs.scramble(op.cube.size, scramble_key, scramble_size)

    if verbose:
        print(f"Running scramble, cube size={op.cube.size} key={scramble_key}, {type(scramble_key)=}, n={scramble_size}, alg={alg}")

    op.play(alg, False, animation=animation)

    app.vs.set_last_scramble_test(scramble_key, scramble_size)

    return alg


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
    scramble(app, scramble_key, scramble_size, animation, verbose=verbose)

    try:
        slv.solve(animation=animation, debug=debug)
        # we ask solver, because in develop phase it wants to check what was implemented
        assert slv.is_solved

    except Exception:
        print()
        print(f"Failure on scramble cube_size={op.cube.size} key={scramble_key}, {type(scramble_key)=}, n={scramble_size} ")
        print("Alt T to repeat it, Ctrl T to repeat scramble")

        traceback.print_exc(file=sys.stdout)
        raise


# todo: Replace with :class:`cube.tests.tetser.TestRunner.run_tests`
def run_tests(app: AbstractApp,
              first_key: int,
              number_of_loops: int,
              debug=False):
    op: Operator = app.op

    nn = number_of_loops
    # ll = 0
    count = 0
    n_loops = 0
    idx = 0
    for s in range(first_key,
                   first_key + nn + 1):

        if s == -1:
            scramble_key = -1
            n = 5
        else:
            scramble_key = s
            n = None

        idx += 1

        print(str(idx) + f"/{nn} solver={app.slv.name} cube size: {op.cube.size} "
                         f"scramble_key={scramble_key} {type(scramble_key)}, {n=} ")

        # ll += 1
        # if ll > 5:
        #     print()
        #     ll = 0

        n_loops += 1
        c0 = op.count
        app.reset()  # cube and operator
        run_single_test(app, scramble_key, n, debug, False,
                        verbose=False  # I will do the printing
                        )
        count += op.count - c0

    print()
    print(f"Count={count}, average={count / n_loops}")
