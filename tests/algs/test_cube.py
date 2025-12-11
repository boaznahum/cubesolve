import pytest

from cube.domain.algs import Algs
from cube.application.AbstractApp import AbstractApp
from cube.application import _config as config


@pytest.fixture(autouse=True)
def reset_sanity_config():
    """Reset sanity config before each test to ensure clean state."""
    original = config.CHECK_CUBE_SANITY
    yield
    config.CHECK_CUBE_SANITY = original


@pytest.mark.parametrize("cube_size", [3, 5])
@pytest.mark.parametrize("sanity_check", [True, False])
def test_scramble_and_solve(cube_size: int, sanity_check: bool):
    """Test that a scrambled cube can be solved correctly."""
    config.CHECK_CUBE_SANITY = sanity_check

    app = AbstractApp.create_non_default(cube_size, animation=False)
    cube = app.cube

    alg = Algs.scramble(cube.size, 4)
    alg.play(cube)

    result = app.slv.solve()

    assert cube.solved, f"Cube of size {cube_size} should be solved"

    # Log solve details (visible with pytest -v)
    print(f"\nCube size: {cube_size}, Sanity: {sanity_check}")
    print(f"  corner swap: {result.was_corner_swap}")
    print(f"  even edge parity: {result.was_even_edge_parity}")
    print(f"  partial edge parity: {result.was_partial_edge_parity}")
    print(f"  move count: {app.op.count}")


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_scramble_by_seed_and_solve(seed: int):
    """
    Test scramble with specific seeds and solve - mirrors GUI test sequences.

    This test uses the same scramble seeds as the GUI tests to ensure
    the solver works correctly for these specific scramble patterns.

    Matches GUI test: Command.SCRAMBLE_1 + Command.SOLVE_ALL + Command.QUIT
    Which calls: app.scramble(seed, None, animation=False) then app.slv.solve()
    """
    app = AbstractApp.create_non_default(cube_size=3, animation=False)

    # Use app.scramble() same as GUI - this resets op and uses op.play()
    app.scramble(scramble_key=seed, scramble_size=None, animation=False, verbose=True)

    result = app.slv.solve(animation=False)

    assert app.cube.solved, f"Cube should be solved after scramble seed {seed}"

    print(f"\nScramble seed {seed} test:")
    print(f"  corner swap: {result.was_corner_swap}")
    print(f"  even edge parity: {result.was_even_edge_parity}")
    print(f"  partial edge parity: {result.was_partial_edge_parity}")
    print(f"  move count: {app.op.count}")


def test_m_rotation_and_solve_kociemba():
    """
    Test that a cube with M rotation can be solved by Kociemba solver.

    M is the middle layer rotation (between L and R).
    This tests the Kociemba solver's ability to handle slice moves.
    """
    from cube.domain.solver.SolverName import SolverName

    app = AbstractApp.create_non_default(cube_size=3, animation=False, solver=SolverName.KOCIEMBA)
    cube = app.cube

    # Apply M rotation
    Algs.M.play(cube)

    assert not cube.solved, "Cube should not be solved after M rotation"

    result = app.slv.solve(animation=False)

    assert cube.solved, "Cube should be solved after M rotation and solve"

    print(f"\nM rotation test (Kociemba):")
    print(f"  move count: {app.op.count}")


def test_compare_all_solvers_summary():
    """
    Compare move counts across all solvers and print a summary table.

    Tests all solvers with multiple scramble seeds and displays results
    in a formatted table for easy comparison.
    """
    from cube.domain.solver.SolverName import SolverName

    solvers = ["LBL", "CFOP", "KOCIEMBA"]
    seeds = [1, 2, 3]

    # Collect results: {solver: {seed: moves}}
    results: dict[str, dict[int, int]] = {s: {} for s in solvers}

    for solver_name in solvers:
        for seed in seeds:
            solver_enum = SolverName[solver_name]
            app = AbstractApp.create_non_default(cube_size=3, animation=False, solver=solver_enum)

            # Apply scramble
            app.scramble(scramble_key=seed, scramble_size=None, animation=False, verbose=False)
            scramble_moves = app.op.count

            # Solve
            app.slv.solve(animation=False)
            assert app.cube.solved, f"Cube should be solved by {solver_name}"

            # Record solve moves
            results[solver_name][seed] = app.op.count - scramble_moves

    # Print summary table
    print("\n")
    print("=" * 50)
    print("        SOLVER COMPARISON - MOVE COUNTS")
    print("=" * 50)
    print(f"{'Solver':<12} | {'Seed 1':>8} | {'Seed 2':>8} | {'Seed 3':>8} | {'Avg':>8}")
    print("-" * 50)

    for solver_name in solvers:
        moves = results[solver_name]
        avg = sum(moves.values()) / len(moves)
        print(f"{solver_name:<12} | {moves[1]:>8} | {moves[2]:>8} | {moves[3]:>8} | {avg:>8.1f}")

    print("=" * 50)
    print("Note: Kociemba is near-optimal (God's Number = 20)")
    print("=" * 50)
