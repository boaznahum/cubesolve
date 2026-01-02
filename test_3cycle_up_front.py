"""
Test to understand s2 derivation for UP → FRONT face pair.

This test:
1. Places 3 different markers on s1, t, and s2 (guesses)
2. Executes communicator
3. Tracks where all 3 markers move
4. Records findings to YAML table
5. Determines the rule for deriving s2 from t
"""

import uuid
from typing import Tuple

from cube.application.AbstractApp import AbstractApp
from cube.domain.model.cube_layout.cube_boy import FaceName
from cube.domain.model.Face import Face
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver

Point = Tuple[int, int]


def test_3cycle_up_to_front():
    """
    Test the full 3-cycle for UP → FRONT with multiple target positions.

    3-cycle pattern:
    s1 (source point on UP) → t (target point on FRONT)
    t (target point on FRONT) → s2 (unknown intermediate point)
    s2 → s1
    """

    CUBE_SIZE = 5  # 5x5 for clarity

    app = AbstractApp.create_non_default(cube_size=CUBE_SIZE, animation=False)
    solver = CageNxNSolver(app.op)
    helper = CommunicatorHelper(solver)
    cube = app.cube

    n_slices = cube.n_slices
    print(f"\n{'='*80}")
    print(f"3-CYCLE TEST: UP → FRONT (5x5 cube)")
    print(f"{'='*80}\n")

    # Test target positions on FRONT
    target_positions = [
        (0, 0),  # Top-left
        (0, 1),  # Top-middle
        (1, 0),  # Middle-left
        (1, 1),  # Center
        (2, 1),  # Bottom-middle
    ]

    results = []

    for target_point in target_positions:
        print(f"\n--- Testing target position t = {target_point} ---")

        cube.reset()
        source_face = cube.up
        target_face = cube.front

        # Get natural source point
        natural_source = helper.get_natural_source_ltr(source_face, target_face, target_point)
        print(f"Natural source s1 = {natural_source}")

        # For this test, use source point at natural position (rotation=0)
        source_point = natural_source
        target_block = (target_point, target_point)
        source_block = (source_point, source_point)

        # Create 3 UNIQUE markers
        marker_s1_key = f"s1_{uuid.uuid4().hex[:4]}"
        marker_t_key = f"t_{uuid.uuid4().hex[:4]}"
        marker_s2_key = f"s2_{uuid.uuid4().hex[:4]}"

        marker_s1_val = "S1_MARKER"
        marker_t_val = "T_MARKER"
        marker_s2_val = "S2_MARKER"

        # Place marker on s1 (source)
        source_piece = source_face.center.get_center_slice(source_point)
        source_piece.edge.c_attributes[marker_s1_key] = marker_s1_val
        print(f"Placed {marker_s1_key}={marker_s1_val} at s1={source_point} on UP")

        # Place marker on t (target) - BEFORE execution
        target_piece_before = target_face.center.get_center_slice(target_point)
        target_piece_before.edge.c_attributes[marker_t_key] = marker_t_val
        print(f"Placed {marker_t_key}={marker_t_val} at t={target_point} on FRONT")

        # Try s2 as clockwise rotation of t
        s2_cw = cube.cqr.rotate_point_clockwise(target_point)
        s2_ccw = cube.cqr.rotate_point_counterclockwise(target_point)

        print(f"  s2 if clockwise: {s2_cw}")
        print(f"  s2 if counter-clockwise: {s2_ccw}")

        # Place marker on both potential s2 positions
        # We'll check which one moves to s1
        s2_piece_cw = target_face.center.get_center_slice(s2_cw)
        s2_piece_cw.edge.c_attributes[f"s2_cw_{uuid.uuid4().hex[:4]}"] = "S2_CW"

        s2_piece_ccw = target_face.center.get_center_slice(s2_ccw)
        s2_piece_ccw.edge.c_attributes[f"s2_ccw_{uuid.uuid4().hex[:4]}"] = "S2_CCW"

        # Execute communicator
        print(f"Executing communicator...")
        alg = helper.do_communicator(
            source_face=source_face,
            target_face=target_face,
            target_block=target_block,
            source_block=source_block,
            preserve_state=True
        )

        # Now check where all markers are
        print(f"\nAfter communicator:")

        # Check s1: should now have marker_t
        source_piece_after = source_face.center.get_center_slice(source_point)
        s1_has_marker_s1 = marker_s1_key in source_piece_after.edge.c_attributes
        s1_has_marker_t = marker_t_key in source_piece_after.edge.c_attributes
        s1_markers = [f"{k}={v}" for k, v in source_piece_after.edge.c_attributes.items()
                      if k.startswith(("s1_", "t_", "s2_"))]
        print(f"  At s1={source_point} on UP: {s1_markers}")

        # Check target: should have marker_s1
        target_piece_after = target_face.center.get_center_slice(target_point)
        t_has_marker_s1 = marker_s1_key in target_piece_after.edge.c_attributes
        t_markers = [f"{k}={v}" for k, v in target_piece_after.edge.c_attributes.items()
                     if k.startswith(("s1_", "t_", "s2_"))]
        print(f"  At t={target_point} on FRONT: {t_markers}")

        # Check s2_cw position
        s2_cw_piece = target_face.center.get_center_slice(s2_cw)
        s2_cw_markers = [f"{k}={v}" for k, v in s2_cw_piece.edge.c_attributes.items()
                         if k.startswith(("s1_", "t_", "s2_"))]
        print(f"  At s2_cw={s2_cw} on FRONT: {s2_cw_markers}")

        # Check s2_ccw position
        s2_ccw_piece = target_face.center.get_center_slice(s2_ccw)
        s2_ccw_markers = [f"{k}={v}" for k, v in s2_ccw_piece.edge.c_attributes.items()
                          if k.startswith(("s1_", "t_", "s2_"))]
        print(f"  At s2_ccw={s2_ccw} on FRONT: {s2_ccw_markers}")

        # SEARCH: Find where marker_t actually went (on ALL 6 faces!)
        actual_s2 = None
        actual_s2_face = None
        s2_rotation = None

        print(f"  Searching ALL FACES for {marker_t_key}...")
        all_faces = [cube.front, cube.back, cube.up, cube.down, cube.left, cube.right]
        face_names = ["FRONT", "BACK", "UP", "DOWN", "LEFT", "RIGHT"]

        for face, face_name in zip(all_faces, face_names):
            for search_row in range(n_slices):
                for search_col in range(n_slices):
                    search_point = (search_row, search_col)
                    search_piece = face.center.get_center_slice(search_point)
                    if marker_t_key in search_piece.edge.c_attributes:
                        actual_s2 = search_point
                        actual_s2_face = face_name
                        # Determine rotation type
                        if search_point == s2_cw:
                            s2_rotation = "CW"
                        elif search_point == s2_ccw:
                            s2_rotation = "CCW"
                        else:
                            s2_rotation = "OTHER"
                        print(f"    Found {marker_t_key} at {actual_s2} on {face_name} (rotation: {s2_rotation})")
                        break
                if actual_s2:
                    break
            if actual_s2:
                break

        if not actual_s2:
            print(f"    ⚠️  {marker_t_key} not found on any face!")

        # Verify 3-cycle
        cycle_valid = (
            s1_has_marker_t and
            t_has_marker_s1 and
            actual_s2 is not None
        )

        result = {
            "target_point": target_point,
            "source_point": source_point,
            "s2_actual": actual_s2,
            "s2_face": actual_s2_face,
            "s2_rotation": s2_rotation,
            "cycle_valid": cycle_valid,
            "algorithm": str(alg),
        }
        results.append(result)

        print(f"  3-cycle valid: {cycle_valid}")
        print(f"  s2 is at: {actual_s2} (via {s2_rotation} rotation)")
        print()

    # Print summary table
    print(f"\n{'='*80}")
    print("SUMMARY: UP → FRONT")
    print(f"{'='*80}")
    print(f"{'Target':<12} {'Source':<12} {'s2 Position':<15} {'s2 Face':<10} {'Rotation':<10} {'Valid':<8}")
    print("-" * 80)
    for r in results:
        print(f"{str(r['target_point']):<12} {str(r['source_point']):<12} "
              f"{str(r['s2_actual']):<15} {str(r['s2_face']):<10} {str(r['s2_rotation']):<10} {str(r['cycle_valid']):<8}")

    # Check if pattern is consistent
    rotations = [r['s2_rotation'] for r in results if r['s2_rotation']]
    if len(set(rotations)) == 1:
        print(f"\n✅ CONSISTENT RULE: s2 = rotate_{rotations[0].lower()}(t)")
    else:
        print(f"\n❌ INCONSISTENT: Different rotations needed for different positions")
        print(f"   Rotations used: {set(rotations)}")

    # All should be valid
    assert all(r['cycle_valid'] for r in results), "Some cycles are invalid!"
    print("\n✅ All 3-cycles validated!")


if __name__ == "__main__":
    test_3cycle_up_to_front()
