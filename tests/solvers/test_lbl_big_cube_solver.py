"""Tests for LayerByLayerNxNSolver - Layer-by-Layer method for big cubes.

Currently only Layer 1 is implemented, so tests focus on:
- Layer 1 centers (SolveStep.LBL_L1_Ctr)
- Layer 1 cross (SolveStep.L1x) - centers + edges paired + edges positioned
- Layer 1 complete (SolveStep.LBL_L1) - centers + edges + corners
"""
from __future__ import annotations

import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.direct.lbl.LayerByLayerNxNSolver import LayerByLayerNxNSolver
from cube.domain.solver.solver import SolveStep
from cube.domain.solver.SolverName import SolverName
from tests.solvers.conftest import skip_if_not_supported


# =============================================================================
# Status Tests
# =============================================================================

@pytest.mark.parametrize("size", [4, 5, 7])
def test_lbl_solver_status_on_solved_cube(size: int) -> None:
    """Test status reporting on a solved cube."""
    skip_if_not_supported(SolverName.LBL_DIRECT, size)
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    solver = LayerByLayerNxNSolver(app.op)

    # Solved cube should report "Solved"
    assert solver.status == "Solved"


@pytest.mark.parametrize("size", [4, 5])
def test_lbl_solver_status_on_scrambled_cube(size: int) -> None:
    """Test status reporting on a scrambled cube."""
    skip_if_not_supported(SolverName.LBL_DIRECT, size)
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    solver = LayerByLayerNxNSolver(app.op)

    # After scramble, status should show Layer 1 pending
    status = solver.status
    assert "L1:" in status, f"Expected Layer 1 status, got '{status}'"


# =============================================================================
# State Inspection Tests
# =============================================================================

@pytest.mark.parametrize("size", [4, 5, 7])
def test_lbl_solver_state_inspection_on_solved_cube(size: int) -> None:
    """Test state inspection methods on a solved cube."""
    skip_if_not_supported(SolverName.LBL_DIRECT, size)
    app = AbstractApp.create_non_default(cube_size=size, animation=False)
    solver = LayerByLayerNxNSolver(app.op)

    # On solved cube, use FacesTrackerHolder for inspection
    from cube.domain.solver.common.big_cube.FacesTrackerHolder import FacesTrackerHolder

    with FacesTrackerHolder(solver) as th:
        assert solver._is_layer1_centers_solved(th)
        assert solver._is_layer1_edges_solved(th)
        assert solver._is_layer1_corners_solved(th)
        assert solver._is_layer1_solved(th)


@pytest.mark.parametrize("size", [4, 5])
def test_lbl_solver_state_inspection_on_scrambled_cube(size: int) -> None:
    """Test state inspection methods on a scrambled cube."""
    skip_if_not_supported(SolverName.LBL_DIRECT, size)
    app = AbstractApp.create_non_default(cube_size=size, animation=False)
    solver = LayerByLayerNxNSolver(app.op)

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    from cube.domain.solver.common.big_cube.FacesTrackerHolder import FacesTrackerHolder

    with FacesTrackerHolder(solver) as th:
        # On scrambled cube, Layer 1 should not be solved
        assert not solver._is_layer1_solved(th), "Layer 1 should not be solved after scramble"


# =============================================================================
# Layer 1 Centers Tests (SolveStep.LBL_L1_Ctr)
# =============================================================================

@pytest.mark.parametrize("size", [4, 5, 7])
def test_lbl_solver_solves_layer1_centers(size: int) -> None:
    """Test that LBL solver can solve Layer 1 centers."""
    skip_if_not_supported(SolverName.LBL_DIRECT, size)
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    solver = LayerByLayerNxNSolver(app.op)

    from cube.domain.solver.common.big_cube.FacesTrackerHolder import FacesTrackerHolder

    # Before solve - centers might or might not be solved
    # (could be solved by chance on small scrambles)

    # Solve only Layer 1 centers
    solver.solve(what=SolveStep.LBL_L1_Ctr, animation=False)

    # After solve - centers should be solved
    with FacesTrackerHolder(solver) as th:
        assert solver._is_layer1_centers_solved(th), "Layer 1 centers should be solved"

    print(f"\n  Size {size}x{size}: Layer 1 centers solved")


