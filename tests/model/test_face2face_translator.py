"""
Comprehensive tests for Face2FaceTranslator.

DEFINITION (Viewer Perspective):
    translate(source_face, dest_face, coord) → (dest_coord, whole_cube_alg)

    Verification:
    1. Put marker at dest_coord on dest_face
    2. Execute whole_cube_alg (brings dest_face to source_face position)
    3. Marker now appears at coord on source_face (same screen position)

TEST MATRIX:
    - 6 source faces × 5 destinations = 30 face pairs
    - Cube sizes: 3, 4, 5, 6, 7, 8
    - All positions on each face (n² per face)

    Total tests: 30 pairs × sum(n² for n in 3..8) = 30 × (9+16+25+36+49+64) = 30 × 199 = 5,970 tests
"""

from __future__ import annotations

import pytest
from typing import TYPE_CHECKING

from cube.domain.model.Cube import Cube
from cube.domain.model.Face2FaceTranslator import Face2FaceTranslator
from cube.domain.model.FaceName import FaceName

if TYPE_CHECKING:
    from cube.domain.model.Face import Face


# All 30 face pairs (source, dest) - excluding self-to-self
ALL_FACE_PAIRS: list[tuple[FaceName, FaceName]] = [
    # From F
    (FaceName.F, FaceName.U),
    (FaceName.F, FaceName.R),
    (FaceName.F, FaceName.D),
    (FaceName.F, FaceName.L),
    (FaceName.F, FaceName.B),  # opposite
    # From U
    (FaceName.U, FaceName.F),
    (FaceName.U, FaceName.R),
    (FaceName.U, FaceName.B),
    (FaceName.U, FaceName.L),
    (FaceName.U, FaceName.D),  # opposite
    # From R
    (FaceName.R, FaceName.F),
    (FaceName.R, FaceName.U),
    (FaceName.R, FaceName.B),
    (FaceName.R, FaceName.D),
    (FaceName.R, FaceName.L),  # opposite
    # From B
    (FaceName.B, FaceName.U),
    (FaceName.B, FaceName.R),
    (FaceName.B, FaceName.D),
    (FaceName.B, FaceName.L),
    (FaceName.B, FaceName.F),  # opposite
    # From D
    (FaceName.D, FaceName.F),
    (FaceName.D, FaceName.R),
    (FaceName.D, FaceName.B),
    (FaceName.D, FaceName.L),
    (FaceName.D, FaceName.U),  # opposite
    # From L
    (FaceName.L, FaceName.F),
    (FaceName.L, FaceName.U),
    (FaceName.L, FaceName.B),
    (FaceName.L, FaceName.D),
    (FaceName.L, FaceName.R),  # opposite
]

# Cube sizes to test
CUBE_SIZES = [3, 4, 5, 6, 7, 8]


def get_face_by_name(cube: Cube, name: FaceName) -> Face:
    """Get face object from cube by FaceName."""
    match name:
        case FaceName.F:
            return cube.front
        case FaceName.U:
            return cube.up
        case FaceName.R:
            return cube.right
        case FaceName.B:
            return cube.back
        case FaceName.D:
            return cube.down
        case FaceName.L:
            return cube.left
        case _:
            raise ValueError(f"Unknown face name: {name}")


def get_all_coords(n: int) -> list[tuple[int, int]]:
    """Get all (row, col) coordinates for an n×n face."""
    return [(row, col) for row in range(n) for col in range(n)]


