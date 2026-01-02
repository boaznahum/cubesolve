"""
Test all 30 source/target face pairs using the working test_3cycle_up_front approach.

Based on: test_3cycle_up_front.py which successfully tracks 3-cycle markers.

This script:
1. Tests each of 30 face pairs
2. For each pair, tests target positions (0,0), (0,1), (1,0)
3. Tracks where marker_t moves to find s2
4. Records results to lookup table
"""

import uuid
import yaml
from typing import Tuple, Dict, List, Any
from collections import defaultdict

from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver

Point = Tuple[int, int]

# All 30 face pairs
FACE_PAIRS = [
    # source UP
    ("UP", "FRONT"), ("UP", "BACK"), ("UP", "RIGHT"), ("UP", "LEFT"),
    # source DOWN
    ("DOWN", "FRONT"), ("DOWN", "BACK"), ("DOWN", "RIGHT"), ("DOWN", "LEFT"),
    # source FRONT
    ("FRONT", "UP"), ("FRONT", "DOWN"), ("FRONT", "RIGHT"), ("FRONT", "LEFT"),
    # source BACK
    ("BACK", "UP"), ("BACK", "DOWN"), ("BACK", "RIGHT"), ("BACK", "LEFT"),
    # source RIGHT
    ("RIGHT", "UP"), ("RIGHT", "DOWN"), ("RIGHT", "FRONT"), ("RIGHT", "BACK"),
    # source LEFT
    ("LEFT", "UP"), ("LEFT", "DOWN"), ("LEFT", "FRONT"), ("LEFT", "BACK"),
]


def test_face_pair(source_name: str, target_name: str, cube_size: int = 5) -> Dict[str, Any]:
    """Test one source/target pair using the working test approach."""

    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
    solver = CageNxNSolver(app.op)
    helper = CommunicatorHelper(solver)
    cube = app.cube

    faces = {
        "UP": cube.up,
        "DOWN": cube.down,
        "FRONT": cube.front,
        "BACK": cube.back,
        "RIGHT": cube.right,
        "LEFT": cube.left,
    }

    source_face = faces[source_name]
    target_face = faces[target_name]
    n_slices = cube.n_slices

    # Test positions (same as original: corner and edge positions)
    target_positions = [(0, 0), (0, 1), (1, 0)]

    pair_results = {
        "source": source_name,
        "target": target_name,
        "cube_size": cube_size,
        "test_cases": []
    }

    for target_point in target_positions:
        try:
            cube.reset()

            # Get natural source point
            source_point = helper.get_natural_source_ltr(source_face, target_face, target_point)
            target_block = (target_point, target_point)
            source_block = (source_point, source_point)

            # Create markers
            marker_t_key = f"t_{uuid.uuid4().hex[:4]}"
            marker_s1_key = f"s1_{uuid.uuid4().hex[:4]}"

            # Place markers
            target_piece_before = target_face.center.get_center_slice(target_point)
            target_piece_before.edge.c_attributes[marker_t_key] = "T_MARKER"

            source_piece = source_face.center.get_center_slice(source_point)
            source_piece.edge.c_attributes[marker_s1_key] = "S1_MARKER"

            # Compute s2 candidates
            s2_cw = cube.cqr.rotate_point_clockwise(target_point)
            s2_ccw = cube.cqr.rotate_point_counterclockwise(target_point)

            # Execute communicator
            try:
                alg = helper.do_communicator(
                    source_face=source_face,
                    target_face=target_face,
                    target_block=target_block,
                    source_block=source_block,
                    preserve_state=True
                )
            except Exception as e:
                if "Intersection still exists" in str(e):
                    pair_results["test_cases"].append({
                        "target_point": target_point,
                        "source_point": source_point,
                        "s2_position": None,
                        "s2_face": None,
                        "s2_rotation": None,
                        "valid": False,
                        "error": "intersection"
                    })
                    continue
                else:
                    raise

            # Search for marker_t on all faces
            actual_s2 = None
            actual_s2_face = None
            s2_rotation = None

            all_faces = [cube.front, cube.back, cube.up, cube.down, cube.left, cube.right]
            face_names = ["FRONT", "BACK", "UP", "DOWN", "LEFT", "RIGHT"]

            for face, face_name in zip(all_faces, face_names):
                found = False
                for search_row in range(n_slices):
                    for search_col in range(n_slices):
                        search_point = (search_row, search_col)
                        search_piece = face.center.get_center_slice(search_point)
                        if marker_t_key in search_piece.edge.c_attributes:
                            actual_s2 = search_point
                            actual_s2_face = face_name

                            # Determine rotation
                            if search_point == s2_cw:
                                s2_rotation = "CW"
                            elif search_point == s2_ccw:
                                s2_rotation = "CCW"
                            else:
                                s2_rotation = "OTHER"

                            found = True
                            break
                    if found:
                        break
                if found:
                    break

            # Record result
            pair_results["test_cases"].append({
                "target_point": target_point,
                "source_point": source_point,
                "s2_position": actual_s2,
                "s2_face": actual_s2_face,
                "s2_rotation": s2_rotation,
                "valid": actual_s2 is not None
            })

        except Exception as e:
            pair_results["test_cases"].append({
                "target_point": target_point,
                "source_point": None,
                "s2_position": None,
                "s2_face": None,
                "s2_rotation": None,
                "valid": False,
                "error": str(e)[:50]
            })

    return pair_results


