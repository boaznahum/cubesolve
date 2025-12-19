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
    assert "Cage:Pending" in status  # Cage (edges+corners) pending
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

    solver = CageNxNSolver(app.op)
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

    solver = CageNxNSolver(app.op)

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


# =============================================================================
# EVEN CUBE EDGE TESTS - Testing NxNEdges on 4x4, 6x6
# =============================================================================
# NxNEdges already supports even cubes (uses majority color instead of middle slice).
# These tests verify edge solving works correctly before we implement corner support.


@pytest.mark.parametrize("size", [4, 6])
def test_cage_even_cube_edges_status_pending(size: int) -> None:
    """Test that edges show as pending on scrambled even cubes."""
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    solver = CageNxNSolver(app.op)

    # Verify edges are not solved
    assert not solver._are_edges_solved(), f"Edges should not be solved after scramble on {size}x{size}"

    # Status should show pending
    status = solver.status
    assert "Cage:Pending" in status, f"Expected 'Cage:Pending' in status, got '{status}'"

    print(f"\n  {size}x{size}: status before edge solve = '{status}'")


@pytest.mark.parametrize("size", [4, 6])
def test_cage_even_cube_edges_status_after_solve(size: int) -> None:
    """Test that edges show as solved after edge solving on even cubes."""
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    solver = CageNxNSolver(app.op)

    # Solve edges only
    solver._nxn_edges.solve()

    # Verify edges are now solved
    assert solver._are_edges_solved(), f"Edges should be solved after edge solve on {size}x{size}"

    # Status should show Cage:Edges (edges done, corners pending)
    status = solver.status
    assert "Cage:Edges" in status, f"Expected 'Cage:Edges' in status, got '{status}'"

    print(f"\n  {size}x{size}: status after edge solve = '{status}'")


@pytest.mark.parametrize("size", [4, 6])
def test_cage_even_cube_edges_solve(size: int) -> None:
    """Test that NxNEdges can solve edges on even cubes (4x4, 6x6).

    NxNEdges handles even cubes by:
    - Using majority color on edge (not middle slice which doesn't exist)
    - Detecting partial parity (1 edge left after solving 11)
    - Fixing parity with M-slice algorithm

    This test verifies edges are correctly paired on even cubes.
    """
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    # Verify edges are not solved after scramble
    edges_solved_before = all(e.is3x3 for e in app.cube.edges)
    assert not edges_solved_before, f"Edges should not be solved after scramble on {size}x{size}"

    # Create CageNxNSolver and use its internal NxNEdges
    # (CageNxNSolver can be created for even cubes, only full solve() fails)
    solver = CageNxNSolver(app.op)

    # Solve edges only (via internal NxNEdges)
    had_parity = solver._nxn_edges.solve()

    # Verify ALL edges are now paired (is3x3 = True)
    for edge in app.cube.edges:
        assert edge.is3x3, f"Edge {edge} should be paired after solve on {size}x{size}"

    print(f"\n  {size}x{size}: edges solved, parity={'YES' if had_parity else 'no'}")


@pytest.mark.parametrize("size,seed", [
    (4, 0), (4, 1), (4, 2), (4, 3), (4, 4),
    (6, 0), (6, 1), (6, 2),
])
def test_cage_even_cube_edges_multiple_seeds(size: int, seed: int) -> None:
    """Test edge solving on even cubes with multiple scramble seeds.

    Even cubes can have "partial" parity (detectable during pairing) and
    "full" parity (all slices flipped same way - only detectable during L3).
    This test covers partial parity handling in NxNEdges.
    """
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    # Scramble with specific seed
    app.scramble(seed, None, animation=False, verbose=False)

    # Create CageNxNSolver and use its internal NxNEdges
    solver = CageNxNSolver(app.op)

    # Solve edges only
    had_parity = solver._nxn_edges.solve()

    # Verify edges solved
    assert all(e.is3x3 for e in app.cube.edges), \
        f"All edges should be paired on {size}x{size} seed={seed}"

    parity_str = "PARITY" if had_parity else "no-parity"
    print(f"  {size}x{size} seed={seed}: {parity_str}")


# =============================================================================
# EVEN CUBE FULL SOLVE TESTS - Using virtual_face_colors for corners
# =============================================================================
# These tests verify the complete cage solver works on even cubes (4x4, 6x6)
# using the virtual face color mechanism for corner solving.


@pytest.mark.parametrize("size", [4, 6])
def test_cage_even_cube_full_solve(size: int) -> None:
    """Test that cage solver fully solves even cubes (4x4, 6x6).

    This is the key test for virtual_face_colors mechanism:
    1. Scramble the cube
    2. Solve edges (NxNEdges - already works for even cubes)
    3. Create FaceTrackers to establish face colors
    4. Use virtual_face_colors context to solve corners
    5. Solve centers (NxNCentersV3 - already works for even cubes)
    6. Verify cube is fully solved

    If this test passes, even cube support in cage solver is working.
    """
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    # Verify cube is scrambled
    assert not app.cube.solved, f"{size}x{size} should be scrambled"

    # Create solver and solve
    solver = CageNxNSolver(app.op)
    results = solver.solve()

    # Verify cube is fully solved
    assert app.cube.solved, f"{size}x{size} should be fully solved after cage solve"

    # Verify all components are in correct state
    assert solver._are_edges_solved(), f"{size}x{size} edges should be paired"
    assert solver._are_edges_positioned(), f"{size}x{size} edges should be positioned"
    assert solver._are_corners_solved(), f"{size}x{size} corners should be solved"
    assert solver._are_centers_solved(), f"{size}x{size} centers should be solved"

    print(f"\n  {size}x{size}: FULLY SOLVED via cage method with virtual colors!")


@pytest.mark.parametrize("size,seed", [
    (4, 0), (4, 1), (4, 2), (4, 7), (4, 42),
    (6, 0), (6, 1), (6, 42),
])
def test_cage_even_cube_full_solve_multiple_seeds(size: int, seed: int) -> None:
    """Test even cube cage solver with multiple scramble seeds.

    This verifies the virtual_face_colors mechanism works across
    different scramble states, not just one lucky configuration.
    """
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    # Scramble with specific seed
    app.scramble(seed, None, animation=False, verbose=False)

    # Solve
    solver = CageNxNSolver(app.op)
    results = solver.solve()

    # Verify fully solved
    assert app.cube.solved, f"{size}x{size} seed={seed} should be solved"

    parity_str = "parity" if results._was_partial_edge_parity else "no-parity"
    print(f"  {size}x{size} seed={seed}: solved ({parity_str})")
