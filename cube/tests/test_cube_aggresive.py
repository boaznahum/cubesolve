from math import ceil
from typing import Any, Collection

from cube import config
from cube.algs import Algs
from cube.app.abstract_ap import AbstractApp
from cube.app.app_state import ApplicationAndViewState
from cube.model import Cube
from cube.operator.cube_operator import Operator
from cube.solver import Solver, Solvers
from cube.solver.solver_name import SolverName
from cube.tests.test_utils import Tests
from cube.tests.tetser import TestRunner


def _scramble(op: Operator, _scramble_key: Any, _n=None):
    op.reset()

    _alg = Algs.scramble(op.cube.size, _scramble_key, _n)

    print(f"Running scramble, key={_scramble_key}, n={_n}, alg={_alg}")

    op.play(_alg, False)


def test1():
    app = AbstractApp.create_non_default(config.CUBE_SIZE, animation=False)
    debug = False
    sizes = config.AGGRESSIVE_TEST_NUMBER_SIZES
    for size in sizes:
        app.reset(cube_size=size)

        app.run_tests(config.AGGRESSIVE_TEST_NUMBER_OF_SCRAMBLE_START,
                      config.AGGRESSIVE_TEST_NUMBER_OF_SCRAMBLE_ITERATIONS // len(sizes),
                      debug=debug)


def test2() -> Any:
    sizes = config.AGGRESSIVE_2_TEST_NUMBER_SIZES
    debug = False
    first_scramble_key = config.AGGRESSIVE_2_TEST_NUMBER_OF_SCRAMBLE_START
    number_of_loops = ceil(config.AGGRESSIVE_2_TEST_NUMBER_OF_SCRAMBLE_ITERATIONS / len(SolverName))
    solvers: list[SolverName] = [*SolverName]

    TestRunner.run_solvers_sizes(solvers, sizes, first_scramble_key, number_of_loops, debug)




tests: Tests = [test2]


def main():
    #test1()
    test2()


if __name__ == '__main__':
    main()
