"""Tests for tracker behavior with even color distribution.

GitHub Issue: https://github.com/boaznahum/cubesolve/issues/51

SCENARIO:
=========
When creating trackers on an even cube (4x4, 6x6) where:
1. Two opposite faces are fully solved (e.g., U=YELLOW, D=WHITE)
2. The remaining 4 faces have EVEN distribution of colors (1 of each)

The majority algorithm in _find_face_with_max_colors has no clear winner
when all colors have the same count (1) on each side face.

BUG STATUS: Under Review (#51)
==============================
Initial investigation suggested the bug does not manifest due to BOY constraints,
but the test scenario may not correctly reproduce the problematic state.

The concern is that arbitrary tie-breaking could assign the same color
to multiple faces, resulting in only 5 unique colors instead of 6.

WHAT THESE TESTS VERIFY:
========================
1. Even distribution produces valid 6-color BOY layout
2. L1 solved state is consistent after Y rotation
3. Fresh trackers after rotation give equivalent BOY layout
4. Random scrambles always produce valid trackers

See: src/cube/domain/solver/direct/lbl/TRACKER_MAJORITY_BUG.md
"""
from __future__ import annotations

import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.model import Color
from cube.domain.model.FaceName import FaceName
from cube.domain.solver.common.big_cube.FacesTrackerHolder import FacesTrackerHolder
from cube.domain.solver.direct.lbl.LayerByLayerNxNSolver import LayerByLayerNxNSolver


def _setup_even_distribution_cube(app: AbstractApp) -> None:
    """Set up a 4x4 cube with even color distribution on side faces.

    Configuration:
    - U face: All 4 centers are YELLOW (solved)
    - D face: All 4 centers are WHITE (solved)
    - F, B, L, R faces: Each has exactly 1 BLUE, 1 GREEN, 1 ORANGE, 1 RED

    This creates a scenario where the majority algorithm has no clear winner.

    Center layout on each side face (2x2 grid):
        ┌─────┬─────┐
        │ B   │ G   │  (Blue, Green)
        ├─────┼─────┤
        │ O   │ R   │  (Orange, Red)
        └─────┴─────┘
    """
    cube = app.cube

    # Colors for the side faces - one of each
    side_colors = [
        [Color.BLUE, Color.GREEN],     # Row 0: Blue, Green
        [Color.ORANGE, Color.RED]      # Row 1: Orange, Red
    ]

    # Set U face - all YELLOW
    u_face = cube.face(FaceName.U)
    for i in range(2):
        for j in range(2):
            u_face.center.get_slice((i, j)).edges[0]._color = Color.YELLOW

    # Set D face - all WHITE
    d_face = cube.face(FaceName.D)
    for i in range(2):
        for j in range(2):
            d_face.center.get_slice((i, j)).edges[0]._color = Color.WHITE

    # Set side faces - each has 1 of each remaining color
    for face_name in [FaceName.F, FaceName.B, FaceName.L, FaceName.R]:
        face = cube.face(face_name)
        for i in range(2):
            for j in range(2):
                face.center.get_slice((i, j)).edges[0]._color = side_colors[i][j]

    # Reset caches after direct color changes
    cube.reset_after_faces_changes()
    cube.modified()


def _count_unique_colors(trackers: list) -> int:
    """Count how many unique colors are assigned by trackers."""
    colors = set()
    for tracker in trackers:
        colors.add(tracker.color)
    return len(colors)


def _print_tracker_assignment(trackers: list) -> None:
    """Print the tracker face→color assignment for debugging."""
    print("\nTracker assignment:")
    for tracker in trackers:
        print(f"  {tracker.face.name} -> {tracker.color}")


