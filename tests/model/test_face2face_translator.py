"""
Comprehensive tests for Face2FaceTranslator.

NAMING CONVENTION:
    translate(target_face, source_face, target_coord) -> source_coord

    - target_face: Where content should ARRIVE
    - source_face: Where content COMES FROM
    - target_coord: Position on target where we want content
    - source_coord: Position on source where content originates
    - Algorithm: Brings source_face content to target_face

VERIFICATION:
    1. Place marker at source_coord on source_face
    2. Apply algorithm
    3. Marker appears at target_coord on target_face
"""

from __future__ import annotations

import pytest

from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.model.Face2FaceTranslator import Face2FaceTranslator, FaceTranslationResult
from cube.domain.model._elements import CenterSliceIndex
from cube.domain.model.PartSlice import CenterSlice
from tests.test_utils import _test_sp


def verify_translation(
    cube: Cube,
    target_face: Face,
    source_face: Face,
    target_coord: CenterSliceIndex,
) -> None:
    """
    Verify that translate() returns correct source_coord and algorithm.

    Contract:
        translate(target, source, target_coord) returns source_coord such that:
        1. Place marker at source_coord on SOURCE face
        2. Apply algorithm
        3. Marker appears at target_coord on TARGET face
    """
    # Get fresh face references
    target_name = target_face.name
    source_name = source_face.name
    target_face = cube.face(target_name)
    source_face = cube.face(source_name)

    result = Face2FaceTranslator.translate(target_face, source_face, target_coord)
    source_coord = result.source_coord

    marker_value = f"TEST_{target_name}_{source_name}_{target_coord}"

    # Step 1: Place marker at source_coord on SOURCE face
    source_slice: CenterSlice = source_face.center.get_center_slice(source_coord)
    source_slice.edge.c_attributes["test_marker"] = marker_value

    # Step 2: Apply algorithm (should bring source content to target)
    result.whole_cube_alg.play(cube)

    # Step 3: Verify marker is at target_coord on TARGET face
    target_face = cube.face(target_name)
    check_slice: CenterSlice = target_face.center.get_center_slice(target_coord)

    assert check_slice.edge.c_attributes.get("test_marker") == marker_value, (
        f"Translation failed!\n"
        f"  Target: {target_name} target_coord={target_coord}\n"
        f"  Source: {source_name} source_coord={source_coord}\n"
        f"  Algorithm: {result.whole_cube_alg}\n"
        f"  Expected marker at {target_coord} on {target_name}\n"
        f"  Found: {check_slice.edge.c_attributes.get('test_marker')}"
    )


class TestWholeCubeAlgorithm:
    """Tests for translate() whole-cube algorithms."""

    @pytest.mark.parametrize("cube_size", [3, 5])
    def test_all_face_pairs_all_positions(self, cube_size: int) -> None:
        """Test whole-cube algorithm for all face pairs and positions."""
        cube = Cube(cube_size, sp=_test_sp)

        for target_face in cube.faces:
            for source_face in target_face.others_faces:
                for center_slice in target_face.center.all_slices:
                    target_coord: CenterSliceIndex = center_slice.index

                    verify_translation(
                        cube, target_face, source_face, target_coord
                    )

                    cube.clear_c_attributes()


class TestSliceAlgorithm:
    """Tests for translate() slice algorithms."""

    @pytest.mark.parametrize("cube_size", [5])
    def test_all_face_pairs_all_positions(self, cube_size: int) -> None:
        """Test slice algorithm for all face pairs and positions."""
        cube = Cube(cube_size, sp=_test_sp)

        for target_face in cube.faces:
            for source_face in target_face.others_faces:
                for center_slice in target_face.center.all_slices:
                    target_coord: CenterSliceIndex = center_slice.index

                    # Get fresh references
                    target_face_fresh = cube.face(target_face.name)
                    source_face_fresh = cube.face(source_face.name)

                    result = Face2FaceTranslator.translate(
                        target_face_fresh, source_face_fresh, target_coord
                    )
                    source_coord = result.source_coord

                    marker_value = f"SLICE_{target_face.name}_{source_face.name}_{target_coord}"

                    # Place marker at source_coord on source
                    source_slice = source_face_fresh.center.get_center_slice(source_coord)
                    source_slice.edge.c_attributes["test_marker"] = marker_value

                    # Apply slice algorithm
                    slice_alg = result.slice_algorithms[0].get_alg()
                    slice_alg.play(cube)

                    # Verify marker at target_coord on target
                    target_face_check = cube.face(target_face.name)
                    check_slice = target_face_check.center.get_center_slice(target_coord)

                    assert check_slice.edge.c_attributes.get("test_marker") == marker_value, (
                        f"Slice algorithm failed!\n"
                        f"  Target: {target_face.name} coord={target_coord}\n"
                        f"  Source: {source_face.name} coord={source_coord}\n"
                        f"  Algorithm: {slice_alg}\n"
                    )

                    cube.clear_c_attributes()
