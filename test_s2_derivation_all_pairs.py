"""
Test to discover and validate the s2 derivation rule across all face pairs.

This test:
1. Tests each source/target face pair
2. Tracks markers to determine s2 position and rotation type
3. Captures on_front_rotate value from communicator
4. Builds comprehensive YAML table
5. Validates the rule: s2 = rotate_X(t) where X depends on on_front_rotate
"""

import uuid
import yaml
from typing import Tuple, Dict, List, Any

from cube.application.AbstractApp import AbstractApp
from cube.domain.model.geometric.cube_boy import FaceName
from cube.domain.model.Face import Face
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver

Point = Tuple[int, int]

# All 30 face pair combinations (6 faces * 5 possible targets per source)
FACE_PAIRS = [
    # source UP
    ("UP", "FRONT"),
    ("UP", "BACK"),
    ("UP", "RIGHT"),
    ("UP", "LEFT"),

    # source DOWN
    ("DOWN", "FRONT"),
    ("DOWN", "BACK"),
    ("DOWN", "RIGHT"),
    ("DOWN", "LEFT"),

    # source FRONT
    ("FRONT", "UP"),
    ("FRONT", "DOWN"),
    ("FRONT", "RIGHT"),
    ("FRONT", "LEFT"),

    # source BACK
    ("BACK", "UP"),
    ("BACK", "DOWN"),
    ("BACK", "RIGHT"),
    ("BACK", "LEFT"),

    # source RIGHT
    ("RIGHT", "UP"),
    ("RIGHT", "DOWN"),
    ("RIGHT", "FRONT"),
    ("RIGHT", "BACK"),

    # source LEFT
    ("LEFT", "UP"),
    ("LEFT", "DOWN"),
    ("LEFT", "FRONT"),
    ("LEFT", "BACK"),
]

# Map face names to Face objects
FACE_MAP = {
    "UP": None,  # Will be filled in
    "DOWN": None,
    "FRONT": None,
    "BACK": None,
    "RIGHT": None,
    "LEFT": None,
}

def get_on_front_rotate_from_communicator(helper, source_face, target_face, target_point):
    """Extract the on_front_rotate value from the communicator logic."""
    # Get the internal data by using dry_run
    result = helper.execute_communicator(
        source_face=source_face,
        target_face=target_face,
        target_block=(target_point, target_point),
        dry_run=True
    )
    # The internal data includes information about the rotation
    # We need to access the _secret field to get details
    if result._secret:
        # Get the trans_data which contains rotation information
        trans_data = result._secret.trans_data
        # The on_front_rotate is stored in the trans_data
        return trans_data.on_front_rotate if hasattr(trans_data, 'on_front_rotate') else None
    return None


def test_single_face_pair(source_face_name: str, target_face_name: str,
                          CUBE_SIZE: int = 5) -> List[Dict[str, Any]]:
    """Test a single source/target face pair and collect results."""

    app = AbstractApp.create_non_default(cube_size=CUBE_SIZE, animation=False)
    solver = CageNxNSolver(app.op)
    helper = CommunicatorHelper(solver)
    cube = app.cube

    # Get face objects
    face_map = {
        "UP": cube.up,
        "DOWN": cube.down,
        "FRONT": cube.front,
        "BACK": cube.back,
        "RIGHT": cube.right,
        "LEFT": cube.left,
    }

    source_face = face_map[source_face_name]
    target_face = face_map[target_face_name]
    n_slices = cube.n_slices

    # Test corner positions only (avoid center which causes intersection errors)
    target_positions = [
        (0, 0),  # Top-left
        (0, n_slices - 1),  # Top-right
        (n_slices - 1, 0),  # Bottom-left
        (n_slices - 1, n_slices - 1),  # Bottom-right
    ]

    results = []

    for target_point in target_positions:
        try:
            cube.reset()

            # Get source point using helper
            natural_source = helper.get_natural_source_ltr(source_face, target_face, target_point)
            source_point = natural_source

            # Create unique markers for each position in the 3-cycle
            marker_s1_key = f"s1_{uuid.uuid4().hex[:4]}"
            marker_s1_val = "S1_MARKER"
            marker_t_key = f"t_{uuid.uuid4().hex[:4]}"
            marker_t_val = "T_MARKER"

            # Place marker on s1 (source)
            source_piece = source_face.center.get_center_slice(source_point)
            source_piece.edge.c_attributes[marker_s1_key] = marker_s1_val

            # Place marker on t (target) BEFORE execution
            target_piece_before = target_face.center.get_center_slice(target_point)
            target_piece_before.edge.c_attributes[marker_t_key] = marker_t_val

            # Get s2 position BEFORE execution (we'll predict it)
            s2_cw = cube.cqr.rotate_point_clockwise(target_point)
            s2_ccw = cube.cqr.rotate_point_counterclockwise(target_point)

            # Try both positions for s2 marker placement
            # We'll place markers and see which one ends up at s1
            marker_s2_cw_key = f"s2_cw_{uuid.uuid4().hex[:4]}"
            marker_s2_ccw_key = f"s2_ccw_{uuid.uuid4().hex[:4]}"

            s2_cw_piece = target_face.center.get_center_slice(s2_cw)
            s2_cw_piece.edge.c_attributes[marker_s2_cw_key] = "S2_CW_MARKER"

            s2_ccw_piece = target_face.center.get_center_slice(s2_ccw)
            s2_ccw_piece.edge.c_attributes[marker_s2_ccw_key] = "S2_CCW_MARKER"

            # Execute communicator
            target_block = (target_point, target_point)
            source_block = (source_point, source_point)

            alg = helper.do_communicator(
                source_face=source_face,
                target_face=target_face,
                target_block=target_block,
                source_block=source_block,
                preserve_state=True
            )

            # Find where marker_t moved (to find s2)
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

                            # Determine rotation type
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

            # Try to get on_front_rotate value
            on_front_rotate = get_on_front_rotate_from_communicator(
                helper, source_face, target_face, target_point
            )

            result = {
                "target_point": target_point,
                "source_point": source_point,
                "s2_position": actual_s2,
                "s2_face": actual_s2_face,
                "s2_rotation": s2_rotation,
                "on_front_rotate": on_front_rotate,
                "valid": actual_s2 is not None,
            }
            results.append(result)

        except Exception as e:
            # Skip this target position on error
            result = {
                "target_point": target_point,
                "source_point": None,
                "s2_position": None,
                "s2_face": None,
                "s2_rotation": None,
                "on_front_rotate": None,
                "valid": False,
                "error": str(e),
            }
            results.append(result)

    return results


