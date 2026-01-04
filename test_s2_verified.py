#!/usr/bin/env python
"""Test to discover s2 position for each source/target face pair."""

import sys
sys.path.insert(0, '/home/user/cubesolve/src')

import uuid
from typing import Tuple
from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver

Point = Tuple[int, int]


def test_face_pair(source_name: str, target_name: str, cube_size: int = 5):
    """Test a single face pair."""

    print(f"\n{'='*80}")
    print(f"Testing {source_name} → {target_name} ({cube_size}x{cube_size})")
    print(f"{'='*80}\n")

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

    print(f"Cube size: {n_slices}x{n_slices}")

    # Test corner positions
    target_positions = [(0, 0), (0, n_slices - 1), (n_slices - 1, 0)]

    results = []

    for target_point in target_positions:
        cube.reset()
        source_point = helper.get_natural_source_ltr(source_face, target_face, target_point)

        # Create marker for target piece
        marker_t_key = f"t_{uuid.uuid4().hex[:4]}"
        target_piece = target_face.center.get_center_slice(target_point)
        target_piece.edge.c_attributes[marker_t_key] = "T_MARKER"

        print(f"  t={str(target_point):8} s1={str(source_point):8}  ", end="", flush=True)

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

                        # Determine rotation
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

        if actual_s2:
            print(f"→ s2={str(actual_s2):8} on {actual_s2_face:6} {s2_rotation:5} ✅")
            results.append({
                "target": target_point,
                "s2": actual_s2,
                "s2_face": actual_s2_face,
                "rotation": s2_rotation
            })
        else:
            print(f"→ NOT FOUND ❌")

    # Analyze pattern
    if results and len(results) > 0:
        valid_results = results
        rotations = [r["rotation"] for r in valid_results]
        s2_faces = set(r["s2_face"] for r in valid_results)

        print(f"\n  Pattern for {source_name}→{target_name}:")
        unique_rotations = set(rotations)
        if len(unique_rotations) == 1:
            print(f"    ✅ Consistent: s2 = rotate_{list(unique_rotations)[0]}(t) on {s2_faces}")
        else:
            print(f"    ⚠️  Mixed rotations: {unique_rotations}")
            for r in valid_results:
                print(f"       t={r['target']} → {r['rotation']} rotation")

    return results


def main():
    """Test key face pairs."""

    print("\n" + "="*80)
    print("S2 DERIVATION DISCOVERY")
    print("="*80)

    test_pairs = [
        ("UP", "FRONT"),
        ("UP", "RIGHT"),
        ("FRONT", "UP"),
    ]

    all_results = {}
    for source, target in test_pairs:
        try:
            results = test_face_pair(source, target)
            all_results[f"{source}→{target}"] = results
        except Exception as e:
            print(f"\n❌ FAILED: {source}→{target}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")

    for pair_name in test_pairs:
        key = f"{pair_name[0]}→{pair_name[1]}"
        if key in all_results and all_results[key]:
            print(f"✅ {key}: Successful")
        else:
            print(f"❌ {key}: No valid results")


if __name__ == "__main__":
    main()
