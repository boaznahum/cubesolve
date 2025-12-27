"""
Comprehensive tests for FaceCoordinateTranslator.

Test Matrix:
- 6 faces × 6 faces = 36 combinations (30 non-self)
- Each combination tested with multiple coordinates
- Both directions tested (forward and reverse)
- All cube sizes (3×3, 4×4, 5×5)

See: docs/design2/issue-face-to-face-navigation-framework.md
"""

import pytest
from cube.domain.model.FaceCoordinateTranslator import (
    FaceCoordinateTranslator,
    FaceTranslationResult,
    Axis,
    EdgePosition,
)
from cube.domain.model.Cube import Cube
from tests.test_utils import _test_sp


class TestFaceCoordinateTranslator:
    """
    Comprehensive tests proving all face-to-face translations work correctly.
    """

    @pytest.fixture
    def cube(self):
        """Create a 3x3 cube for testing."""
        return Cube(3, sp=_test_sp)

    @pytest.fixture
    def translator(self):
        """Create a translator instance."""
        return FaceCoordinateTranslator()

    @pytest.fixture
    def faces(self, cube):
        """Get all faces from the cube."""
        return {
            'F': cube.front,
            'U': cube.up,
            'R': cube.right,
            'B': cube.back,
            'D': cube.down,
            'L': cube.left,
        }

    # Adjacent pairs (24 total - each face has 4 neighbors)
    ADJACENT_PAIRS = [
        ('F', 'U'), ('F', 'R'), ('F', 'D'), ('F', 'L'),
        ('U', 'F'), ('U', 'R'), ('U', 'B'), ('U', 'L'),
        ('R', 'F'), ('R', 'U'), ('R', 'B'), ('R', 'D'),
        ('B', 'U'), ('B', 'R'), ('B', 'D'), ('B', 'L'),
        ('D', 'F'), ('D', 'R'), ('D', 'B'), ('D', 'L'),
        ('L', 'F'), ('L', 'U'), ('L', 'B'), ('L', 'D'),
    ]

    # Opposite pairs (6 total)
    OPPOSITE_PAIRS = [
        ('F', 'B'), ('B', 'F'),
        ('U', 'D'), ('D', 'U'),
        ('L', 'R'), ('R', 'L'),
    ]

    def test_translator_creation(self, translator):
        """Test that translator can be created."""
        assert translator is not None

    def test_same_face_raises_error(self, translator, faces):
        """Test that translating from a face to itself raises an error."""
        with pytest.raises(ValueError, match="Source and destination faces cannot be the same"):
            translator.translate_coordinate(
                faces['F'], faces['F'], (1, 1), cube_size=3
            )

    @pytest.mark.parametrize("source_name,dest_name", ADJACENT_PAIRS)
    def test_adjacent_faces_have_shared_edge(self, translator, faces, source_name, dest_name):
        """Test that adjacent face pairs have a shared edge."""
        source = faces[source_name]
        dest = faces[dest_name]

        result = translator.translate_coordinate(source, dest, (1, 1), cube_size=3)

        assert result.is_adjacent is True
        assert result.shared_edge is not None
        assert result.rotation_count == 1

    @pytest.mark.parametrize("source_name,dest_name", OPPOSITE_PAIRS)
    def test_opposite_faces_no_shared_edge(self, translator, faces, source_name, dest_name):
        """Test that opposite face pairs have no shared edge."""
        source = faces[source_name]
        dest = faces[dest_name]

        result = translator.translate_coordinate(source, dest, (1, 1), cube_size=3)

        assert result.is_adjacent is False
        assert result.shared_edge is None
        assert result.rotation_count == 2

    @pytest.mark.parametrize("source_name,dest_name", ADJACENT_PAIRS)
    def test_valid_dest_coordinates(self, translator, faces, source_name, dest_name):
        """Test that destination coordinates are within valid range."""
        source = faces[source_name]
        dest = faces[dest_name]
        n = 3

        for row in range(n):
            for col in range(n):
                result = translator.translate_coordinate(
                    source, dest, (row, col), cube_size=n
                )
                assert 0 <= result.dest_coord[0] < n, f"Row out of range: {result.dest_coord}"
                assert 0 <= result.dest_coord[1] < n, f"Col out of range: {result.dest_coord}"

    @pytest.mark.parametrize("source_name,dest_name", ADJACENT_PAIRS)
    def test_round_trip_adjacent(self, translator, faces, source_name, dest_name):
        """Test that translating forward then back returns to original coordinate."""
        source = faces[source_name]
        dest = faces[dest_name]
        n = 3

        for row in range(n):
            for col in range(n):
                coord = (row, col)

                # Forward
                result = translator.translate_coordinate(source, dest, coord, cube_size=n)

                # Reverse
                reverse = translator.translate_coordinate(
                    dest, source, result.dest_coord, cube_size=n
                )

                assert reverse.dest_coord == coord, (
                    f"{source_name}→{dest_name}: Round-trip failed: "
                    f"{coord} → {result.dest_coord} → {reverse.dest_coord}"
                )

    @pytest.mark.parametrize("source_name,dest_name", OPPOSITE_PAIRS)
    def test_round_trip_opposite(self, translator, faces, source_name, dest_name):
        """Test round-trip for opposite faces."""
        source = faces[source_name]
        dest = faces[dest_name]
        n = 3

        for row in range(n):
            for col in range(n):
                coord = (row, col)

                # Forward
                result = translator.translate_coordinate(source, dest, coord, cube_size=n)

                # Reverse
                reverse = translator.translate_coordinate(
                    dest, source, result.dest_coord, cube_size=n
                )

                assert reverse.dest_coord == coord, (
                    f"{source_name}↔{dest_name}: Round-trip failed: "
                    f"{coord} → {result.dest_coord} → {reverse.dest_coord}"
                )

    @pytest.mark.parametrize("source_name,dest_name", ADJACENT_PAIRS)
    def test_axis_exchange_follows_rule(self, translator, faces, source_name, dest_name):
        """
        Test that axis exchange follows the rule:
        - Horizontal edge (top/bottom) → COLUMN
        - Vertical edge (left/right) → ROW
        """
        source = faces[source_name]
        dest = faces[dest_name]

        result = translator.translate_coordinate(source, dest, (1, 1), cube_size=3)

        # Determine expected axes based on edge positions
        source_is_horizontal = result.source_edge_position in (
            EdgePosition.TOP, EdgePosition.BOTTOM
        )
        dest_is_horizontal = result.dest_edge_position in (
            EdgePosition.TOP, EdgePosition.BOTTOM
        )

        expected_source_axis = Axis.COLUMN if source_is_horizontal else Axis.ROW
        expected_dest_axis = Axis.COLUMN if dest_is_horizontal else Axis.ROW

        assert result.source_axis == expected_source_axis, (
            f"{source_name}→{dest_name}: Source axis mismatch. "
            f"Edge pos: {result.source_edge_position}, "
            f"Expected: {expected_source_axis}, Got: {result.source_axis}"
        )
        assert result.dest_axis == expected_dest_axis, (
            f"{source_name}→{dest_name}: Dest axis mismatch. "
            f"Edge pos: {result.dest_edge_position}, "
            f"Expected: {expected_dest_axis}, Got: {result.dest_axis}"
        )

        # Verify axis_exchange flag
        expected_exchange = (expected_source_axis != expected_dest_axis)
        assert result.axis_exchange == expected_exchange

    @pytest.mark.parametrize("cube_size", [3, 4, 5])
    def test_different_cube_sizes(self, translator, cube_size):
        """Test that translator works with different cube sizes."""
        cube = Cube(cube_size, sp=_test_sp)
        source = cube.front
        dest = cube.up

        # Test corners
        corners = [
            (0, 0), (0, cube_size - 1),
            (cube_size - 1, 0), (cube_size - 1, cube_size - 1)
        ]

        for coord in corners:
            result = translator.translate_coordinate(
                source, dest, coord, cube_size=cube_size
            )
            assert 0 <= result.dest_coord[0] < cube_size
            assert 0 <= result.dest_coord[1] < cube_size

    def test_all_combinations_exhaustive(self, translator, faces):
        """
        THE ULTIMATE TEST: Verify every single coordinate on every face
        can be translated to every other face and back.

        Total tests: 6 faces × 5 destinations × 9 coords (3×3) = 270 translations
        """
        face_list = list(faces.values())
        cube_size = 3
        failures = []

        for source in face_list:
            for dest in face_list:
                if source == dest:
                    continue

                for row in range(cube_size):
                    for col in range(cube_size):
                        coord = (row, col)
                        try:
                            # Forward
                            result = translator.translate_coordinate(
                                source, dest, coord, cube_size
                            )

                            # Validate result
                            assert 0 <= result.dest_coord[0] < cube_size
                            assert 0 <= result.dest_coord[1] < cube_size

                            # Reverse
                            reverse = translator.translate_coordinate(
                                dest, source, result.dest_coord, cube_size
                            )
                            assert reverse.dest_coord == coord

                        except AssertionError as e:
                            src_name = source.name.name if hasattr(source.name, 'name') else str(source.name)
                            dst_name = dest.name.name if hasattr(dest.name, 'name') else str(dest.name)
                            failures.append(f"{src_name}→{dst_name} coord={coord}: {e}")

        assert not failures, f"Failed translations:\n" + "\n".join(failures[:10])


