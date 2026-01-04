#!/usr/bin/env python
"""Focused s2 derivation validation across key face pairs and cube sizes."""

import sys
sys.path.insert(0, '/home/user/cubesolve/src')

import uuid
import yaml
from typing import Dict, Tuple, Any

from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver

Point = Tuple[int, int]

# Key face pairs representing each source face
KEY_PAIRS = [
    # UP as source
    ("UP", "FRONT"),
    ("UP", "RIGHT"),
    # DOWN as source
    ("DOWN", "FRONT"),
    ("DOWN", "RIGHT"),
    # FRONT as source
    ("FRONT", "UP"),
    ("FRONT", "RIGHT"),
    # BACK as source
    ("BACK", "UP"),
    ("BACK", "LEFT"),
    # RIGHT as source
    ("RIGHT", "UP"),
    ("RIGHT", "FRONT"),
    # LEFT as source
    ("LEFT", "UP"),
    ("LEFT", "FRONT"),
]

# Cube sizes to test (smaller set for focused validation)
CUBE_SIZES = [3, 5]


def test_pair(source_name: str, target_name: str, cube_size: int) -> Dict[str, Any]:
    """Test one source/target pair on a given cube size."""

    try:
        app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
        solver = CageNxNSolver(app.op)
        helper = CommunicatorHelper(solver)
        cube = app.cube

        faces = {
            "UP": cube.up, "DOWN": cube.down, "FRONT": cube.front,
            "BACK": cube.back, "RIGHT": cube.right, "LEFT": cube.left,
        }

        source_face = faces[source_name]
        target_face = faces[target_name]
        n_slices = cube.n_slices

        # Test position (0, 0)
        target_point = (0, 0)

        cube.reset()
        source_point = helper.get_natural_source_ltr(source_face, target_face, target_point)

        # Create marker
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

        # Find marker
        all_faces = [cube.front, cube.back, cube.up, cube.down, cube.left, cube.right]
        face_names = ["FRONT", "BACK", "UP", "DOWN", "LEFT", "RIGHT"]

        for face, face_name in zip(all_faces, face_names):
            for r in range(n_slices):
                for c in range(n_slices):
                    pos = (r, c)
                    piece = face.center.get_center_slice(pos)
                    if marker_t_key in piece.edge.c_attributes:
                        # Determine rotation
                        s2_cw = cube.cqr.rotate_point_clockwise(target_point)
                        s2_ccw = cube.cqr.rotate_point_counterclockwise(target_point)

                        if pos == s2_cw:
                            rotation = "CW"
                        elif pos == s2_ccw:
                            rotation = "CCW"
                        else:
                            rotation = "OTHER"

                        return {
                            "valid": True,
                            "s2_position": pos,
                            "s2_face": face_name,
                            "rotation": rotation,
                            "source_point": source_point,
                        }

        return {"valid": False, "error": "marker_not_found"}

    except Exception as e:
        error_msg = str(e)
        if "Intersection still exists" in error_msg:
            return {"valid": False, "error": "intersection"}
        else:
            return {"valid": False, "error": str(e)[:40]}


def main():
    """Run focused s2 validation."""

    print(f"\n{'='*100}")
    print(f"FOCUSED S2 DERIVATION VALIDATION")
    print(f"Testing {len(KEY_PAIRS)} key face pairs × {len(CUBE_SIZES)} cube sizes")
    print(f"{'='*100}\n")

    all_results = {}
    valid_count = 0
    total_count = 0

    for cube_size in CUBE_SIZES:
        print(f"{'='*100}")
        print(f"{cube_size}x{cube_size} CUBE")
        print(f"{'='*100}\n")

        cube_results = {}

        for source, target in KEY_PAIRS:
            pair_name = f"{source}→{target}"
            result = test_pair(source, target, cube_size)
            cube_results[pair_name] = result
            total_count += 1

            if result["valid"]:
                valid_count += 1
                print(f"{pair_name:20} ✅ s2={str(result['s2_position']):8} on {result['s2_face']:6} {result['rotation']:3}")
            elif result["error"] == "intersection":
                print(f"{pair_name:20} ⊘ Intersection error")
            else:
                print(f"{pair_name:20} ❌ {result['error']}")

        print()
        all_results[cube_size] = cube_results

    # Analyze consistency
    print(f"{'='*100}")
    print("CONSISTENCY ANALYSIS")
    print(f"{'='*100}\n")

    consistent = 0
    mixed = 0

    for source, target in KEY_PAIRS:
        pair_name = f"{source}→{target}"
        rotations = {}
        s2_faces = set()
        all_valid = True

        for cube_size in CUBE_SIZES:
            result = all_results[cube_size].get(pair_name, {})
            if result.get("valid"):
                rotations[cube_size] = result["rotation"]
                s2_faces.add(result["s2_face"])
            else:
                all_valid = False

        if all_valid and rotations:
            unique_rotations = set(rotations.values())
            if len(unique_rotations) == 1 and len(s2_faces) == 1:
                rotation = list(unique_rotations)[0]
                s2_face = list(s2_faces)[0]
                print(f"{pair_name:20} ✅ CONSISTENT: rotate_{rotation}(t) on {s2_face}")
                consistent += 1
            else:
                print(f"{pair_name:20} ⚠️  MIXED across cube sizes")
                mixed += 1

    # Save results
    yaml_data = {
        "validation_summary": {
            "total_tests": total_count,
            "valid_results": valid_count,
            "success_rate": f"{100*valid_count/total_count:.1f}%",
            "consistent_rules": consistent,
            "mixed_patterns": mixed,
        },
        "results_by_cube_size": {
            str(size): {
                pair_name: {
                    "valid": result["valid"],
                    "s2_position": result.get("s2_position"),
                    "s2_face": result.get("s2_face"),
                    "rotation": result.get("rotation"),
                    "error": result.get("error"),
                }
                for pair_name, result in all_results[size].items()
            }
            for size in CUBE_SIZES
        }
    }

    with open('/home/user/cubesolve/s2_focused_validation.yaml', 'w') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    # Summary
    print(f"\n{'='*100}")
    print("SUMMARY")
    print(f"{'='*100}\n")

    success_rate = 100 * valid_count / total_count if total_count > 0 else 0

    print(f"Total Tests:       {total_count}")
    print(f"Valid Results:     {valid_count} ({success_rate:.1f}%)")
    print(f"Consistent Rules:  {consistent}/{len(KEY_PAIRS)}")
    print(f"Mixed Patterns:    {mixed}")
    print(f"\n✅ Results saved to s2_focused_validation.yaml\n")


if __name__ == "__main__":
    main()
