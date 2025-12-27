"""
Comprehensive tests for Face2FaceTranslator.

DEFINITION (Viewer Perspective):
    translate(source_face, dest_face, coord) → FaceTranslationResult

    The result contains:
    - dest_coord: where to place marker on dest_face
    - whole_cube_alg: algorithm that brings dest_face to source_face's screen position

    Verification:
    1. Put marker at dest_coord on dest_face
    2. Execute whole_cube_alg (brings dest_face to source_face position)
    3. Marker now appears at coord on dest_face (same screen position as original)

TEST MATRIX:
    - All faces from cube.faces
    - All destinations (adjacent via edges + opposite)
    - Cube sizes: 3, 4, 5, 6, 7, 8
    - All center slices on each face (from face.center.all_slices)
"""

from __future__ import annotations

import pytest
from collections.abc import Iterator

from cube.domain.algs import Alg
from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.model.Face2FaceTranslator import Face2FaceTranslator, FaceTranslationResult
# noinspection PyProtectedMember
from cube.domain.model._part_slice import CenterSlice
# noinspection PyProtectedMember
from cube.domain.model._elements import CenterSliceIndex
from tests.test_utils import _test_sp


def execute_whole_cube_alg(cube: Cube, alg: Alg) -> None:
    """
    Execute a whole-cube algorithm (X, Y, Z moves only).

    Args:
        cube: The cube to rotate
        alg: Algorithm
    """

    alg.play(cube)


# Cube sizes to test
CUBE_SIZES: list[int] = [3, 4, 5, 6, 7, 8]


def get_all_dest_faces(source_face: Face) -> Iterator[Face]:
    """
    Get all destination faces for a source face.

    Yields:
        - 4 adjacent faces (via edges)
        - 1 opposite face
    """
    yield from source_face.others_faces


class TestFace2FaceTranslator:
    """
    Comprehensive test suite for face-to-face coordinate translation.

    Each test:
    1. Creates cube of given size
    2. For each source face, for each dest face, for each center slice:
       - Get translation result (dest_coord, whole_cube_alg)
       - Mark dest_coord on dest_face with c_attributes
       - Execute whole_cube_alg
       - Verify marker appears at original coord on dest_face
    """

    @pytest.mark.parametrize("cube_size", CUBE_SIZES)
    def test_all_face_pairs_all_positions(self, cube_size: int) -> None:
        """
        Test all positions on all face pairs translate correctly.
        """
        cube = Cube(cube_size, sp=_test_sp)

        for source_face in cube.faces:
            for dest_face in get_all_dest_faces(source_face):
                for center_slice in source_face.center.all_slices:
                    coord: CenterSliceIndex = center_slice.index
                    self._verify_single_translation(
                        cube, source_face, dest_face, coord
                    )
                    # Clear markers for next test (avoid stale object references from reset())
                    cube.clear_c_attributes()

    @staticmethod
    def _verify_single_translation(
            cube: Cube,
            source_face: Face,
            dest_face: Face,
            coord: CenterSliceIndex
    ) -> None:
        """
        Verify a single coordinate translation using the viewer-perspective test.

        Args:
            cube: The cube instance
            source_face: Face where the original coordinate is defined
            dest_face: Face we're translating to
            coord: (row, col) on source_face

        Test logic:
        1. Get translation result
        2. Place marker at dest_coord on dest_face
        3. Execute whole_cube_alg (brings dest_face to source_face's screen position)
        4. Marker should now be at coord on dest_face
        """
        row, col = coord

        # Step 1: Get translation (utility class - static method)
        result: FaceTranslationResult = Face2FaceTranslator.translate(source_face, dest_face, coord)

        # Step 2: Place marker at dest_coord on dest_face using c_attributes
        # c_attributes move with colors during whole cube rotations
        dest_row, dest_col = result.dest_coord
        marker_value: str = f"MARKER_{source_face.name}_{row}_{col}"
        dest_slice: CenterSlice = dest_face.center.get_center_slice((dest_row, dest_col))
        dest_slice.edge.c_attributes["test_marker"] = marker_value

        # Step 3: Execute whole cube algorithm (brings dest_face colors to source_face)
        execute_whole_cube_alg(cube, result.whole_cube_alg)

        # Step 4: After rotation, dest_face's colors are now on source_face.
        # The marker should appear at coord on source_face (same screen position).
        check_slice: CenterSlice = source_face.center.get_center_slice((row, col))

        assert check_slice.edge.c_attributes.get("test_marker") == marker_value, (
            f"Translation failed:\n"
            f"  Source: {source_face.name} coord=({row},{col})\n"
            f"  Dest: {dest_face.name} dest_coord={result.dest_coord}\n"
            f"  Algorithm: {result.whole_cube_alg}\n"
            f"  Expected marker '{marker_value}' at ({row},{col}) on {source_face.name}\n"
            f"  Found: {check_slice.edge.c_attributes.get('test_marker')}"
        )


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_translate_same_face_raises_error(self) -> None:
        """Translating from a face to itself should raise ValueError."""
        cube = Cube(3, sp=_test_sp)

        with pytest.raises(ValueError, match="Cannot translate from a face to itself"):
            Face2FaceTranslator.translate(cube.front, cube.front, (1, 1))

    @pytest.mark.parametrize("cube_size", CUBE_SIZES)
    def test_out_of_bounds_raises_error(self, cube_size: int) -> None:
        """Coordinates outside face bounds should raise ValueError."""
        cube = Cube(cube_size, sp=_test_sp)

        invalid_coords: list[tuple[int, int]] = [
            (-1, 0),
            (0, -1),
            (cube_size, 0),
            (0, cube_size),
            (cube_size, cube_size),
        ]

        for coord in invalid_coords:
            with pytest.raises(ValueError, match="out of bounds"):
                Face2FaceTranslator.translate(cube.front, cube.right, coord)


class TestRoundTrip:
    """Test that translating A→B→A returns the original coordinate."""

    @pytest.mark.parametrize("cube_size", [3, 5])
    def test_round_trip_returns_original(self, cube_size: int) -> None:
        """Translate A→B then B→A should return original coordinate."""
        cube = Cube(cube_size, sp=_test_sp)

        for source_face in cube.faces:
            for dest_face in get_all_dest_faces(source_face):
                for center_slice in source_face.center.all_slices:
                    coord: CenterSliceIndex = center_slice.index

                    # A → B
                    result1: FaceTranslationResult = Face2FaceTranslator.translate(
                        source_face, dest_face, coord
                    )

                    # B → A
                    result2: FaceTranslationResult = Face2FaceTranslator.translate(
                        dest_face, source_face, result1.dest_coord
                    )

                    assert result2.dest_coord == coord, (
                        f"Round-trip failed:\n"
                        f"  {source_face.name}({coord}) → {dest_face.name}({result1.dest_coord})\n"
                        f"  → {source_face.name}({result2.dest_coord})\n"
                        f"  Expected: {coord}"
                    )
