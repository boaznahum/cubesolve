import sys
import traceback
from collections.abc import Collection
from typing import Any

from cube.domain.algs import Algs
from cube.application.state import ApplicationAndViewState
from cube.domain.model.Cube import Cube
from cube.application.commands.Operator import Operator
from cube.domain.solver import Solver, Solvers
from cube.domain.solver.SolverName import SolverName


def run_solvers_sizes(solvers: Collection[SolverName], cube_sizes: Collection[int],
                      first_scramble_key: Any,
                      number_of_loops: int, debug: bool):
    for cube_size in cube_sizes:
        for SolverName in solvers:
            cube = Cube(cube_size)
            vs = ApplicationAndViewState()
            op: Operator = Operator(cube, vs)
            slv: Solver = Solvers.by_name(SolverName, op)

            run_tests(slv, first_scramble_key,
                                 number_of_loops,
                                 debug=debug)


def run_tests(solver: Solver,
              first_key: int,
              number_of_loops: int,
              debug=False):
    op: Operator = solver.op

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

        print(str(idx) + f"/{nn} solver={solver.name} cube size: {op.cube.size} "
                         f"scramble_key={scramble_key} {type(scramble_key)}, {n=} ")

        # ll += 1
        # if ll > 5:
        #     print()
        #     ll = 0

        n_loops += 1
        run_single_test(solver, scramble_key, n, debug, False,
                        verbose=False  # I will do the printing
                        )
        count += op.count

    print(f"**** Count={count}, average={count / n_loops}")
    print()


def run_single_test(solver: Solver,
                    scramble_key: Any,
                    scramble_size: int | None,
                    debug: bool,
                    animation: bool,
                    verbose=True):
    # noinspection PyBroadException

    slv = solver
    op: Operator = slv.op

    op.reset()  # cube and operator, history and count
    scramble(op, scramble_key, scramble_size, animation, verbose=verbose)

    try:
        slv.solve(animation=animation, debug=debug)
        # we ask solver, because in develop phase it wants to check what was implemented
        assert slv.is_solved

    except Exception:
        print()
        print(
            f"Failure on scramble cube_size={op.cube.size} key={scramble_key}, {type(scramble_key)=}, n={scramble_size} ")
        print("Alt T to repeat it, Ctrl T to repeat scramble")

        traceback.print_exc(file=sys.stdout)
        raise


def scramble(op: Operator,
             scramble_key: Any,
             scramble_size: Any,
             animation: bool,
             verbose=True):
    op.reset()  # cube and history

    alg = Algs.scramble(op.cube.size, scramble_key, scramble_size)

    if verbose:
        print(
            f"Running scramble, cube size={op.cube.size} key={scramble_key}, {type(scramble_key)=}, n={scramble_size}, alg={alg}")

    op.play(alg, False, animation=animation)

    op.app_state.set_last_scramble_test(scramble_key, scramble_size)

    return alg
