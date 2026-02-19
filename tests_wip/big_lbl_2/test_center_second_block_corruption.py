"""
Test for second block corruption bug in LBL NxN centers solver.

Bug Description:
================
When the optimization in _LBLNxNCenters._source_block_has_color_no_rotation
(lines 721-723) is enabled, previously solved pieces in the second block (s2)
get corrupted during commutator execution.

Specific Case:
- Cube size: 12 (n_slices=10)
- Working on row 3
- Target block: Point(row=3, col=7)
- Second block (computed): Point(row=2, col=3) - previously solved row 2
- Source face: BACK
- Corruption: Piece at (2,3) changes from BLUE (expected) to ORANGE

The 3-Cycle:
============
The commutator performs: target → second → source → target
- Target's color → Second block (this corrupts the solved piece!)
- Second's color → Source
- Source's color → Target

Test Strategy:
==============
Following the pattern from tests/geometry/test_commutator_helper.py:
1. Set up the specific scenario (size 12, target at (3,7), source=BACK)
2. Place unique markers on all 3 cycle points (s1, t, s2)
3. Mark second piece as "solved" (simulate previously solved row)
4. Record second piece color BEFORE commutator
5. Execute commutator
6. Verify 3-cycle completed correctly (markers moved)
7. Verify second block NOT corrupted (color unchanged)

Expected Results:
=================
- With optimization DISABLED (current state): Test PASSES
- With optimization ENABLED (uncommenting lines 721-723): Test FAILS (second block corrupted)
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.geometric.block import Block
from cube.domain.geometric.geometry_types import Point
from cube.domain.model.Face import Face
from cube.domain.solver.common.big_cube.commutator.CommutatorHelper import CommutatorHelper
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver
from cube.domain.solver.Solvers import Solvers

if TYPE_CHECKING:
    from cube.domain.model.PartEdge import PartEdge


def _cage(app: AbstractApp) -> CageNxNSolver:
    """Create CageNxNSolver through factory with correct type hint."""
    solver = Solvers.cage(app.op)
    assert isinstance(solver, CageNxNSolver)
    return solver


def search_marker_location(
    marker_key: str,
    faces: list[Face],
    n_slices: int
) -> tuple[str, Point] | None:
    """
    Search for a marker on multiple faces.

    Args:
        marker_key: Marker attribute key to search for
        faces: List of faces to search
        n_slices: Number of center slices

    Returns:
        (face_name, point) where marker was found, or None if not found
    """
    for face in faces:
        for row in range(n_slices):
            for col in range(n_slices):
                point = Point(row, col)
                piece = face.center.get_center_slice(point).edge
                if marker_key in piece.moveable_attributes:
                    return (face.name.name, point)
    return None


def test_second_block_corruption_minimal_reproduction():
    """
    Minimal reproduction of the second block corruption bug.

    This test reproduces the specific case from state.md:
    - GUI seed 1, size 12
    - Target block at (3, 7) on row 3
    - Second block at (2, 3) on row 2 (previously solved)
    - Source face: BACK

    The test verifies:
    1. The 3-cycle completes correctly (markers move as expected)
    2. The second block is NOT corrupted (color unchanged)

    Follows the pattern from tests/geometry/test_commutator_helper.py:
    - Tests all 4 rotations (0°, 90°, 180°, 270°)
    - Resets cube for each rotation (creates new objects!)
    - Rotates both source and second points together
    - Recreates solver/helper after each reset

    Current Status:
    - With optimization DISABLED (lines 721-723 commented): Should PASS
    - With optimization ENABLED (lines 721-723 uncommented): Should FAIL
    """
    # Create 12x12 cube
    cube_size = 12
    app = AbstractApp.create_app(cube_size=cube_size)
    cube = app.cube
    n_slices = cube.n_slices

    assert n_slices == 10, f"Expected n_slices=10 for 12x12 cube, got {n_slices}"

    # Set up face names (not Face objects - those will be recreated after reset)
    from cube.domain.model.FaceName import FaceName
    target_face_name = FaceName.F  # FRONT
    source_face_name = FaceName.B  # BACK

    # Target point from bug report (this stays constant, not rotated)
    target_point = Point(3, 7)

    # Collect results for all rotations
    all_results = []

    print(f"\n{'='*80}")
    print(f"SCENARIO SETUP")
    print(f"{'='*80}")
    print(f"Cube size: {cube_size} (n_slices={n_slices})")
    print(f"Target face: {target_face_name.name}")
    print(f"Source face: {source_face_name.name}")
    print(f"Target point: {target_point}")

    # =========================================================================
    # ITERATE ALL 4 ROTATIONS (following geometry test pattern)
    # =========================================================================
    for rotation in range(4):
        print(f"\n{'='*80}")
        print(f"ROTATION {rotation} (source rotated {rotation * 90}° clockwise)")
        print(f"{'='*80}")

        # Reset cube to pristine state for each rotation
        # IMPORTANT: This creates new Face objects!
        cube = app.cube
        cube.reset()
        solver = _cage(app)
        helper = CommutatorHelper(solver)

        # Re-get faces from reset cube (new objects after reset!)
        source_face = cube.face(source_face_name)
        target_face = cube.face(target_face_name)

        target_block = Block(target_point, target_point)

        # =====================================================================
        # Get natural source and second points from dry_run
        # =====================================================================
        dry_result = helper.execute_commutator(
            source_face=source_face,
            target_face=target_face,
            target_block=target_block,
            dry_run=True
        )

        natural_source_point = dry_result.natural_source_block.as_point
        natural_second_point = dry_result.second_block.as_point

        # Rotate both source and second points by the same rotation
        # (they're both on source face, so rotate together)
        rotated_source_point = cube.cqr.rotate_point_clockwise(natural_source_point, rotation)
        rotated_second_point = cube.cqr.rotate_point_clockwise(natural_second_point, rotation)

        print(f"Natural source: {natural_source_point}, rotated: {rotated_source_point}")
        print(f"Natural second: {natural_second_point}, rotated: {rotated_second_point}")

        # =====================================================================
        # Place unique markers on ROTATED positions
        # =====================================================================
        marker_s1_key = f"marker_s1_{uuid.uuid4().hex[:8]}"
        marker_s1_value = f"s1_{uuid.uuid4().hex[:4]}"

        marker_t_key = f"marker_t_{uuid.uuid4().hex[:8]}"
        marker_t_value = f"t_{uuid.uuid4().hex[:4]}"

        marker_s2_key = f"marker_s2_{uuid.uuid4().hex[:8]}"
        marker_s2_value = f"s2_{uuid.uuid4().hex[:4]}"

        # Get pieces at ROTATED positions
        source_piece = source_face.center.get_center_slice(rotated_source_point).edge
        target_piece = target_face.center.get_center_slice(target_point).edge
        second_piece = source_face.center.get_center_slice(rotated_second_point).edge

        # Place markers
        source_piece.moveable_attributes[marker_s1_key] = marker_s1_value
        target_piece.moveable_attributes[marker_t_key] = marker_t_value
        second_piece.moveable_attributes[marker_s2_key] = marker_s2_value

        # =====================================================================
        # Execute commutator with ROTATED source block
        # =====================================================================
        helper.execute_commutator(
            source_face=source_face,
            target_face=target_face,
            target_block=target_block,
            source_block=Block(rotated_source_point, rotated_source_point),
            preserve_state=True,
            dry_run=False,
            _cached_secret=dry_result
        )

        # =====================================================================
        # Verify 3-cycle: s1 → t → s2 → s1
        # =====================================================================
        # Get pieces AFTER commutator
        source_piece_after = source_face.center.get_center_slice(rotated_source_point).edge
        target_piece_after = target_face.center.get_center_slice(target_point).edge
        second_piece_after = source_face.center.get_center_slice(rotated_second_point).edge

        cycle_ok = True
        cycle_errors = []

        # Expected locations after 3-cycle
        expected_s1_location = (target_face.name.name, target_point)
        expected_t_location = (source_face.name.name, rotated_second_point)
        expected_s2_location = (source_face.name.name, rotated_source_point)

        # Search ALL faces (not just source/target) - bug might move markers elsewhere!
        all_faces = list(cube.faces)

        # Verify marker_s1 moved to target
        if marker_s1_key not in target_piece_after.moveable_attributes:
            actual_s1 = search_marker_location(marker_s1_key, all_faces, n_slices)
            cycle_ok = False
            cycle_errors.append(f"marker_s1: expected {expected_s1_location}, found {actual_s1}")
        elif target_piece_after.moveable_attributes[marker_s1_key] != marker_s1_value:
            cycle_ok = False
            cycle_errors.append("marker_s1: value mismatch")

        # Verify marker_t moved to second
        if marker_t_key not in second_piece_after.moveable_attributes:
            actual_t = search_marker_location(marker_t_key, all_faces, n_slices)
            cycle_ok = False
            cycle_errors.append(f"marker_t: expected {expected_t_location}, found {actual_t}")
        elif second_piece_after.moveable_attributes[marker_t_key] != marker_t_value:
            cycle_ok = False
            cycle_errors.append("marker_t: value mismatch")

        # Verify marker_s2 moved to source
        if marker_s2_key not in source_piece_after.moveable_attributes:
            actual_s2 = search_marker_location(marker_s2_key, all_faces, n_slices)
            cycle_ok = False
            cycle_errors.append(f"marker_s2: expected {expected_s2_location}, found {actual_s2}")
        elif source_piece_after.moveable_attributes[marker_s2_key] != marker_s2_value:
            cycle_ok = False
            cycle_errors.append("marker_s2: value mismatch")

        # Verify markers NOT in original positions
        if marker_s1_key in source_piece_after.moveable_attributes:
            cycle_ok = False
            cycle_errors.append("marker_s1 still at original position")
        if marker_t_key in target_piece_after.moveable_attributes:
            cycle_ok = False
            cycle_errors.append("marker_t still at original position")
        if marker_s2_key in second_piece_after.moveable_attributes:
            cycle_ok = False
            cycle_errors.append("marker_s2 still at original position")

        print(f"3-cycle: {'✅ OK' if cycle_ok else '❌ FAILED'}")

        if not cycle_ok:
            print("  Errors:")
            for error in cycle_errors:
                print(f"    • {error}")

        # Record result for this rotation
        all_results.append({
            "rotation": rotation,
            "cycle_ok": cycle_ok,
            "cycle_errors": cycle_errors,
        })

    # =========================================================================
    # Final Report and Assertions
    # =========================================================================
    print(f"\n{'='*80}")
    print(f"FINAL RESULTS (all rotations)")
    print(f"{'='*80}")

    failures = []
    for result in all_results:
        rot = result["rotation"]
        if not result["cycle_ok"]:
            failures.append(f"Rotation {rot}: 3-cycle FAILED - {', '.join(result['cycle_errors'])}")

    if failures:
        print("❌ FAILURES:")
        for failure in failures:
            print(f"  • {failure}")
        pytest.fail("\n" + "\n".join(failures))
    else:
        print("✅ ALL ROTATIONS PASSED - 3-cycle markers moved correctly")
