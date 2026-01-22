"""Tests for CageNxNSolver - cage method (edges first, then corners, then centers)."""

import pytest
from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver
from cube.domain.solver.Solvers import Solvers


def _cage(app: AbstractApp) -> CageNxNSolver:
    """Create CageNxNSolver through factory with correct type hint."""
    solver = Solvers.cage(app.op)
    assert isinstance(solver, CageNxNSolver)
    return solver


@pytest.mark.parametrize("size", [5, 7])
def test_cage_solver_status_on_solved_cube(size: int) -> None:
    """Test status reporting on a solved cube."""
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    solver = _cage(app)

    # Solved cube should report "Solved"
    assert solver.status == "Solved"


@pytest.mark.parametrize("size", [5, 7])
def test_cage_solver_status_on_scrambled_cube(size: int) -> None:
    """Test status reporting on a scrambled cube."""
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    solver = _cage(app)

    # After scramble, status should show pending phases
    status = solver.status
    assert "Cage:Pending" in status  # Cage (edges+corners) pending
    assert "Ctr:Pending" in status  # Centers pending


@pytest.mark.parametrize("size", [5, 7])
def test_cage_solver_state_inspection(size: int) -> None:
    """Test stateless inspection methods."""
    app = AbstractApp.create_non_default(cube_size=size, animation=False)
    solver = _cage(app)

    # On solved cube
    assert solver._are_edges_solved()
    assert solver._are_centers_solved()

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    # On scrambled cube, at least edges or centers should be unsolved
    edges_solved = solver._are_edges_solved()
    centers_solved = solver._are_centers_solved()
    # At least one should be False after scramble
    assert not (edges_solved and centers_solved)


@pytest.mark.parametrize("size", [3])
def test_cage_solver_on_3x3(size: int) -> None:
    """Test that 3x3 cube is trivially solved (no edges/centers to reduce)."""
    app = AbstractApp.create_non_default(cube_size=size, animation=False)
    solver = _cage(app)

    # 3x3 has no edge/center reduction needed - is3x3 is always True
    assert solver._are_edges_solved()
    assert solver._are_centers_solved()


@pytest.mark.parametrize("size", [5, 7])
def test_cage_solver_solves_edges(size: int) -> None:
    """Test that cage solver can solve edges on odd cubes."""
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    solver = _cage(app)

    # Edges should not be solved before
    assert not solver._are_edges_solved(), "Edges should not be solved after scramble"

    # Solve
    results = solver.solve()

    # Edges should be solved after
    assert solver._are_edges_solved(), "Edges should be solved after solve()"

    # Cube should be fully solved now (Phase 2 centers complete)
    assert solver.status == "Solved", f"Expected 'Solved', got '{solver.status}'"

    # Print parity info for visibility
    print(f"\n  Size {size}x{size}: parity={results._was_partial_edge_parity}")


@pytest.mark.parametrize("seed", range(10))
def test_cage_solver_parity_detection(seed: int) -> None:
    """Test parity detection across multiple scrambles on 5x5."""
    app = AbstractApp.create_non_default(cube_size=5, animation=False)

    # Scramble with different seeds
    app.scramble(seed, None, animation=False, verbose=False)

    solver = _cage(app)
    results = solver.solve()

    # Edges should be solved
    assert solver._are_edges_solved()

    # Print parity for each seed
    parity = "YES" if results._was_partial_edge_parity else "no"
    print(f"  seed={seed}: parity={parity}")


@pytest.mark.parametrize("size", [5, 7])
def test_cage_solver_solves_corners(size: int) -> None:
    """Test that cage solver solves corners and the entire cube.

    After solve():
    - Edges: paired AND positioned correctly
    - Corners: positioned correctly
    - Centers: SOLVED (Phase 2 complete)
    """
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    solver = _cage(app)

    # Before solve - corners and edges should be scrambled
    assert not solver._are_corners_solved(), "Corners should not be solved after scramble"

    # Solve
    solver.solve()

    # After solve - edges should be paired AND positioned
    assert solver._are_edges_solved(), "Edges should be paired"
    assert solver._are_edges_positioned(), "Edges should be positioned correctly"

    # Corners should be solved
    assert solver._are_corners_solved(), "Corners should be solved"

    # Centers should also be solved (Phase 2 complete)
    assert solver._are_centers_solved(), "Centers should be solved (Phase 2 complete)"

    # Cube should be fully solved
    assert app.cube.solved, "Cube should be fully solved"

    print(f"\n  Size {size}x{size}: fully solved")


# ===========================================================================
# Even cube tests (4x4, 6x6) - using shadow cube approach
# ===========================================================================

@pytest.mark.parametrize("size", [4, 6])
def test_cage_solver_even_cube_status(size: int) -> None:
    """Test status reporting on even cubes."""
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    solver = _cage(app)

    # Solved cube should report "Solved"
    assert solver.status == "Solved"
    assert app.cube.size % 2 == 0, f"Size {size} should be even"


@pytest.mark.parametrize("size", [4, 6])
def test_cage_solver_even_cube_solves(size: int) -> None:
    """Test that cage solver can solve even cubes using shadow cube approach."""
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    solver = _cage(app)

    # Solve
    solver.solve()

    # Cube should be fully solved
    assert app.cube.solved, f"Even cube {size}x{size} should be fully solved"
    print(f"\n  Even cube {size}x{size}: fully solved")


@pytest.mark.parametrize("seed", range(5))
def test_cage_solver_even_cube_multiple_scrambles(seed: int) -> None:
    """Test even cube solving with multiple scramble seeds."""
    app = AbstractApp.create_non_default(cube_size=4, animation=False)

    # Scramble with different seeds
    app.scramble(seed, None, animation=False, verbose=False)

    solver = _cage(app)
    solver.solve()

    # Cube should be solved
    assert app.cube.solved, f"4x4 should be solved with seed={seed}"
    print(f"  4x4 seed={seed}: solved")
