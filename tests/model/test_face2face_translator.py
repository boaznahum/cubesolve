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

from itertools import product
from typing import Iterator

import pytest

from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.model.FaceName import FaceName
from cube.domain.model.geometric.Face2FaceTranslator import Face2FaceTranslator, FaceTranslationResult
from cube.domain.model._elements import CenterSliceIndex
from cube.domain.model.PartSlice import CenterSlice
from tests.test_utils import _test_sp


# All face pairs (target, source) - 30 combinations (6 faces * 5 others)
def _get_face_pairs() -> list[tuple[FaceName, FaceName]]:
    """Generate all valid (target, source) face pairs."""
    all_faces = list(FaceName)
    return [(t, s) for t, s in product(all_faces, all_faces) if t != s]


FACE_PAIRS = _get_face_pairs()
CUBE_SIZES_WHOLE = [3, 5]
CUBE_SIZES_SLICE = [5]


def _face_pair_id(pair: tuple[FaceName, FaceName]) -> str:
    """Generate readable test ID for face pair."""
    return f"{pair[0].name}<-{pair[1].name}"


def verify_whole_cube_translation(
    cube: Cube,
    target_face: Face,
    source_face: Face,
    target_coord: CenterSliceIndex,
) -> None:
    """
    Verify whole-cube algorithm translation.

    Contract:
        1. Place marker at source_coord on source_face
        2. Apply whole_cube_alg
        3. Marker appears at target_coord on target_face
    """
    target_name = target_face.name
    source_name = source_face.name
    target_face = cube.face(target_name)
    source_face = cube.face(source_name)

    result = Face2FaceTranslator.translate_source_from_target(target_face, source_face, target_coord)
    source_coord = result.source_coord

    marker_value = f"WHOLE_{target_name}_{source_name}_{target_coord}"

    # Place marker at source_coord on source_face
    source_slice: CenterSlice = source_face.center.get_center_slice(source_coord)
    source_slice.edge.c_attributes["test_marker"] = marker_value

    # Apply whole-cube algorithm
    result.whole_cube_alg.play(cube)

    # Verify marker at target_coord on target_face
    target_face = cube.face(target_name)
    check_slice: CenterSlice = target_face.center.get_center_slice(target_coord)

    assert check_slice.edge.c_attributes.get("test_marker") == marker_value, (
        f"Whole-cube translation failed!\n"
        f"  Target: {target_name} target_coord={target_coord}\n"
        f"  Source: {source_name} source_coord={source_coord}\n"
        f"  Algorithm: {result.whole_cube_alg}\n"
        f"  Expected marker at {target_coord} on {target_name}\n"
        f"  Found: {check_slice.edge.c_attributes.get('test_marker')}"
    )


def verify_slice_translation(
    cube: Cube,
    target_face: Face,
    source_face: Face,
    target_coord: CenterSliceIndex,
) -> None:
    """
    Verify slice algorithm translation.

    Contract:
        1. Place marker at source_coord on source_face
        2. Apply slice algorithm
        3. Marker appears at target_coord on target_face
    """
    target_name = target_face.name
    source_name = source_face.name
    target_face = cube.face(target_name)
    source_face = cube.face(source_name)

    result = Face2FaceTranslator.translate_source_from_target(target_face, source_face, target_coord)
    source_coord = result.source_coord

    marker_value = f"SLICE_{target_name}_{source_name}_{target_coord}"

    # Place marker at source_coord on source_face
    source_slice: CenterSlice = source_face.center.get_center_slice(source_coord)
    source_slice.edge.c_attributes["test_marker"] = marker_value

    # Apply slice algorithm
    slice_alg = result.slice_algorithms[0].get_alg()
    slice_alg.play(cube)

    # Verify marker at target_coord on target_face
    target_face = cube.face(target_name)
    check_slice: CenterSlice = target_face.center.get_center_slice(target_coord)

    assert check_slice.edge.c_attributes.get("test_marker") == marker_value, (
        f"Slice translation failed!\n"
        f"  Target: {target_name} target_coord={target_coord}\n"
        f"  Source: {source_name} source_coord={source_coord}\n"
        f"  Algorithm: {slice_alg}\n"
        f"  Expected marker at {target_coord} on {target_name}\n"
        f"  Found: {check_slice.edge.c_attributes.get('test_marker')}"
    )


