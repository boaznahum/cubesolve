"""Performance benchmark tests for cube solving."""
import pytest
import time

from cube.domain.algs import Algs
from cube.application.config_impl import AppConfig
from cube.application.state import ApplicationAndViewState
from cube.application.commands.Operator import Operator
from cube.domain.solver import Solver, Solvers
from cube.domain.solver.SolverName import SolverName
from cube.domain.model.Cube import Cube
from tests.test_utils import _test_sp


@pytest.mark.slow
@pytest.mark.benchmark
def test_solve_performance():
    """Benchmark cube solving performance."""
    n_loops = 3
    cube_size = 10

    # Check if the default solver supports this cube size
    config = AppConfig()
    solver_name = SolverName.lookup(config.default_solver)
    skip_reason = solver_name.meta.get_skip_reason(cube_size)
    if skip_reason:
        pytest.skip(f"Default solver {solver_name.display_name}: {skip_reason}")

    cube = Cube(cube_size, sp=_test_sp)
    vs = ApplicationAndViewState(config)
    op: Operator = Operator(cube, vs)
    slv: Solver = Solvers.default(op)

    count = 0
    n_executed_tests = 0

    start = time.time_ns()

    for s in range(-1, n_loops):
        op.reset()  # also reset cube

        if s == -1:
            scramble_key = -1
            n = 5
        else:
            scramble_key = s
            n = None

        alg = Algs.scramble(cube.size, scramble_key, n)
        op.op(alg, animation=False)

        c0 = op.count
        slv.solve(animation=False, debug=False)

        assert slv.is_solved, f"Failed on scramble key={scramble_key}, n={n}"

        count += op.count - c0
        n_executed_tests += 1

    period = (time.time_ns() - start) / 1e9

    # Print performance stats (visible with pytest -v -s)
    s = cube.size
    print(f"\nCube size={s}")
    print(f"Count={count}, average={count / n_executed_tests}")
    print(f"Time(s)={period:.3f}, average per solve={period / n_executed_tests:.3f}s")
