#!/usr/bin/env python
"""Based on working test_marker_tracking.py - test multiple face pairs."""

import sys
sys.path.insert(0, '/home/user/cubesolve/src')

import uuid
import yaml
from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver

# Define face pairs to test
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

def test_pair(source_name, target_name):
    """Test one source/target pair."""

    # Use same setup as test_marker_tracking.py
    CUBE_SIZE = 5
    app = AbstractApp.create_non_default(cube_size=CUBE_SIZE, animation=False)
    solver = CageNxNSolver(app.op)
    helper = CommunicatorHelper(solver)
    cube = app.cube

    n_slices = cube.n_slices

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

    # Test one position
    target_point = (0, 0)

    print(f"\nTesting {source_name}→{target_name}...", flush=True)

    cube.reset()

    source_point = helper.get_natural_source_ltr(source_face, target_face, target_point)

    # Create marker
    marker_t_key = f"t_{uuid.uuid4().hex[:4]}"
    marker_t_val = "T_MARKER"

    # Place marker on t (target) - BEFORE execution
    target_piece_before = target_face.center.get_center_slice(target_point)
    target_piece_before.edge.c_attributes[marker_t_key] = marker_t_val

    # Execute communicator
    try:
        alg = helper.do_communicator(
            source_face=source_face,
            target_face=target_face,
            target_block=(target_point, target_point),
            source_block=(source_point, source_point),
            preserve_state=True
        )

        # Now check where marker is
        all_faces = [cube.front, cube.back, cube.up, cube.down, cube.left, cube.right]
        face_names = ["FRONT", "BACK", "UP", "DOWN", "LEFT", "RIGHT"]

        actual_s2 = None
        actual_s2_face = None

        for face, face_name in zip(all_faces, face_names):
            for search_row in range(n_slices):
                for search_col in range(n_slices):
                    search_point = (search_row, search_col)
                    search_piece = face.center.get_center_slice(search_point)
                    if marker_t_key in search_piece.edge.c_attributes:
                        actual_s2 = search_point
                        actual_s2_face = face_name

                        # Determine rotation type
                        s2_cw = cube.cqr.rotate_point_clockwise(target_point)
                        s2_ccw = cube.cqr.rotate_point_counterclockwise(target_point)

                        if search_point == s2_cw:
                            rotation = "CW"
                        elif search_point == s2_ccw:
                            rotation = "CCW"
                        else:
                            rotation = "OTHER"

                        print(f"  t={target_point} → s2={actual_s2} on {actual_s2_face} ({rotation}) ✅")
                        return {
                            "valid": True,
                            "s2_position": actual_s2,
                            "s2_face": actual_s2_face,
                            "rotation": rotation,
                            "source_point": source_point
                        }

        print(f"  t={target_point} → marker not found ❌")
        return {"valid": False}

    except Exception as e:
        if "Intersection" in str(e):
            print(f"  t={target_point} → intersection error (center pos)")
        else:
            print(f"  ERROR: {str(e)[:60]}")
        return {"valid": False}


def main():
    """Test all face pairs."""

    print(f"\n{'='*90}")
    print("S2 DERIVATION PATTERN DISCOVERY")
    print(f"{'='*90}")

    all_results = {}

    for source, target in FACE_PAIRS:
        pair_name = f"{source}→{target}"
        result = test_pair(source, target)
        all_results[pair_name] = result

    # Print summary
    print(f"\n{'='*90}")
    print("SUMMARY")
    print(f"{'='*90}\n")

    for pair_name in sorted(all_results.keys()):
        result = all_results[pair_name]
        if result["valid"]:
            print(f"{pair_name:20} → s2=rotate_{result['rotation']}(t) on {result['s2_face']}")
        else:
            print(f"{pair_name:20} → no valid result")

    # Save YAML
    yaml_data = {}
    for pair_name, result in all_results.items():
        source, target = pair_name.split("→")
        if result["valid"]:
            rule = f"rotate_{result['rotation']}(t) on {result['s2_face']}"
        else:
            rule = "NOT_TESTED"

        yaml_data[pair_name] = {
            "source": source,
            "target": target,
            "rule": rule,
            "s2": result.get("s2_position"),
            "s2_face": result.get("s2_face"),
            "rotation": result.get("rotation"),
            "valid": result.get("valid", False)
        }

    with open('/home/user/cubesolve/s2_patterns.yaml', 'w') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    print(f"\n✅ Results saved to s2_patterns.yaml")


if __name__ == "__main__":
    main()
