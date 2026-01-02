#!/usr/bin/env python
"""Simple test to discover s2 pattern for key face pairs."""

import sys
sys.path.insert(0, '/home/user/cubesolve/src')

import uuid
from typing import Tuple, Dict, Any

from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver

Point = Tuple[int, int]


def test_face_pair(source_name: str, target_name: str) -> Dict[str, Any]:
    """Test a single face pair and discover s2 pattern."""

    print(f"\n{'='*80}")
    print(f"Testing {source_name} → {target_name}")
    print(f"{'='*80}")

    app = AbstractApp.create_non_default(cube_size=5, animation=False)
    solver = CageNxNSolver(app.op)
    helper = CommunicatorHelper(solver)
    cube = app.cube

    # Map face names to objects
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

    # Test a few corner positions (skip center positions if odd-sized cube)
    # For 5x5: corners are (0,0), (0,4), (4,0), (4,4)
    # For 3x3: corners are (0,0), (0,2), (2,0), (2,2)
    test_positions = []

    if n_slices >= 3:
        test_positions.append((0, 0))  # Top-left
        if n_slices > 2:
            test_positions.append((0, n_slices - 1))  # Top-right
            test_positions.append((n_slices - 1, 0))  # Bottom-left
            if n_slices > 3:
                test_positions.append((n_slices - 1, n_slices - 1))  # Bottom-right

    pair_results = {
        "source": source_name,
        "target": target_name,
        "tests": []
    }

    for target_point in test_positions:
        try:
            cube.reset()

            # Get source point
            natural_source = helper.get_natural_source_ltr(source_face, target_face, target_point)
            source_point = natural_source

            # Create marker for target piece
            marker_t_key = f"t_{uuid.uuid4().hex[:4]}"
            target_piece = target_face.center.get_center_slice(target_point)
            target_piece.edge.c_attributes[marker_t_key] = "T_MARKER"

            # Compute s2 positions
            s2_cw = cube.cqr.rotate_point_clockwise(target_point)
            s2_ccw = cube.cqr.rotate_point_counterclockwise(target_point)

            # Execute communicator
            alg = helper.do_communicator(
                source_face=source_face,
                target_face=target_face,
                target_block=(target_point, target_point),
                source_block=(source_point, source_point),
                preserve_state=False  # Don't preserve - we want to see the actual 3-cycle
            )

            # Find where marker_t ended up
            actual_s2 = None
            actual_s2_face = None
            s2_rotation = None

            all_faces = [cube.front, cube.back, cube.up, cube.down, cube.left, cube.right]
            face_names = ["FRONT", "BACK", "UP", "DOWN", "LEFT", "RIGHT"]

            # DEBUG: Print what's at target position on target face
            target_after = target_face.center.get_center_slice(target_point)
            print(f"  [DEBUG] Alg: {alg}")
            print(f"  [DEBUG] Target pos after comm: {target_after.edge.c_attributes}")

            for face, face_name in zip(all_faces, face_names):
                found = False
                for r in range(n_slices):
                    for c in range(n_slices):
                        pos = (r, c)
                        piece = face.center.get_center_slice(pos)
                        if marker_t_key in piece.edge.c_attributes:
                            actual_s2 = pos
                            actual_s2_face = face_name
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

            # DEBUG: If not found, search more carefully
            if not actual_s2:
                for face, face_name in zip(all_faces, face_names):
                    for r in range(n_slices):
                        for c in range(n_slices):
                            pos = (r, c)
                            piece = face.center.get_center_slice(pos)
                            if piece.edge.c_attributes and any(marker_t_key in k for k in piece.edge.c_attributes.keys()):
                                print(f"  [DEBUG] Found marker-like at {face_name} {pos}: {piece.edge.c_attributes}")

            # Display result
            if actual_s2:
                print(f"  t={str(target_point):9} → s2={str(actual_s2):9} on {actual_s2_face:6} "
                      f"rotation={s2_rotation} ✅")
                pair_results["tests"].append({
                    "target": target_point,
                    "source": source_point,
                    "s2": actual_s2,
                    "s2_face": actual_s2_face,
                    "rotation": s2_rotation,
                    "valid": True
                })
            else:
                print(f"  t={str(target_point):9} → NOT FOUND ❌")
                pair_results["tests"].append({
                    "target": target_point,
                    "source": source_point,
                    "s2": None,
                    "s2_face": None,
                    "rotation": None,
                    "valid": False
                })

        except Exception as e:
            print(f"  t={str(target_point):9} → ERROR: {str(e)[:40]} ❌")
            pair_results["tests"].append({
                "target": target_point,
                "source": source_point,
                "s2": None,
                "s2_face": None,
                "rotation": None,
                "valid": False,
                "error": str(e)
            })

    return pair_results


def main():
    """Test key face pairs."""

    print("\n" + "="*80)
    print("S2 DERIVATION PATTERN DISCOVERY")
    print("="*80)

    test_pairs = [
        ("UP", "FRONT"),
        ("UP", "RIGHT"),
        ("FRONT", "UP"),
        ("FRONT", "RIGHT"),
    ]

    all_results = {}
    for source, target in test_pairs:
        try:
            result = test_face_pair(source, target)
            all_results[f"{source}→{target}"] = result
        except Exception as e:
            print(f"\n❌ FAILED to test {source}→{target}: {e}")

    # Analyze patterns
    print(f"\n{'='*80}")
    print("PATTERN ANALYSIS")
    print(f"{'='*80}\n")

    for pair_name, data in all_results.items():
        if not data["tests"]:
            continue

        valid_tests = [t for t in data["tests"] if t["valid"]]
        if valid_tests:
            rotations = [t["rotation"] for t in valid_tests]
            s2_faces = set(t["s2_face"] for t in valid_tests)

            # Check consistency
            unique_rotations = set(rotations)
            if len(unique_rotations) == 1:
                print(f"✅ {pair_name}: Consistent rule s2 = rotate_{list(unique_rotations)[0]}(t) on {s2_faces}")
            else:
                print(f"⚠️  {pair_name}: Multiple rotation types {unique_rotations}")
                for t in valid_tests:
                    print(f"      t={t['target']} → rotate_{t['rotation']}(t) on {t['s2_face']}")


if __name__ == "__main__":
    main()
