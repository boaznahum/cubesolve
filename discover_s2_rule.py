#!/usr/bin/env python
"""Discover s2 derivation rule for all source/target face pairs."""

import sys
sys.path.insert(0, '/home/user/cubesolve/src')

import uuid
import yaml
from typing import Dict, List, Any, Tuple

from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver

Point = Tuple[int, int]

# List of (source, target) face pairs to test
FACE_PAIRS = [
    ("UP", "FRONT"),
    ("UP", "RIGHT"),
    ("UP", "BACK"),
    ("UP", "LEFT"),
    ("DOWN", "FRONT"),
    ("DOWN", "RIGHT"),
    ("FRONT", "UP"),
    ("FRONT", "RIGHT"),
]


def test_single_pair(source_name: str, target_name: str) -> Dict[str, Any]:
    """Test one source/target pair and return results."""

    # Create app - use explicit cube size like test_marker_tracking.py does
    CUBE_SIZE = 5
    app = AbstractApp.create_non_default(cube_size=CUBE_SIZE, animation=False)
    solver = CageNxNSolver(app.op)
    helper = CommunicatorHelper(solver)
    cube = app.cube

    # Get face objects
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

    # Define target positions to test
    target_positions = [(0, 0)]
    if n_slices > 2:
        target_positions.extend([(0, n_slices - 1), (n_slices - 1, 0)])

    pair_name = f"{source_name}→{target_name}"
    pair_results = {
        "source": source_name,
        "target": target_name,
        "test_cases": []
    }

    print(f"\n  Testing {pair_name} (cube {n_slices}x{n_slices})...")

    for target_point in target_positions:
        cube.reset()

        # Get source point
        source_point = helper.get_natural_source_ltr(source_face, target_face, target_point)

        # Place marker on target
        marker_t_key = f"t_{uuid.uuid4().hex[:4]}"
        target_piece = target_face.center.get_center_slice(target_point)
        target_piece.edge.c_attributes[marker_t_key] = "T_MARKER"

        try:
            # Execute communicator
            alg = helper.do_communicator(
                source_face=source_face,
                target_face=target_face,
                target_block=(target_point, target_point),
                source_block=(source_point, source_point),
                preserve_state=True
            )

            # Search for marker on all faces
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
                            s2_cw = cube.cqr.rotate_point_clockwise(target_point)
                            s2_ccw = cube.cqr.rotate_point_counterclockwise(target_point)
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

            test_case = {
                "target_point": target_point,
                "source_point": source_point,
                "s2_position": actual_s2,
                "s2_face": actual_s2_face,
                "s2_rotation": s2_rotation,
                "valid": actual_s2 is not None,
            }
            pair_results["test_cases"].append(test_case)

            if actual_s2:
                print(f"    t={str(target_point):7} → s2={str(actual_s2):7} on {actual_s2_face:6} {s2_rotation} ✅")
            else:
                print(f"    t={str(target_point):7} → NOT FOUND ❌")

        except Exception as e:
            if "Intersection" in str(e):
                print(f"    t={str(target_point):7} → INTERSECTION ERROR (center position)")
                pair_results["test_cases"].append({
                    "target_point": target_point,
                    "valid": False,
                    "error": "intersection"
                })
            else:
                print(f"    t={str(target_point):7} → ERROR: {str(e)[:50]}")
                raise

    return pair_results


def main():
    """Test all face pairs and discover the s2 rule."""

    print(f"\n{'='*100}")
    print("S2 DERIVATION RULE DISCOVERY")
    print(f"{'='*100}")

    all_results = {}

    for source, target in FACE_PAIRS:
        try:
            result = test_single_pair(source, target)
            pair_name = f"{source}→{target}"
            all_results[pair_name] = result

            # Analyze pattern
            valid_tests = [t for t in result["test_cases"] if t.get("valid", False)]
            if valid_tests:
                rotations = set(t["s2_rotation"] for t in valid_tests if t.get("s2_rotation"))
                s2_face = valid_tests[0].get("s2_face")

                if len(rotations) == 1:
                    rotation_type = list(rotations)[0]
                    print(f"    → Rule: s2 = rotate_{rotation_type}(t) on {s2_face}")
                else:
                    print(f"    → Mixed rotations: {rotations}")

        except Exception as e:
            print(f"  ❌ FAILED: {source}→{target}: {str(e)[:80]}")

    # Save results to YAML
    print(f"\n{'='*100}")
    print("SAVING RESULTS")
    print(f"{'='*100}")

    yaml_data = {}
    for pair_name, data in all_results.items():
        source, target = pair_name.split("→")
        valid_tests = [t for t in data["test_cases"] if t.get("valid")]

        if valid_tests:
            rotations = set(t["s2_rotation"] for t in valid_tests if t.get("s2_rotation"))
            s2_face = valid_tests[0].get("s2_face")
            if len(rotations) == 1:
                rule = f"rotate_{list(rotations)[0]}(t) on {s2_face}"
            else:
                rule = f"MIXED: {rotations}"
        else:
            rule = "NO_VALID_TESTS"

        yaml_data[pair_name] = {
            "source_face": source,
            "target_face": target,
            "s2_rule": rule,
            "test_cases": [
                {
                    "target": t["target_point"],
                    "s2": t.get("s2_position"),
                    "s2_face": t.get("s2_face"),
                    "rotation": t.get("s2_rotation"),
                    "valid": t.get("valid"),
                }
                for t in data["test_cases"]
                if t.get("valid") is not None
            ]
        }

    with open('/home/user/cubesolve/s2_rule_discovery.yaml', 'w') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    print(f"✅ Saved to s2_rule_discovery.yaml\n")

    # Print summary
    print(f"{'='*100}")
    print("SUMMARY")
    print(f"{'='*100}\n")

    for pair_name in sorted(all_results.keys()):
        data = all_results[pair_name]
        valid_tests = [t for t in data["test_cases"] if t.get("valid")]
        if valid_tests:
            s2_face = valid_tests[0].get("s2_face")
            rotations = set(t["s2_rotation"] for t in valid_tests)
            if len(rotations) == 1:
                print(f"{pair_name:20} → s2 = rotate_{list(rotations)[0]:3}(t) on {s2_face}")
            else:
                print(f"{pair_name:20} → MIXED ROTATIONS: {rotations}")
        else:
            print(f"{pair_name:20} → NO VALID RESULTS")


if __name__ == "__main__":
    main()