def main():
    """Test all face pairs and build comprehensive table."""

    print(f"\n{'='*100}")
    print("S2 DERIVATION RULE DISCOVERY - ALL FACE PAIRS")
    print(f"{'='*100}\n")

    all_results = {}

    # Test a few key pairs first
    test_pairs = [
        ("UP", "FRONT"),
        ("UP", "RIGHT"),
        ("FRONT", "UP"),
        ("FRONT", "RIGHT"),
    ]

    for source, target in test_pairs:
        pair_name = f"{source}→{target}"
        print(f"\nTesting {pair_name}...", flush=True)

        try:
            results = test_single_face_pair(source, target)
            all_results[pair_name] = results

            print(f"  Results for {pair_name}:")
            for r in results:
                status = "✅" if r['valid'] else "❌"
                rotation = r.get('s2_rotation', 'N/A')
                on_front = r.get('on_front_rotate', 'N/A')
                print(f"    {status} t={r['target_point']} → s2={r['s2_position']} "
                      f"(on_source={r['s2_face']}, rotation={rotation}, on_front_rotate={on_front})")
        except Exception as e:
            print(f"  ⚠️  Error testing {pair_name}: {e}")
            all_results[pair_name] = []

    # Analyze patterns
    print(f"\n{'='*100}")
    print("PATTERN ANALYSIS")
    print(f"{'='*100}\n")

    for pair_name, results in all_results.items():
        if not results:
            continue

        # Check consistency
        rotations = [r['s2_rotation'] for r in results if r['valid']]
        on_fronts = [r['on_front_rotate'] for r in results if r['valid']]

        if rotations:
            # Correlate on_front_rotate with rotation type
            rot_dict = {}
            for r in results:
                if r['valid'] and r['on_front_rotate'] is not None:
                    on_front = r['on_front_rotate']
                    rotation = r['s2_rotation']
                    if on_front not in rot_dict:
                        rot_dict[on_front] = []
                    rot_dict[on_front].append(rotation)

            print(f"{pair_name}:")
            for on_front in sorted(rot_dict.keys()):
                rotations = set(rot_dict[on_front])
                print(f"  on_front_rotate={on_front:2d} → s2 rotation: {rotations}")

            # Check if s2 is always on source face
            s2_faces = set(r['s2_face'] for r in results if r['valid'])
            print(f"  s2 always on: {s2_faces}")
            print()

    # Save YAML summary
    yaml_data = {}
    for pair_name, results in all_results.items():
        source, target = pair_name.split("→")
        yaml_data[pair_name] = {
            "source_face": source,
            "target_face": target,
            "test_cases": [
                {
                    "target_point": r['target_point'],
                    "source_point": r['source_point'],
                    "s2_position": r['s2_position'],
                    "s2_face": r['s2_face'],
                    "s2_rotation": r['s2_rotation'],
                    "on_front_rotate": r['on_front_rotate'],
                    "valid": r['valid'],
                }
                for r in results
            ]
        }

    with open('/home/user/cubesolve/s2_analysis_all_pairs.yaml', 'w') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    print(f"\n✅ Full analysis saved to s2_analysis_all_pairs.yaml")


if __name__ == "__main__":
    main()
