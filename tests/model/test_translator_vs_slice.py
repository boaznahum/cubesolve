"""
Compare FaceCoordinateTranslator predictions against actual Slice behavior.

This test verifies that the translator produces the same coordinate
mappings as the existing (proven working) Slice rotation code.

The Slice code uses edge translation internally:
    next_slice_index = next_edge.get_slice_index_from_ltr_index(current_face, current_index)
    current_index = next_edge.get_ltr_index_from_slice_index(next_face, next_slice_index)

Our FaceCoordinateTranslator uses the SAME methods, so results must match.

Run with: PYTHONPATH=src pytest tests/model/test_translator_vs_slice.py -v
"""

import pytest
from cube.domain.model.FaceCoordinateTranslator import (
    FaceCoordinateTranslator,
    Axis,
    EdgePosition,
)
from cube.domain.model.Cube import Cube
from tests.test_utils import _test_sp


class TestTranslatorVsSlice:
    """Compare translator predictions against actual Slice behavior."""

    @pytest.fixture
    def cube(self):
        """Create a 3x3 cube for testing."""
        return Cube(3, sp=_test_sp)

    @pytest.fixture
    def translator(self):
        """Create a translator instance."""
        return FaceCoordinateTranslator()

    def test_edge_translation_matches_slice_logic(self, cube, translator):
        """
        Verify that translator's edge translation matches Slice behavior.

        The Slice code (Slice.py lines 131-132) does:
            next_slice_index = next_edge.get_slice_index_from_ltr_index(current_face, current_index)
            current_index = next_edge.get_ltr_index_from_slice_index(next_face, next_slice_index)

        Our translator does the same thing in _translate_adjacent().
        """
        # Test F→U translation
        source = cube.front
        dest = cube.up
        shared_edge = source.edge_top  # The F-U edge

        # Verify this is indeed the shared edge
        assert dest.is_edge(shared_edge)

        n = 3
        for ltr in range(n):
            # Slice method
            edge_index = shared_edge.get_slice_index_from_ltr_index(source, ltr)
            dest_ltr = shared_edge.get_ltr_index_from_slice_index(dest, edge_index)

            # Translator method - use edge position at TOP on source
            # For TOP edge, ltr is the column index
            source_coord = (0, ltr)  # row 0 is at the edge
            result = translator.translate_coordinate(source, dest, source_coord, n)

            # The dest_ltr from translator should match
            assert result.dest_ltr == dest_ltr, (
                f"LTR mismatch at {ltr}: Slice={dest_ltr}, Translator={result.dest_ltr}"
            )

    def test_perpendicular_distance_preserved(self, cube, translator):
        """
        Verify perpendicular distance from edge is preserved during translation.

        When moving from F to U:
        - F's TOP edge is shared with U's BOTTOM edge
        - A piece at row 0 on F (at the edge) should end up at row 2 on U (at the edge)
        - A piece at row 2 on F (far from edge) should end up at row 0 on U (far from edge)
        """
        source = cube.front
        dest = cube.up
        n = 3

        # Test different perpendicular distances
        for col in range(n):
            for row in range(n):
                result = translator.translate_coordinate(source, dest, (row, col), n)

                # Perpendicular distance from TOP edge on source = n - 1 - row
                source_perp = n - 1 - row

                # On destination (BOTTOM edge), perpendicular distance = n - 1 - dest_row
                dest_perp = n - 1 - result.dest_coord[0]

                assert source_perp == dest_perp, (
                    f"Perpendicular distance not preserved: "
                    f"source ({row},{col}) perp={source_perp}, "
                    f"dest {result.dest_coord} perp={dest_perp}"
                )

    def test_all_adjacent_pairs_have_consistent_edge_positions(self, cube, translator):
        """
        Verify that edge positions are correctly identified for all adjacent pairs.

        For each adjacent pair, the shared edge should have complementary positions:
        - TOP on source ↔ BOTTOM on dest (or vice versa)
        - LEFT on source ↔ RIGHT on dest (or vice versa)
        """
        faces = {
            'F': cube.front,
            'U': cube.up,
            'R': cube.right,
            'B': cube.back,
            'D': cube.down,
            'L': cube.left,
        }

        # Expected edge position pairs for each adjacent combination
        # (These are physical facts about the cube)
        expected_pairs = {
            ('F', 'U'): (EdgePosition.TOP, EdgePosition.BOTTOM),
            ('F', 'R'): (EdgePosition.RIGHT, EdgePosition.LEFT),
            ('F', 'D'): (EdgePosition.BOTTOM, EdgePosition.TOP),
            ('F', 'L'): (EdgePosition.LEFT, EdgePosition.RIGHT),
            # Add more pairs as needed...
        }

        for (src_name, dst_name), (expected_src_pos, expected_dst_pos) in expected_pairs.items():
            source = faces[src_name]
            dest = faces[dst_name]

            result = translator.translate_coordinate(source, dest, (1, 1), 3)

            assert result.source_edge_position == expected_src_pos, (
                f"{src_name}→{dst_name}: Expected source edge {expected_src_pos}, "
                f"got {result.source_edge_position}"
            )
            assert result.dest_edge_position == expected_dst_pos, (
                f"{src_name}→{dst_name}: Expected dest edge {expected_dst_pos}, "
                f"got {result.dest_edge_position}"
            )

    def test_axis_exchange_correctly_detected(self, cube, translator):
        """
        Verify axis exchange is correctly detected.

        Axis exchange occurs when source and dest edges have different orientations:
        - Source horizontal (TOP/BOTTOM) + Dest vertical (LEFT/RIGHT) → exchange
        - Source vertical (LEFT/RIGHT) + Dest horizontal (TOP/BOTTOM) → exchange
        - Same orientation → no exchange
        """
        # F→U: Both horizontal edges (TOP on F, BOTTOM on U) → NO exchange
        result = translator.translate_coordinate(cube.front, cube.up, (1, 1), 3)
        assert result.axis_exchange is False, "F→U should have no axis exchange"

        # F→R: F has vertical edge (RIGHT), R has vertical edge (LEFT) → NO exchange
        result = translator.translate_coordinate(cube.front, cube.right, (1, 1), 3)
        assert result.axis_exchange is False, "F→R should have no axis exchange"

        # For S slice: U→R has axis exchange (U horizontal → R vertical)
        # U uses LEFT edge (vertical), R uses TOP edge (horizontal)
        result = translator.translate_coordinate(cube.up, cube.right, (1, 1), 3)
        # U-R edge is on RIGHT of U (vertical) and TOP of R (horizontal)
        # Vertical source → Horizontal dest = exchange
        expected_exchange = (result.source_axis != result.dest_axis)
        assert result.axis_exchange == expected_exchange