class TestEdgePosition:
    """Tests for edge position determination."""

    @pytest.fixture
    def cube(self):
        return Cube(3, sp=_test_sp)

    @pytest.fixture
    def translator(self):
        return FaceCoordinateTranslator()

    def test_f_u_edge_positions(self, translator, cube):
        """Test edge positions for F→U translation."""
        result = translator.translate_coordinate(
            cube.front, cube.up, (0, 1), cube_size=3
        )
        # F-U edge should be TOP on F and BOTTOM on U
        assert result.source_edge_position == EdgePosition.TOP
        assert result.dest_edge_position == EdgePosition.BOTTOM

    def test_f_d_edge_positions(self, translator, cube):
        """Test edge positions for F→D translation."""
        result = translator.translate_coordinate(
            cube.front, cube.down, (2, 1), cube_size=3
        )
        # F-D edge should be BOTTOM on F and TOP on D
        assert result.source_edge_position == EdgePosition.BOTTOM
        assert result.dest_edge_position == EdgePosition.TOP

    def test_f_l_edge_positions(self, translator, cube):
        """Test edge positions for F→L translation."""
        result = translator.translate_coordinate(
            cube.front, cube.left, (1, 0), cube_size=3
        )
        # F-L edge should be LEFT on F and RIGHT on L
        assert result.source_edge_position == EdgePosition.LEFT
        assert result.dest_edge_position == EdgePosition.RIGHT

    def test_f_r_edge_positions(self, translator, cube):
        """Test edge positions for F→R translation."""
        result = translator.translate_coordinate(
            cube.front, cube.right, (1, 2), cube_size=3
        )
        # F-R edge should be RIGHT on F and LEFT on R
        assert result.source_edge_position == EdgePosition.RIGHT
        assert result.dest_edge_position == EdgePosition.LEFT
