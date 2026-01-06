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
from cube.application import _config as config
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


@pytest.mark.benchmark
def test_alg_cache_performance():
    """
    Benchmark alg caching performance.

    Compares scramble generation with and without ALG_CACHE_ENABLED.
    """
    from cube.domain.algs.FaceAlg import FaceAlg
    from cube.domain.algs.SliceAlg import SliceAlg
    from cube.domain.algs.WholeCubeAlg import WholeCubeAlg

    n_scrambles = 50
    cube_size = 5

    def run_scramble_benchmark() -> float:
        """Run scramble generation with simplify/flatten and return time in seconds."""
        start = time.time_ns()
        for seed in range(n_scrambles):
            alg = Algs.scramble(cube_size, seed, 50)
            # simplify() and flatten() call with_n() which uses the cache
            _ = alg.simplify()
            _ = list(alg.flatten())
        return (time.time_ns() - start) / 1e9

    def clear_caches():
        """Clear all alg caches."""
        FaceAlg._instance_cache.clear()
        SliceAlg._instance_cache.clear()
        WholeCubeAlg._instance_cache.clear()

    # Save original setting
    original_setting = config.ALG_CACHE_ENABLED

    try:
        # Test with caching disabled
        config.ALG_CACHE_ENABLED = False
        clear_caches()
        time_no_cache = run_scramble_benchmark()

        # Test with caching enabled
        config.ALG_CACHE_ENABLED = True
        clear_caches()
        time_with_cache = run_scramble_benchmark()

        # Print results
        print(f"\n=== Alg Cache Benchmark ({n_scrambles} scrambles, size {cube_size}) ===")
        print(f"Without cache: {time_no_cache:.3f}s")
        print(f"With cache:    {time_with_cache:.3f}s")
        if time_with_cache > 0:
            speedup = time_no_cache / time_with_cache
            print(f"Speedup:       {speedup:.2f}x")

        # Cache stats
        print(f"\nCache sizes after benchmark:")
        print(f"  FaceAlg:      {len(FaceAlg._instance_cache)} entries")
        print(f"  SliceAlg:     {len(SliceAlg._instance_cache)} entries")
        print(f"  WholeCubeAlg: {len(WholeCubeAlg._instance_cache)} entries")

    finally:
        # Restore original setting
        config.ALG_CACHE_ENABLED = original_setting