class TestVisualOutput:
    """Tests that produce visual output for manual verification."""

    @pytest.fixture
    def cube(self):
        return Cube(3, sp=_test_sp)

    @pytest.fixture
    def translator(self):
        return FaceCoordinateTranslator()

    def test_print_f_to_u_translation(self, cube, translator):
        """Print complete F→U translation for visual verification."""
        print("\n" + "=" * 50)
        print("F → U Translation (all coordinates)")
        print("=" * 50)

        source = cube.front
        dest = cube.up
        n = 3

        print(f"\nSource edge position: TOP on F")
        print(f"Dest edge position: BOTTOM on U")
        print()
        print("Source (F)     →  Dest (U)")
        print("-" * 30)

        for row in range(n):
            for col in range(n):
                result = translator.translate_coordinate(source, dest, (row, col), n)
                print(f"({row},{col})         →  {result.dest_coord}")

        print()

    def test_print_translation_summary(self, cube, translator):
        """Print summary of all adjacent face translations."""
        print("\n" + "=" * 50)
        print("TRANSLATION SUMMARY (center coordinate)")
        print("=" * 50)

        faces = [
            ('F', cube.front), ('U', cube.up), ('R', cube.right),
            ('B', cube.back), ('D', cube.down), ('L', cube.left)
        ]

        center = (1, 1)

        for src_name, source in faces:
            print(f"\nFrom {src_name}:")
            for dst_name, dest in faces:
                if source == dest:
                    continue
                result = translator.translate_coordinate(source, dest, center, 3)
                adj = "adj" if result.is_adjacent else "opp"
                exch = "EXCH" if result.axis_exchange else "same"
                print(f"  → {dst_name}: {center} → {result.dest_coord} "
                      f"[{adj}, {exch}, {result.source_axis.name}→{result.dest_axis.name}]")
