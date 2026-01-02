"""
Test s2 derivation for ALL 30 face pairs.

Based on the working approach:
1. Places markers on s1, t
2. Executes communicator
3. Tracks where marker_t moves to find s2
4. Records findings to lookup table
5. Determines s2 rule for each face pair
"""

import uuid
import yaml
from typing import Tuple, Dict, List, Any

from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver

Point = Tuple[int, int]

# All 30 face pairs
ALL_FACE_PAIRS = [
    ("UP", "FRONT"), ("UP", "BACK"), ("UP", "RIGHT"), ("UP", "LEFT"),
    ("DOWN", "FRONT"), ("DOWN", "BACK"), ("DOWN", "RIGHT"), ("DOWN", "LEFT"),
    ("FRONT", "UP"), ("FRONT", "DOWN"), ("FRONT", "RIGHT"), ("FRONT", "LEFT"),
    ("BACK", "UP"), ("BACK", "DOWN"), ("BACK", "RIGHT"), ("BACK", "LEFT"),
    ("RIGHT", "UP"), ("RIGHT", "DOWN"), ("RIGHT", "FRONT"), ("RIGHT", "BACK"),
    ("LEFT", "UP"), ("LEFT", "DOWN"), ("LEFT", "FRONT"), ("LEFT", "BACK"),
]


def test_3cycle_face_pair(source_name: str, target_name: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Test the full 3-cycle for a given source/target face pair.

    Returns dict with s2 derivation rule or error.
    """

    CUBE_SIZE = 5

    app = AbstractApp.create_non_default(cube_size=CUBE_SIZE, animation=False)
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

    # Test target positions
    target_positions = [(0, 0), (0, 1), (1, 0)]

    results = []

    for target_point in target_positions:
        try:
            cube.reset()

            # Get natural source point
            natural_source = helper.get_natural_source_ltr(source_face, target_face, target_point)
            source_point = natural_source
            target_block = (target_point, target_point)
            source_block = (source_point, source_point)

            # Create markers
            marker_s1_key = f"s1_{uuid.uuid4().hex[:4]}"
            marker_t_key = f"t_{uuid.uuid4().hex[:4]}"

            # Place markers on s1 and t
            source_piece = source_face.center.get_center_slice(source_point)
            source_piece.edge.c_attributes[marker_s1_key] = "S1_MARKER"

            target_piece_before = target_face.center.get_center_slice(target_point)
            target_piece_before.edge.c_attributes[marker_t_key] = "T_MARKER"

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
                    results.append({
                        "target_point": target_point,
                        "s2_position": None,
                        "s2_rotation": None,
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

            results.append({
                "target_point": target_point,
                "source_point": source_point,
                "s2_position": actual_s2,
                "s2_face": actual_s2_face,
                "s2_rotation": s2_rotation,
                "valid": actual_s2 is not None
            })

        except Exception as e:
            results.append({
                "target_point": target_point,
                "s2_position": None,
                "s2_rotation": None,
                "error": str(e)[:40]
            })

    # Extract rule from results
    valid_results = [r for r in results if r.get("valid", False)]

    if valid_results:
        rotations = set(r["s2_rotation"] for r in valid_results)
        s2_faces = set(r["s2_face"] for r in valid_results)

        if len(rotations) == 1 and len(s2_faces) == 1:
            rule = f"rotate_{list(rotations)[0]}(t) on {list(s2_faces)[0]}"
            return {
                "valid": True,
                "rule": rule,
                "rotation": list(rotations)[0],
                "s2_face": list(s2_faces)[0],
                "test_results": results
            }
        else:
            return {
                "valid": False,
                "error": f"MIXED: rotations={rotations}, faces={s2_faces}",
                "test_results": results
            }
    else:
        return {
            "valid": False,
            "error": "NO_VALID_RESULTS",
            "test_results": results
        }


def main():
    """Test all 30 face pairs and build lookup table."""

    print(f"\n{'='*100}")
    print(f"S2 DERIVATION LOOKUP TABLE - ALL 30 FACE PAIRS")
    print(f"{'='*100}\n")

    all_results = {}
    summary = {}

    for source, target in ALL_FACE_PAIRS:
        pair_name = f"{source}→{target}"
        print(f"Testing {pair_name:20}", end=" ", flush=True)

        result = test_3cycle_face_pair(source, target)
        all_results[pair_name] = result

        if result.get("valid"):
            summary[pair_name] = result["rule"]
            print(f"✅ {result['rule']}")
        else:
            summary[pair_name] = f"FAILED: {result.get('error', 'unknown')}"
            print(f"❌ {result.get('error', 'unknown')}")

    # Save full results
    with open('/home/user/cubesolve/s2_lookup_table_full.yaml', 'w') as f:
        # Convert for YAML
        yaml_data = {}
        for pair_name, result in all_results.items():
            yaml_data[pair_name] = {
                "valid": result.get("valid", False),
                "rule": result.get("rule"),
                "rotation": result.get("rotation"),
                "s2_face": result.get("s2_face"),
                "error": result.get("error"),
                "test_count": len(result.get("test_results", []))
            }
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    # Print summary
    print(f"\n{'='*100}")
    print("LOOKUP TABLE SUMMARY")
    print(f"{'='*100}\n")

    valid_count = sum(1 for r in all_results.values() if r.get("valid"))
    print(f"Valid results: {valid_count}/{len(ALL_FACE_PAIRS)}\n")

    for pair_name in sorted(all_results.keys()):
        result = all_results[pair_name]
        if result.get("valid"):
            print(f"{pair_name:20} → {result['rule']}")

    print(f"\n✅ Full results saved to s2_lookup_table_full.yaml")
    print(f"✅ Total: {valid_count} consistent rules out of {len(ALL_FACE_PAIRS)} face pairs\n")


if __name__ == "__main__":
    main()
