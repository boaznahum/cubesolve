"""
Comprehensive tests for Face2FaceTranslator.

Tests both:
1. translate() - returns whole-cube algorithm (X, Y, Z)
2. get_slice_algorithm() - returns slice algorithm(s) (M, E, S)

Both methods return algorithm(s) that bring content from dest_face to source_face.

VERIFICATION APPROACH:
    1. Place marker at coord on SOURCE
    2. Apply INVERSE algorithm to find where marker ends up on DEST
    3. Reset cube, place marker at discovered dest_coord on DEST
    4. Apply algorithm
    5. Verify marker is at coord on SOURCE

TEST MATRIX:
    - All faces from cube.faces
    - All destinations (adjacent + opposite)
    - Cube sizes: 3-8 for whole-cube, 5-7 for slice (need inner slices)
    - Both algorithm types: whole-cube and slice
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from enum import Enum, auto

import pytest

from cube.domain.algs.Alg import Alg
from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.model.Face2FaceTranslator import Face2FaceTranslator, FaceTranslationResult
# noinspection PyProtectedMember
from cube.domain.model._elements import CenterSliceIndex
# noinspection PyProtectedMember
from cube.domain.model.PartSlice import CenterSlice
from tests.test_utils import _test_sp


class AlgorithmType(Enum):
    """Type of algorithm being tested."""
    WHOLE_CUBE = auto()  # X, Y, Z rotations
    SLICE = auto()       # M, E, S slice moves


def get_all_dest_faces(source_face: Face) -> Iterator[Face]:
    """Get all destination faces for a source face (4 adjacent + 1 opposite)."""
    yield from source_face.others_faces


def get_algorithms(
    source_face: Face,
    dest_face: Face,
    coord: CenterSliceIndex
) -> FaceTranslationResult:
    """
    Get algorithm(s) that bring content from dest_face to source_face at coord.

    Args:
        source_face: Where we want the content to arrive
        dest_face: Where the content originates
        coord: Position on source_face
        alg_type: WHOLE_CUBE or SLICE

    Returns:
        List of algorithms (1 for whole-cube, 1-2 for slice depending on adjacency)
    """
    result: FaceTranslationResult = Face2FaceTranslator.translate(source_face, dest_face, coord)
    return result


def verify_algorithm(
    cube: Cube,
    source_face: Face,
    dest_face: Face,
    coord: CenterSliceIndex,
    alg: Alg
) -> None:
    """
    Verify that applying the algorithm brings dest content to source position.

    Definition: translate(source, dest, coord) returns dest_coord such that:
    1. Place marker at dest_coord on DEST face
    2. Apply algorithm
    3. Marker appears at coord on SOURCE face

    Args:
        cube: The cube instance
        source_face: Face where we want content to arrive (may be stale after reset)
        dest_face: Face where content originates (may be stale after reset)
        coord: (row, col) position on source_face
        alg: The algorithm to verify
        alg_type: Type of algorithm (for error messages)
    """
    row, col = coord

    # Get fresh face references (may be stale after cube.reset())
    source_name = source_face.name
    dest_name = dest_face.name
    source_face = cube.face(source_name)
    dest_face = cube.face(dest_name)

    # Get dest_coord from translate()
    result = Face2FaceTranslator.translate(source_face, dest_face, coord)
    dest_coord = result.dest_coord

    marker_value: str = f"TEST_{alg}_{source_name}_{row}_{col}"

    # Step 1: Place marker at dest_coord on DEST face
    dest_slice: CenterSlice = dest_face.center.get_center_slice(dest_coord)
    dest_slice.edge.c_attributes["test_marker"] = marker_value

    # Step 2: Apply algorithm
    alg.play(cube)

    # Step 3: Verify marker is at coord on SOURCE face
    # Get fresh reference - face objects move after rotation
    source_face = cube.face(source_name)
    check_slice: CenterSlice = source_face.center.get_center_slice(coord)

    assert check_slice.edge.c_attributes.get("test_marker") == marker_value, (
        f"  Source: {source_name} coord=({row},{col})\n"
        f"  Dest: {dest_name} dest_coord={dest_coord}\n"
        f"  Algorithm: {alg}\n"
        f"  Expected marker at ({row},{col}) on {source_name}\n"
        f"  Found: {check_slice.edge.c_attributes.get('test_marker')}"
    )


# =============================================================================
# WHOLE CUBE ALGORITHM TESTS
# =============================================================================

WHOLE_CUBE_SIZES: list[int] = [3, 4, 5, 6, 7, 8]


class TestWholeCubeAlgorithm:
    """Tests for translate() which returns whole-cube algorithms."""

    @pytest.mark.parametrize("cube_size", WHOLE_CUBE_SIZES)
    def test_all_face_pairs_all_positions(self, cube_size: int) -> None:
        """Test all positions on all face pairs with whole-cube algorithm."""
        cube = Cube(cube_size, sp=_test_sp)

        for source_face in cube.faces:
            for dest_face in get_all_dest_faces(source_face):
                for center_slice in source_face.center.all_slices:
                    coord: CenterSliceIndex = center_slice.index

                    algorithms: FaceTranslationResult = get_algorithms(
                        source_face, dest_face, coord
                    )

                    verify_algorithm(
                        cube, source_face, dest_face, coord,
                        algorithms.whole_cube_alg)

                    # Test individual slice algorithm (uses computed slice index)
                    verify_algorithm(
                        cube, source_face, dest_face, coord,
                        algorithms.slice_algorithms[0].get_alg())

                    cube.clear_c_attributes()


class TestWholeCubeRoundTrip:
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


# =============================================================================
# SLICE ALGORITHM TESTS
# =============================================================================

SLICE_CUBE_SIZES: list[int] = [5, 6, 7]  # Need at least 5 for meaningful inner slices




# =============================================================================
# EDGE CASES (shared between both algorithm types)
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling for both algorithm types."""

    def test_translate_same_face_raises_error(self) -> None:
        """Translating from a face to itself should raise ValueError."""
        cube = Cube(3, sp=_test_sp)

        with pytest.raises(ValueError, match="Cannot translate from a face to itself"):
            Face2FaceTranslator.translate(cube.front, cube.front, (1, 1))


    @pytest.mark.parametrize("cube_size", WHOLE_CUBE_SIZES)
    def test_translate_out_of_bounds_raises_error(self, cube_size: int) -> None:
        """Coordinates outside face bounds should raise ValueError for translate."""
        cube = Cube(cube_size, sp=_test_sp)
        n_slices = cube.front.center.n_slices

        invalid_coords: list[tuple[int, int]] = [
            (-1, 0),
            (0, -1),
            (n_slices, 0),
            (0, n_slices),
        ]

        for coord in invalid_coords:
            with pytest.raises(ValueError, match="out of bounds"):
                Face2FaceTranslator.translate(cube.front, cube.right, coord)