class TestWholeCubeAlgorithm:
    """Tests for translate() whole-cube algorithms."""

    @pytest.mark.parametrize("cube_size", CUBE_SIZES_WHOLE)
    @pytest.mark.parametrize("face_pair", FACE_PAIRS, ids=_face_pair_id)
    def test_face_pair(self, cube_size: int, face_pair: tuple[FaceName, FaceName]) -> None:
        """Test whole-cube algorithm for a specific face pair."""
        target_name, source_name = face_pair
        cube = Cube(cube_size, sp=_test_sp)

        target_face = cube.face(target_name)
        source_face = cube.face(source_name)

        for center_slice in target_face.center.all_slices:
            target_coord: CenterSliceIndex = center_slice.index

            verify_whole_cube_translation(
                cube, target_face, source_face, target_coord
            )

            cube.clear_c_attributes()


class TestSliceAlgorithm:
    """Tests for translate() slice algorithms."""

    @pytest.mark.parametrize("cube_size", CUBE_SIZES_SLICE)
    @pytest.mark.parametrize("face_pair", FACE_PAIRS, ids=_face_pair_id)
    def test_face_pair(self, cube_size: int, face_pair: tuple[FaceName, FaceName]) -> None:
        """Test slice algorithm for a specific face pair."""
        target_name, source_name = face_pair
        cube = Cube(cube_size, sp=_test_sp)

        target_face = cube.face(target_name)
        source_face = cube.face(source_name)

        for center_slice in target_face.center.all_slices:
            target_coord: CenterSliceIndex = center_slice.index

            verify_slice_translation(
                cube, target_face, source_face, target_coord
            )

            cube.clear_c_attributes()

    @pytest.mark.parametrize("cube_size", [5])
    @pytest.mark.parametrize("face_pair", [[FaceName.L, FaceName.U]], ids=_face_pair_id)
    def test_face_pair_4_single(self, cube_size: int, face_pair: tuple[FaceName, FaceName]) -> None:
        """Test slice algorithm for a specific face pair."""
        target_name, source_name = face_pair
        cube = Cube(cube_size, sp=_test_sp)

        target_face = cube.face(target_name)
        source_face = cube.face(source_name)

        for center_slice in target_face.center.all_slices:
            target_coord: CenterSliceIndex = center_slice.index

            verify_slice_translation(
                cube, target_face, source_face, target_coord
            )

            cube.clear_c_attributes()


class TestTranslateTargetFromSource:
    """Tests for translate_target_from_source - the inverse of translate_source_from_target."""

    @pytest.mark.parametrize("cube_size", CUBE_SIZES_SLICE)
    @pytest.mark.parametrize("face_pair", FACE_PAIRS, ids=_face_pair_id)
    def test_inverse_of_source_from_target(self, cube_size: int, face_pair: tuple[FaceName, FaceName]) -> None:
        """
        Verify translate_target_from_source is the inverse of translate_source_from_target.

        For each (target_face, source_face, target_coord):
        1. Get source_coord and slice_name from translate_source_from_target
        2. Call translate_target_from_source(source_face, target_face, source_coord, slice_name)
        3. Verify it returns the original target_coord
        """
        target_name, source_name = face_pair
        cube = Cube(cube_size, sp=_test_sp)

        target_face = cube.face(target_name)
        source_face = cube.face(source_name)

        for center_slice in target_face.center.all_slices:
            target_coord: CenterSliceIndex = center_slice.index

            # Get source_coord and slice_name from translate_source_from_target
            result = Face2FaceTranslator.translate_source_from_target(
                target_face, source_face, target_coord
            )
            source_coord = result.source_coord
            slice_name = result.slice_algorithms[0].whole_slice_alg.slice_name

            # Call the inverse function
            computed_target = Face2FaceTranslator.translate_target_from_source(
                source_face, target_face, source_coord, slice_name
            )

            assert computed_target == target_coord, (
                f"translate_target_from_source is not inverse!\n"
                f"  target_face={target_name}, source_face={source_name}\n"
                f"  target_coord={target_coord} -> source_coord={source_coord}\n"
                f"  translate_target_from_source returned {computed_target}\n"
                f"  expected {target_coord}\n"
                f"  slice_name={slice_name}"
            )