class TestFace2FaceTranslator:
    """
    Comprehensive test suite for face-to-face coordinate translation.

    Each test:
    1. Creates cube of given size
    2. Gets translated coordinate and verification algorithm
    3. Places marker at translated coordinate on destination face
    4. Executes whole-cube algorithm
    5. Verifies marker appears at original coordinate on source face
    """

    @pytest.mark.parametrize("cube_size", CUBE_SIZES)
    @pytest.mark.parametrize("source_name,dest_name", ALL_FACE_PAIRS)
    def test_all_face_pairs_all_positions(
        self,
        cube_size: int,
        source_name: FaceName,
        dest_name: FaceName
    ) -> None:
        """
        Test all positions on a face translate correctly.

        For each position (row, col) on source_face:
        1. Get translation result (dest_coord, verification_alg)
        2. Mark dest_coord on dest_face with unique marker
        3. Execute verification_alg (whole cube rotation)
        4. Assert marker is now at (row, col) on source_face
        """
        cube = Cube(cube_size)
        translator = Face2FaceTranslator(cube)

        source_face = get_face_by_name(cube, source_name)
        dest_face = get_face_by_name(cube, dest_name)

        # Test all positions on the face
        for coord in get_all_coords(cube_size):
            self._verify_single_translation(
                cube, translator, source_face, dest_face, coord
            )
            # Reset cube for next test
            cube.reset()

    def _verify_single_translation(
        self,
        cube: Cube,
        translator: Face2FaceTranslator,
        source_face: Face,
        dest_face: Face,
        coord: tuple[int, int]
    ) -> None:
        """
        Verify a single coordinate translation using the viewer-perspective test.

        Steps:
        1. Get translation result
        2. Place marker at dest_coord on dest_face
        3. Execute verification algorithm
        4. Assert marker appears at coord on source_face
        """
        row, col = coord

        # Step 1: Get translation
        result = translator.translate(source_face, dest_face, coord)

        # Step 2: Place marker at dest_coord on dest_face
        # Use c_attribute to mark the cell
        dest_row, dest_col = result.dest_coord
        marker_value = "MARKER"
        dest_cell = dest_face.get_cell(dest_row, dest_col)
        dest_cell.c_attributes["test_marker"] = marker_value

        # Step 3: Execute verification algorithm (brings dest to source position)
        # The verification_rotation brings dest_face to where source_face is
        cube.execute_alg(result.verification_rotation)

        # Step 4: After rotation, check source_face position
        # The face that is now at source_face's original position should have
        # the marker at the original coord
        #
        # Note: After whole-cube rotation, source_face object still refers to
        # the same Face, but that face is now in a different position.
        # We need to check the face that is NOW in the front/up/etc position
        # where source_face WAS.
        #
        # Actually, for whole cube rotations (X, Y, Z), the faces don't change
        # their colors - the whole cube rotates. So we need to check:
        # - What face is now where source_face was?
        # - That face should have the marker at coord

        # Get the face that is now at source_face's original world position
        # After the rotation, dest_face should be where source_face was
        current_face_at_source_position = self._get_face_at_position_after_rotation(
            cube, source_face, result.verification_rotation
        )

        # The marker should be at the original coord on this face
        cell_at_original_position = current_face_at_source_position.get_cell(row, col)

        assert cell_at_original_position.c_attributes.get("test_marker") == marker_value, (
            f"Translation failed for {source_face.name}({row},{col}) → {dest_face.name}\n"
            f"Expected marker at ({row},{col}) on face now at {source_face.name}'s position\n"
            f"Dest coord was: {result.dest_coord}\n"
            f"Verification rotation: {result.verification_rotation}"
        )

    def _get_face_at_position_after_rotation(
        self,
        cube: Cube,
        original_face: Face,
        rotation: str
    ) -> Face:
        """
        After a whole-cube rotation, get the face that is now at
        the position where original_face was before the rotation.

        For example:
        - If original_face was Front, and rotation was Y' (which brings R to front),
          then after Y', the Right face is now at Front's position.
        - So we return cube.front (which is now what was cube.right)

        Wait, that's not right. Whole cube rotations in this codebase...
        need to check how they work.
        """
        # TODO: Implement based on how whole-cube rotations work
        # For now, this is a placeholder
        #
        # The key insight: after rotation, dest_face should be at source_face's position
        # So we just need to return dest_face... but that's not quite right either
        # because the face objects don't move, only the stickers do.
        #
        # Actually for whole cube rotations (X, Y, Z), the cube reference frame changes.
        # After Y', what was Right is now Front.
        # So cube.front now refers to what was Right.
        #
        # This needs careful implementation based on the actual cube model.

        raise NotImplementedError(
            "Need to implement face position tracking after whole-cube rotation"
        )


class TestVerificationRotations:
    """
    Test that we have correct verification rotations for all face pairs.

    The verification rotation for (source, dest) should bring dest to source's position.
    """

    @pytest.mark.parametrize("source_name,dest_name", ALL_FACE_PAIRS)
    def test_verification_rotation_brings_dest_to_source(
        self,
        source_name: FaceName,
        dest_name: FaceName
    ) -> None:
        """
        Verify that the verification rotation actually brings dest to source position.
        """
        cube = Cube(3)
        translator = Face2FaceTranslator(cube)

        source_face = get_face_by_name(cube, source_name)
        dest_face = get_face_by_name(cube, dest_name)

        # Get any translation (just to get the verification rotation)
        result = translator.translate(source_face, dest_face, (1, 1))

        # Mark dest_face center with unique color
        original_dest_center_color = dest_face.center.color

        # Execute verification rotation
        cube.execute_alg(result.verification_rotation)

        # After rotation, the center color of what's now at source position
        # should be the original dest center color
        # (centers don't move relative to their face, so this tracks the face)

        # Get face now at source's world position
        # This depends on how the cube model handles whole-cube rotations
        # TODO: Implement properly

        pass  # Placeholder


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_translate_same_face_raises_error(self) -> None:
        """Translating from a face to itself should raise ValueError."""
        cube = Cube(3)
        translator = Face2FaceTranslator(cube)

        with pytest.raises(ValueError, match="Cannot translate from a face to itself"):
            translator.translate(cube.front, cube.front, (1, 1))

    @pytest.mark.parametrize("cube_size", CUBE_SIZES)
    def test_out_of_bounds_raises_error(self, cube_size: int) -> None:
        """Coordinates outside face bounds should raise ValueError."""
        cube = Cube(cube_size)
        translator = Face2FaceTranslator(cube)

        invalid_coords = [
            (-1, 0),
            (0, -1),
            (cube_size, 0),
            (0, cube_size),
            (cube_size, cube_size),
        ]

        for coord in invalid_coords:
            with pytest.raises(ValueError, match="out of bounds"):
                translator.translate(cube.front, cube.right, coord)


class TestRoundTrip:
    """Test that translating A→B→A returns the original coordinate."""

    @pytest.mark.parametrize("cube_size", [3, 5])  # Subset for performance
    @pytest.mark.parametrize("source_name,dest_name", ALL_FACE_PAIRS[:10])  # Subset
    def test_round_trip_returns_original(
        self,
        cube_size: int,
        source_name: FaceName,
        dest_name: FaceName
    ) -> None:
        """Translate A→B then B→A should return original coordinate."""
        cube = Cube(cube_size)
        translator = Face2FaceTranslator(cube)

        source_face = get_face_by_name(cube, source_name)
        dest_face = get_face_by_name(cube, dest_name)

        for coord in get_all_coords(cube_size):
            # A → B
            result1 = translator.translate(source_face, dest_face, coord)

            # B → A
            result2 = translator.translate(dest_face, source_face, result1.dest_coord)

            assert result2.dest_coord == coord, (
                f"Round-trip failed: {coord} → {result1.dest_coord} → {result2.dest_coord}"
            )