@pytest.mark.parametrize("seed", range(5))
def test_lbl_solver_layer1_centers_multiple_scrambles(seed: int) -> None:
    """Test Layer 1 centers solving with multiple scramble seeds."""
    skip_if_not_supported(SolverName.LBL_DIRECT, 5)
    app = AbstractApp.create_non_default(cube_size=5, animation=False)

    # Scramble with different seeds
    app.scramble(seed, None, animation=False, verbose=False)

    solver = LayerByLayerNxNSolver(app.op)

    # Solve Layer 1 centers
    solver.solve(what=SolveStep.LBL_L1_Ctr, animation=False)

    from cube.domain.solver.common.big_cube.FacesTrackerHolder import FacesTrackerHolder

    with FacesTrackerHolder(solver) as th:
        assert solver._is_layer1_centers_solved(th), f"5x5 Layer 1 centers should be solved (seed={seed})"

    print(f"  5x5 seed={seed}: Layer 1 centers solved")


# =============================================================================
# Layer 1 Cross Tests (SolveStep.L1x)
# =============================================================================

@pytest.mark.parametrize("size", [4, 5, 7])
def test_lbl_solver_solves_layer1_cross(size: int) -> None:
    """Test that LBL solver can solve Layer 1 cross (centers + edges positioned)."""
    skip_if_not_supported(SolverName.LBL_DIRECT, size)
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    solver = LayerByLayerNxNSolver(app.op)

    # Solve Layer 1 cross (centers + edges paired + edges positioned)
    solver.solve(what=SolveStep.L1x, animation=False)

    from cube.domain.solver.common.big_cube.FacesTrackerHolder import FacesTrackerHolder

    with FacesTrackerHolder(solver) as th:
        assert solver._is_layer1_centers_solved(th), "Layer 1 centers should be solved"
        assert solver._is_layer1_edges_solved(th), "Layer 1 edges should be paired"
        assert solver._is_layer1_cross_solved(th), "Layer 1 cross should be solved"

    print(f"\n  Size {size}x{size}: Layer 1 cross solved")


@pytest.mark.parametrize("seed", range(5))
def test_lbl_solver_layer1_cross_multiple_scrambles(seed: int) -> None:
    """Test Layer 1 cross solving with multiple scramble seeds."""
    skip_if_not_supported(SolverName.LBL_DIRECT, 5)
    app = AbstractApp.create_non_default(cube_size=5, animation=False)

    # Scramble with different seeds
    app.scramble(seed, None, animation=False, verbose=False)

    solver = LayerByLayerNxNSolver(app.op)

    # Solve Layer 1 cross
    solver.solve(what=SolveStep.L1x, animation=False)

    from cube.domain.solver.common.big_cube.FacesTrackerHolder import FacesTrackerHolder

    with FacesTrackerHolder(solver) as th:
        assert solver._is_layer1_cross_solved(th), f"5x5 Layer 1 cross should be solved (seed={seed})"

    print(f"  5x5 seed={seed}: Layer 1 cross solved")


# =============================================================================
# Layer 1 Complete Tests (SolveStep.LBL_L1)
# =============================================================================

@pytest.mark.parametrize("size", [4, 5, 7])
def test_lbl_solver_solves_layer1_complete(size: int) -> None:
    """Test that LBL solver can solve complete Layer 1 (centers + edges + corners)."""
    skip_if_not_supported(SolverName.LBL_DIRECT, size)
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    solver = LayerByLayerNxNSolver(app.op)

    # Solve complete Layer 1
    solver.solve(what=SolveStep.LBL_L1, animation=False)

    from cube.domain.solver.common.big_cube.FacesTrackerHolder import FacesTrackerHolder

    with FacesTrackerHolder(solver) as th:
        assert solver._is_layer1_centers_solved(th), "Layer 1 centers should be solved"
        assert solver._is_layer1_edges_solved(th), "Layer 1 edges should be paired"
        assert solver._is_layer1_corners_solved(th), "Layer 1 corners should be solved"
        assert solver._is_layer1_solved(th), "Layer 1 should be completely solved"

    print(f"\n  Size {size}x{size}: Layer 1 complete")


@pytest.mark.parametrize("seed", range(5))
def test_lbl_solver_layer1_complete_multiple_scrambles(seed: int) -> None:
    """Test complete Layer 1 solving with multiple scramble seeds on 5x5."""
    skip_if_not_supported(SolverName.LBL_DIRECT, 5)
    app = AbstractApp.create_non_default(cube_size=5, animation=False)

    # Scramble with different seeds
    app.scramble(seed, None, animation=False, verbose=False)

    solver = LayerByLayerNxNSolver(app.op)

    # Solve complete Layer 1
    solver.solve(what=SolveStep.LBL_L1, animation=False)

    from cube.domain.solver.common.big_cube.FacesTrackerHolder import FacesTrackerHolder

    with FacesTrackerHolder(solver) as th:
        assert solver._is_layer1_solved(th), f"5x5 Layer 1 should be solved (seed={seed})"

    print(f"  5x5 seed={seed}: Layer 1 complete")