def main():
    """Run tests for all 30 face pairs."""

    print(f"\n{'='*100}")
    print(f"TESTING ALL 30 FACE PAIRS - S2 LOOKUP TABLE")
    print(f"{'='*100}\n")

    all_results = {}
    valid_count = 0
    total_count = 0
    pair_results_summary = {}

    for source, target in FACE_PAIRS:
        pair_name = f"{source}→{target}"
        print(f"Testing {pair_name}...", end=" ", flush=True)

        result = test_face_pair(source, target)
        all_results[pair_name] = result

        # Count valid results
        valid_tests = [t for t in result["test_cases"] if t["valid"]]
        total_count += len(result["test_cases"])
        valid_count += len(valid_tests)

        if valid_tests:
            # Extract s2 rule for this pair
            s2_rotations = set(t["s2_rotation"] for t in valid_tests if t.get("s2_rotation"))
            s2_faces = set(t["s2_face"] for t in valid_tests if t.get("s2_face"))

            if len(s2_rotations) == 1 and len(s2_faces) == 1:
                rule = f"rotate_{list(s2_rotations)[0]}(t) on {list(s2_faces)[0]}"
                print(f"✅ {rule}")
                pair_results_summary[pair_name] = {
                    "rule": rule,
                    "consistent": True,
                    "rotation": list(s2_rotations)[0],
                    "s2_face": list(s2_faces)[0]
                }
            else:
                print(f"⚠️  MIXED RESULTS")
                pair_results_summary[pair_name] = {
                    "rule": f"MIXED: rotations={s2_rotations}, faces={s2_faces}",
                    "consistent": False
                }
        else:
            error_types = set(t.get("error") for t in result["test_cases"] if t.get("error"))
            print(f"❌ All failed: {error_types}")
            pair_results_summary[pair_name] = {
                "rule": f"FAILED: {error_types}",
                "consistent": False
            }

    # Save full results
    with open('/home/user/cubesolve/s2_lookup_table_full.yaml', 'w') as f:
        yaml.dump(all_results, f, default_flow_style=False, sort_keys=False)

    # Save summary lookup table
    with open('/home/user/cubesolve/s2_lookup_table_summary.yaml', 'w') as f:
        yaml.dump(pair_results_summary, f, default_flow_style=False, sort_keys=False)

    # Print summary
    print(f"\n{'='*100}")
    print("SUMMARY")
    print(f"{'='*100}\n")

    print(f"Total tests: {total_count}")
    print(f"Valid results: {valid_count} ({100*valid_count/total_count:.1f}%)")

    consistent_count = sum(1 for r in pair_results_summary.values() if r.get("consistent", False))
    print(f"Consistent rules: {consistent_count}/{len(FACE_PAIRS)}\n")

    print("Consistent S2 Derivation Rules:")
    print("-" * 100)
    for pair_name in sorted(pair_results_summary.keys()):
        info = pair_results_summary[pair_name]
        if info.get("consistent"):
            print(f"{pair_name:20} → {info['rule']}")

    print(f"\n✅ Full results saved to: s2_lookup_table_full.yaml")
    print(f"✅ Summary saved to: s2_lookup_table_summary.yaml\n")


if __name__ == "__main__":
    main()
