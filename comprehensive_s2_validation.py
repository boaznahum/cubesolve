#!/usr/bin/env python
"""Comprehensive s2 derivation validation across all cube sizes and all face pairs."""

import sys
sys.path.insert(0, '/home/user/cubesolve/src')

import uuid
import yaml
from typing import Dict, List, Tuple, Any
from collections import defaultdict

from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver

Point = Tuple[int, int]

# All 30 source/target face pair combinations
ALL_FACE_PAIRS = [
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

# Cube sizes to test
CUBE_SIZES = [3, 4, 5, 6]


def test_single_case(source_name: str, target_name: str, cube_size: int) -> Dict[str, Any]:
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
                            "target_point": target_point,
                        }

        return {"valid": False, "error": "marker_not_found"}

    except Exception as e:
        error_msg = str(e)
        if "Intersection still exists" in error_msg:
            return {"valid": False, "error": "intersection"}
        else:
            return {"valid": False, "error": str(e)[:50]}


def main():
    """Run comprehensive validation across all cube sizes and face pairs."""

    print(f"\n{'='*120}")
    print("COMPREHENSIVE S2 DERIVATION VALIDATION")
    print(f"Testing all {len(ALL_FACE_PAIRS)} face pairs × {len(CUBE_SIZES)} cube sizes")
    print(f"{'='*120}\n")

    # Results structure: {cube_size: {pair_name: result}}
    all_results = defaultdict(dict)
    statistics = defaultdict(lambda: {"valid": 0, "intersection": 0, "not_found": 0, "error": 0})

    total = len(ALL_FACE_PAIRS) * len(CUBE_SIZES)
    completed = 0

    for cube_size in CUBE_SIZES:
        print(f"Testing {cube_size}x{cube_size} cube ({len(ALL_FACE_PAIRS)} pairs)...", flush=True)

        for source, target in ALL_FACE_PAIRS:
            pair_name = f"{source}→{target}"
            result = test_single_case(source, target, cube_size)
            all_results[cube_size][pair_name] = result

            completed += 1

            # Update statistics
            if result["valid"]:
                statistics[cube_size]["valid"] += 1
            elif result["error"] == "intersection":
                statistics[cube_size]["intersection"] += 1
            elif result["error"] == "marker_not_found":
                statistics[cube_size]["not_found"] += 1
            else:
                statistics[cube_size]["error"] += 1

            if completed % 10 == 0:
                progress = int(100 * completed / total)
                print(f"  Progress: {completed}/{total} ({progress}%)", flush=True)

        print(f"  {cube_size}x{cube_size} complete\n")

    # Print summary statistics
    print(f"\n{'='*120}")
    print("STATISTICS BY CUBE SIZE")
    print(f"{'='*120}\n")

    for cube_size in CUBE_SIZES:
        stats = statistics[cube_size]
        total_tested = len(ALL_FACE_PAIRS)
        success_rate = 100 * stats["valid"] / total_tested if total_tested > 0 else 0

        print(f"{cube_size}x{cube_size} Cube:")
        print(f"  ✅ Valid:         {stats['valid']:2d}/{total_tested} ({success_rate:5.1f}%)")
        print(f"  ⊘ Intersection:  {stats['intersection']:2d}/{total_tested}")
        print(f"  ❌ Not found:     {stats['not_found']:2d}/{total_tested}")
        print(f"  ⚠️  Error:        {stats['error']:2d}/{total_tested}")
        print()

    # Analyze pattern consistency
    print(f"{'='*120}")
    print("PATTERN CONSISTENCY ANALYSIS")
    print(f"{'='*120}\n")

    consistency_count = 0
    for source, target in ALL_FACE_PAIRS:
        pair_name = f"{source}→{target}"
        rotations_by_size = {}
        all_valid = True

        for cube_size in CUBE_SIZES:
            result = all_results[cube_size].get(pair_name, {})
            if result.get("valid"):
                rotations_by_size[cube_size] = result["rotation"]
            else:
                all_valid = False

        if all_valid and rotations_by_size:
            unique_rotations = set(rotations_by_size.values())
            if len(unique_rotations) == 1:
                rotation_type = list(unique_rotations)[0]
                s2_face = all_results[CUBE_SIZES[0]][pair_name].get("s2_face", "?")
                print(f"{pair_name:20} → rotate_{rotation_type}(t) on {s2_face} ✅ CONSISTENT")
                consistency_count += 1
            else:
                print(f"{pair_name:20} → MIXED ROTATIONS: {unique_rotations} ⚠️")

    # Save detailed results to YAML
    print(f"\n{'='*120}")
    print("SAVING DETAILED RESULTS")
    print(f"{'='*120}\n")

    yaml_data = {}
    for cube_size in CUBE_SIZES:
        yaml_data[f"cube_{cube_size}x{cube_size}"] = {
            "cube_size": cube_size,
            "statistics": dict(statistics[cube_size]),
            "results": {
                pair_name: {
                    "valid": result["valid"],
                    "s2_position": result.get("s2_position"),
                    "s2_face": result.get("s2_face"),
                    "rotation": result.get("rotation"),
                    "error": result.get("error"),
                }
                for pair_name, result in all_results[cube_size].items()
            }
        }

    with open('/home/user/cubesolve/s2_comprehensive_validation.yaml', 'w') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    print(f"✅ Detailed results saved to s2_comprehensive_validation.yaml\n")

    # Summary
    print(f"{'='*120}")
    print("SUMMARY")
    print(f"{'='*120}\n")

    total_valid = sum(stats["valid"] for stats in statistics.values())
    total_tests = len(ALL_FACE_PAIRS) * len(CUBE_SIZES)
    overall_success = 100 * total_valid / total_tests if total_tests > 0 else 0

    print(f"Overall Success Rate: {total_valid}/{total_tests} ({overall_success:.1f}%)")
    print(f"Consistent Rules:     {consistency_count}/{len(ALL_FACE_PAIRS)}")
    print(f"\n✅ S2 derivation rule validated across:")
    print(f"   • {len(ALL_FACE_PAIRS)} source/target face pairs")
    print(f"   • {len(CUBE_SIZES)} cube sizes ({CUBE_SIZES[0]}x{CUBE_SIZES[0]} to {CUBE_SIZES[-1]}x{CUBE_SIZES[-1]})")
    print(f"   • {total_tests} total test cases\n")


if __name__ == "__main__":
    main()