class TestTrackerMajorityBug:
    """Tests for tracker majority algorithm bug (#51)."""

    def test_even_distribution_creates_valid_trackers(self) -> None:
        """Test that trackers on even distribution cube produce valid BOY layout.

        This test attempts to expose the bug (#51): with even color distribution,
        the majority algorithm may assign the same color to multiple faces.

        Note: Current test passes but may not correctly reproduce the bug scenario.
        """
        app = AbstractApp.create_non_default(cube_size=4, animation=False)

        # Set up the problematic cube configuration
        _setup_even_distribution_cube(app)

        # Create solver (which creates trackers)
        solver = LayerByLayerNxNSolver(app.op)

        # Create trackers using FacesTrackerHolder
        with FacesTrackerHolder(solver) as th:
            # Print the assignment for debugging
            _print_tracker_assignment(th.trackers)

            # Count unique colors
            unique_colors = _count_unique_colors(th.trackers)
            print(f"\nUnique colors assigned: {unique_colors}")

            # This SHOULD pass (6 unique colors for valid BOY)
            # But MAY FAIL due to the bug (only 5 colors if one is duplicated)
            assert unique_colors == 6, (
                f"Expected 6 unique colors for valid BOY layout, "
                f"but got {unique_colors}. "
                f"This indicates the tracker majority bug!"
            )

            # Also verify it's a valid BOY using the holder's method
            th.assert_is_boy()

    def test_solved_l1_with_y_rotation_still_solved(self) -> None:
        """Test that L1 solved check is consistent after Y rotation.

        Scenario:
        1. Start with even distribution cube
        2. Solve Layer 1
        3. Check L1 is solved
        4. Rotate Y (whole cube rotation)
        5. Check L1 is still solved

        If trackers are created fresh after Y rotation with different
        color assignments, the L1 check may fail even though nothing
        changed except the cube orientation!
        """
        app = AbstractApp.create_non_default(cube_size=4, animation=False)

        # Set up the problematic cube configuration
        _setup_even_distribution_cube(app)

        solver = LayerByLayerNxNSolver(app.op)

        # Create a tracker holder and keep it across Y rotation
        # The trackers should move with the rotation
        with FacesTrackerHolder(solver) as th:
            # Check if L1 is currently solved (it might not be with our setup)
            # The point is: if it IS solved, it should remain solved after Y rotation
            is_l1_solved_before = solver._is_layer1_solved(th)
            print(f"\nL1 solved before Y: {is_l1_solved_before}")

            # Perform a Y rotation (whole cube)
            from cube.domain.algs import Algs
            app.op.play(Algs.Y)

            # Check L1 again with the SAME tracker holder
            # The trackers should have moved with the rotation
            is_l1_solved_after = solver._is_layer1_solved(th)
            print(f"L1 solved after Y: {is_l1_solved_after}")

            # The solved state should be consistent!
            assert is_l1_solved_before == is_l1_solved_after, (
                f"L1 solved state changed after Y rotation! "
                f"Before: {is_l1_solved_before}, After: {is_l1_solved_after}. "
                f"This indicates a tracker consistency bug."
            )

    def test_fresh_trackers_after_y_rotation_same_assignment(self) -> None:
        """Test that fresh trackers after Y rotation give equivalent BOY layout.

        This is the CORE bug test:
        1. Create trackers → get face→color mapping A
        2. Rotate Y
        3. Create NEW trackers → get face→color mapping B

        Mappings A and B should be equivalent (same colors to same logical faces).
        But with even distribution, they might differ randomly!
        """
        app = AbstractApp.create_non_default(cube_size=4, animation=False)

        # Set up the problematic cube configuration
        _setup_even_distribution_cube(app)

        solver = LayerByLayerNxNSolver(app.op)

        # Create first set of trackers and get face→color mapping
        with FacesTrackerHolder(solver) as th1:
            mapping1 = {tracker.face.name: tracker.color for tracker in th1.trackers}
            print(f"\nMapping before Y: {mapping1}")

        # Rotate Y
        from cube.domain.algs import Algs
        app.op.play(Algs.Y)

        # Create NEW trackers after rotation
        with FacesTrackerHolder(solver) as th2:
            mapping2 = {tracker.face.name: tracker.color for tracker in th2.trackers}
            print(f"Mapping after Y: {mapping2}")

        # After Y rotation:
        # - What was F is now R
        # - What was R is now B
        # - What was B is now L
        # - What was L is now F
        # - U and D stay the same

        # So mapping1[F] should equal mapping2[R], etc.
        # But the colors assigned should be the same 6 colors!

        colors1 = set(mapping1.values())
        colors2 = set(mapping2.values())

        print(f"Colors in mapping1: {colors1}")
        print(f"Colors in mapping2: {colors2}")

        # Both should have exactly 6 unique colors
        assert len(colors1) == 6, f"Mapping1 should have 6 colors, got {len(colors1)}"
        assert len(colors2) == 6, f"Mapping2 should have 6 colors, got {len(colors2)}"

        # The SET of colors should be identical (same 6 colors, just on different faces due to rotation)
        assert colors1 == colors2, (
            f"Color sets differ after Y rotation! "
            f"Before: {colors1}, After: {colors2}"
        )


@pytest.mark.parametrize("seed", range(5))
def test_random_scramble_tracker_validity(seed: int) -> None:
    """Test that random scrambles still produce valid tracker assignments.

    This tests that normal scrambles (not the pathological even distribution)
    still work correctly. The bug is specific to even distributions.
    """
    app = AbstractApp.create_non_default(cube_size=4, animation=False)

    # Normal scramble
    app.scramble(seed, None, animation=False, verbose=False)

    solver = LayerByLayerNxNSolver(app.op)

    with FacesTrackerHolder(solver) as th:
        unique_colors = _count_unique_colors(th.trackers)

        # Random scrambles should always produce valid 6-color assignments
        # because they have clear majorities
        assert unique_colors == 6, (
            f"Expected 6 unique colors even with random scramble (seed={seed}), "
            f"got {unique_colors}"
        )

        # Should be valid BOY
        th.assert_is_boy()
