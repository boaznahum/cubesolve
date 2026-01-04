#!/usr/bin/env python
"""Test all face pairs to discover the universal s2 derivation rule."""

import sys
sys.path.insert(0, '/home/user/cubesolve/src')

import uuid
import yaml
from typing import Tuple, Dict, List, Any

from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver

Point = Tuple[int, int]

# Test pairs to run
TEST_PAIRS = [
    ("UP", "FRONT"),
    ("UP", "RIGHT"),
    ("UP", "BACK"),
    ("UP", "LEFT"),
    ("DOWN", "FRONT"),
    ("DOWN", "RIGHT"),
    ("FRONT", "UP"),
    ("FRONT", "DOWN"),
    ("FRONT", "RIGHT"),
    ("RIGHT", "UP"),
    ("RIGHT", "FRONT"),
]


def test_face_pair(source_name: str, target_name: str) -> Dict[str, Any]:
    """Test a single face pair and return results."""

    # Create cube (will be 3x3 by default)
    app = AbstractApp.create_non_default(cube_size=None, animation=False)
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

    # Test corner positions
    target_positions = []
    if n_slices >= 2:
        target_positions.append((0, 0))
        if n_slices > 2:
            target_positions.append((0, n_slices - 1))
            target_positions.append((n_slices - 1, 0))

    # DEBUG
    print(f"    cube_size={n_slices}, testing {len(target_positions)} positions")

    pair_results = {
        "source": source_name,
        "target": target_name,
        "cube_size": n_slices,
        "test_cases": []
    }

    for target_point in target_positions:
        try:
            cube.reset()
            source_point = helper.get_natural_source_ltr(source_face, target_face, target_point)

            # Place marker on target
            marker_t_key = f"t_{uuid.uuid4().hex[:4]}"
            target_piece = target_face.center.get_center_slice(target_point)
            target_piece.edge.c_attributes[marker_t_key] = "T_MARKER"

            # Execute communicator
            alg = helper.do_communicator(
                source_face=source_face,
                target_face=target_face,
                target_block=(target_point, target_point),
                source_block=(source_point, source_point),
                preserve_state=True
            )

            # Find where marker ended up
            actual_s2 = None
            actual_s2_face = None
            s2_rotation = None

            all_faces = [cube.front, cube.back, cube.up, cube.down, cube.left, cube.right]
            face_names = ["FRONT", "BACK", "UP", "DOWN", "LEFT", "RIGHT"]

            for face, face_name in zip(all_faces, face_names):
                found = False
                for r in range(n_slices):
                    for c in range(n_slices):
                        pos = (r, c)
                        piece = face.center.get_center_slice(pos)
                        if marker_t_key in piece.edge.c_attributes:
                            actual_s2 = pos
                            actual_s2_face = face_name

                            # Determine rotation type
                            s2_cw = cube.cqr.rotate_point_clockwise(target_point)
                            s2_ccw = cube.cqr.rotate_point_counterclockwise(target_point)
                            if pos == s2_cw:
                                s2_rotation = "CW"
                            elif pos == s2_ccw:
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

            # DEBUG
            if actual_s2 is None:
                print(f"    DEBUG: t={target_point}, marker not found")

        except Exception as e:
            error_str = str(e)
            # Only skip if it's an intersection error
            if "Intersection still exists" in error_str:
                test_case = {
                    "target_point": target_point,
                    "source_point": None,
                    "s2_position": None,
                    "s2_face": None,
                    "s2_rotation": None,
                    "valid": False,
                    "error": "intersection"
                }
                pair_results["test_cases"].append(test_case)
            else:
                raise

    return pair_results


def main():
    """Test all face pairs."""

    print(f"\n{'='*100}")
    print("S2 DERIVATION RULE DISCOVERY - ALL FACE PAIRS")
    print(f"{'='*100}\n")

    all_results = {}

    for source, target in TEST_PAIRS:
        pair_name = f"{source}→{target}"
        print(f"Testing {pair_name}...", flush=True)

        try:
            results = test_face_pair(source, target)
            all_results[pair_name] = results

            # Print inline results
            valid_tests = [t for t in results["test_cases"] if t["valid"]]
            if valid_tests:
                rotations = [t["s2_rotation"] for t in valid_tests]
                unique_rotations = set(rotations)
                if len(unique_rotations) == 1:
                    s2_face = valid_tests[0]["s2_face"]
                    print(f"  ✅ Consistent: rotate_{list(unique_rotations)[0]}(t) on {s2_face}")
                else:
                    print(f"  ⚠️  Mixed rotations: {unique_rotations}")
                    for t in valid_tests:
                        print(f"     t={t['target_point']} → {t['s2_rotation']}")
            else:
                print(f"  ⚠️  No valid results")

        except Exception as e:
            print(f"  ❌ ERROR: {str(e)[:80]}")

    # Save comprehensive YAML
    print(f"\n{'='*100}")
    print("SAVING RESULTS")
    print(f"{'='*100}\n")

    yaml_output = {}
    for pair_name, data in all_results.items():
        source, target = pair_name.split("→")
        valid_tests = [t for t in data["test_cases"] if t["valid"]]

        if valid_tests:
            rotations = set(t["s2_rotation"] for t in valid_tests)
            s2_face = valid_tests[0]["s2_face"]
            rule = f"rotate_{list(rotations)[0]}(t) on {s2_face}" if len(rotations) == 1 else f"mixed: {rotations}"
        else:
            rule = "NO_VALID_TESTS"

        yaml_output[pair_name] = {
            "source_face": source,
            "target_face": target,
            "s2_derivation_rule": rule,
            "test_cases": [
                {
                    "target_point": t["target_point"],
                    "source_point": t["source_point"],
                    "s2_position": t["s2_position"],
                    "s2_face": t["s2_face"],
                    "s2_rotation": t["s2_rotation"],
                    "valid": t["valid"],
                }
                for t in data["test_cases"]
            ]
        }

    with open('/home/user/cubesolve/s2_analysis_comprehensive.yaml', 'w') as f:
        yaml.dump(yaml_output, f, default_flow_style=False, sort_keys=False)

    print(f"✅ Results saved to s2_analysis_comprehensive.yaml")

    # Print summary
    print(f"\n{'='*100}")
    print("SUMMARY OF RULES")
    print(f"{'='*100}\n")

    for pair_name in sorted(all_results.keys()):
        data = all_results[pair_name]
        valid_tests = [t for t in data["test_cases"] if t["valid"]]
        if valid_tests:
            rotations = set(t["s2_rotation"] for t in valid_tests)
            rule_str = list(rotations)[0] if len(rotations) == 1 else str(rotations)
            print(f"{pair_name:20} → s2 = rotate_{rule_str}(t) on {valid_tests[0]['s2_face']}")


if __name__ == "__main__":
    main()
