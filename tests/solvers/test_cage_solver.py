"""Tests for CageNxNSolver - cage method (edges first, then corners, then centers)."""

import pytest
from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver


@pytest.mark.parametrize("size", [5, 7])
def test_cage_solver_status_on_solved_cube(size: int) -> None:
    """Test status reporting on a solved cube."""
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    solver = CageNxNSolver(app.op)

    # Solved cube should report "Solved"
    assert solver.status == "Solved"


@pytest.mark.parametrize("size", [5, 7])
def test_cage_solver_status_on_scrambled_cube(size: int) -> None:
    """Test status reporting on a scrambled cube."""
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    solver = CageNxNSolver(app.op)

    # After scramble, status should show pending phases
    status = solver.status
    assert "E:Pending" in status  # Edges pending
    assert "Ctr:Pending" in status  # Centers pending


@pytest.mark.parametrize("size", [5, 7])
def test_cage_solver_state_inspection(size: int) -> None:
    """Test stateless inspection methods."""
    app = AbstractApp.create_non_default(cube_size=size, animation=False)
    solver = CageNxNSolver(app.op)

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
    solver = CageNxNSolver(app.op)

    # 3x3 has no edge/center reduction needed - is3x3 is always True
    assert solver._are_edges_solved()
    assert solver._are_centers_solved()


@pytest.mark.parametrize("size", [5, 7])
def test_cage_solver_solves_edges(size: int) -> None:
    """Test that cage solver can solve edges on odd cubes."""
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    solver = CageNxNSolver(app.op)

    # Edges should not be solved before
    assert not solver._are_edges_solved(), "Edges should not be solved after scramble"

    # Solve
    results = solver.solve()

    # Edges should be solved after
    assert solver._are_edges_solved(), "Edges should be solved after solve()"

    # Status should show E:Done
    assert "E:Done" in solver.status

    # Print parity info for visibility
    print(f"\n  Size {size}x{size}: parity={results._was_partial_edge_parity}")


@pytest.mark.parametrize("seed", range(10))
def test_cage_solver_parity_detection(seed: int) -> None:
    """Test parity detection across multiple scrambles on 5x5."""
    app = AbstractApp.create_non_default(cube_size=5, animation=False)

    # Scramble with different seeds
    app.scramble(seed, None, animation=False, verbose=False)

    solver = CageNxNSolver(app.op)
    results = solver.solve()

    # Edges should be solved
    assert solver._are_edges_solved()

    # Print parity for each seed
    parity = "YES" if results._was_partial_edge_parity else "no"
    print(f"  seed={seed}: parity={parity}")