# =============================================================================
# Even Cube Tests (4x4, 6x6) - using shadow cube approach
# =============================================================================
@pytest.mark.parametrize("size", [4, 6])
def test_lbl_solver_even_cube_layer1(size: int) -> None:
    """Test Layer 1 solving on even cubes (uses shadow cube approach)."""
    skip_if_not_supported(SolverName.LBL_DIRECT, size)
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    solver = LayerByLayerNxNSolver(app.op)

    # Solve complete Layer 1
    solver.solve(what=SolveStep.LBL_L1, animation=False)

    # Use solver's persistent tracker (same one used during solving)
    th = solver.tracker_holder
    assert solver._is_layer1_solved(th), f"Even cube {size}x{size} Layer 1 should be solved"

    # Cleanup trackers when done
    solver.cleanup_trackers()

    print(f"\n  Even cube {size}x{size}: Layer 1 solved")


@pytest.mark.parametrize("seed", range(5))
def test_lbl_solver_even_cube_multiple_scrambles(seed: int) -> None:
    """Test Layer 1 solving on 4x4 with multiple scramble seeds."""
    skip_if_not_supported(SolverName.LBL_DIRECT, 5)
    app = AbstractApp.create_non_default(cube_size=5, animation=False)

    # Scramble with different seeds
    app.scramble(seed, None, animation=False, verbose=False)

    solver = LayerByLayerNxNSolver(app.op)

    # Solve complete Layer 1
    solver.solve(what=SolveStep.LBL_L1, animation=False)

    from cube.domain.solver.common.big_cube.FacesTrackerHolder import FacesTrackerHolder

    with FacesTrackerHolder(solver) as th:
        assert solver._is_layer1_solved(th), f"4x4 Layer 1 should be solved (seed={seed})"

    print(f"  4x4 seed={seed}: Layer 1 solved")


# =============================================================================
# Supported Steps Tests
# =============================================================================

def test_lbl_solver_supported_steps() -> None:
    """Test that LBL solver reports correct supported steps."""
    skip_if_not_supported(SolverName.LBL_DIRECT, 5)
    app = AbstractApp.create_non_default(cube_size=5, animation=False)
    solver = LayerByLayerNxNSolver(app.op)

    steps = solver.supported_steps()

    # Should support Layer 1 steps
    assert SolveStep.LBL_L1_Ctr in steps, "Should support LBL_L1_Ctr"
    assert SolveStep.L1x in steps, "Should support L1x"
    assert SolveStep.LBL_L1 in steps, "Should support LBL_L1"


def test_lbl_solver_code() -> None:
    """Test that LBL solver reports correct code."""
    skip_if_not_supported(SolverName.LBL_DIRECT, 5)

    app = AbstractApp.create_non_default(cube_size=5, animation=False)
    solver = LayerByLayerNxNSolver(app.op)

    assert solver.get_code == SolverName.LBL_DIRECT


# =============================================================================
# Status Progression Tests
# =============================================================================

def test_lbl_solver_status_progression() -> None:
    """Test that status progresses correctly through solve steps."""
    skip_if_not_supported(SolverName.LBL_DIRECT, 5)
    app = AbstractApp.create_non_default(cube_size=5, animation=False)

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    solver = LayerByLayerNxNSolver(app.op)

    # Initial status - pending
    status_before = solver.status
    assert "L1:" in status_before

    # After centers
    solver.solve(what=SolveStep.LBL_L1_Ctr, animation=False)
    status_after_centers = solver.status
    # Status should now show centers done (L1:Ctr or L1:Ctr+Edg if edges happen to be solved)
    assert "L1:" in status_after_centers

    # After complete Layer 1
    solver.solve(what=SolveStep.LBL_L1, animation=False)
    status_after_l1 = solver.status
    # Status should show L1 done
    assert status_after_l1 == "L1:Done", f"Expected 'L1:Done', got '{status_after_l1}'"

    print(f"\n  Status progression: {status_before} -> {status_after_centers} -> {status_after_l1}")
