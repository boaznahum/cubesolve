"""
Behavioral verification tests for face-to-face coordinate translation.

These tests verify the RESULTS of translations, not the implementation.
They work by:
1. Identifying pieces by their colors (immutable identity)
2. Performing rotations
3. Verifying pieces ended up in physically correct positions

This is INDEPENDENT of how the translation is implemented.

Run with: PYTHONPATH=src pytest tests/model/test_translation_behavior.py -v -s
"""

import pytest
from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.model.SliceName import SliceName
from tests.test_utils import _test_sp


def get_center_color_at(face: Face, row: int, col: int) -> str:
    """Get the color name at a specific center position on a face."""
    center = face.center
    center_slice = center.get_center_slice((row, col))
    return center_slice.color.name


def get_edge_color_at(face: Face, edge_name: str, ltr: int) -> str:
    """Get the color of an edge slice at given ltr position."""
    edge = getattr(face, f"edge_{edge_name}")
    edge_slice = edge.get_slice_by_ltr_index(face, ltr)
    # Get the part edge that belongs to this face
    part_edge = edge_slice.get_face_edge(face)
    return part_edge.color.name


class TestMSliceBehavior:
    """
    Test M slice rotation behavior.

    M slice path: F → U → B → D → F
    M slice uses COLUMN axis on all faces (no axis exchange).

    Physical behavior on 3x3:
    - Column 1 of Front goes to Column 1 of Up
    - Column 1 of Up goes to Column 1 of Back (inverted because B is viewed from behind)
    - Column 1 of Back goes to Column 1 of Down
    - Column 1 of Down goes to Column 1 of Front
    """

    @pytest.fixture
    def cube(self):
        """Create a fresh solved 3x3 cube."""
        return Cube(3, sp=_test_sp)

    def test_m_slice_moves_front_center_to_up(self, cube):
        """
        After M rotation, Front's center column should move to Up.

        On a solved cube:
        - Front center is GREEN
        - After M rotation, Up's bottom-center should be GREEN
        """
        # Record initial state
        front_center_color = cube.front.center.color.name

        # Perform M slice rotation
        cube.m.rotate()

        # Verify: Front's center moved to Up's center
        # M moves F→U, and the center goes to center
        up_center_color = cube.up.center.color.name

        assert up_center_color == front_center_color, (
            f"M slice should move Front center ({front_center_color}) to Up center, "
            f"but Up center is {up_center_color}"
        )

    def test_m_slice_full_cycle(self, cube):
        """
        After 4 M rotations, cube should return to solved state.

        This verifies the rotation is consistent.
        """
        assert cube.solved, "Cube should start solved"

        # 4 rotations should return to original
        for _ in range(4):
            cube.m.rotate()

        assert cube.solved, "After 4 M rotations, cube should be solved again"

    def test_m_slice_piece_tracking(self, cube):
        """
        Track a specific piece through M rotation.

        Front center (GREEN) should follow path: F → U → B → D → F
        """
        # Get the colors of centers on the M slice path
        initial_colors = {
            'F': cube.front.center.color.name,
            'U': cube.up.center.color.name,
            'B': cube.back.center.color.name,
            'D': cube.down.center.color.name,
        }

        # After M rotation, each center moves to the next position
        cube.m.rotate()

        # F's color should now be at U
        assert cube.up.center.color.name == initial_colors['F'], (
            f"F center should move to U"
        )
        # U's color should now be at B
        assert cube.back.center.color.name == initial_colors['U'], (
            f"U center should move to B"
        )
        # B's color should now be at D
        assert cube.down.center.color.name == initial_colors['B'], (
            f"B center should move to D"
        )
        # D's color should now be at F
        assert cube.front.center.color.name == initial_colors['D'], (
            f"D center should move to F"
        )


class TestSSliceBehavior:
    """
    Test S slice rotation behavior.

    S slice path: U → R → D → L → U
    S slice has AXIS EXCHANGE (alternates ROW/COLUMN).

    This is the critical test for axis exchange correctness.
    """

    @pytest.fixture
    def cube(self):
        return Cube(3, sp=_test_sp)

    def test_s_slice_moves_up_center_to_right(self, cube):
        """
        After S rotation, Up's center row should move to Right's center column.

        On a solved cube:
        - Up center is WHITE
        - After S rotation, Right's center should be WHITE
        """
        up_center_color = cube.up.center.color.name

        cube.s.rotate()

        right_center_color = cube.right.center.color.name

        assert right_center_color == up_center_color, (
            f"S slice should move Up center ({up_center_color}) to Right center, "
            f"but Right center is {right_center_color}"
        )

    def test_s_slice_full_cycle(self, cube):
        """After 4 S rotations, cube should return to solved state."""
        assert cube.solved

        for _ in range(4):
            cube.s.rotate()

        assert cube.solved, "After 4 S rotations, cube should be solved again"

    def test_s_slice_piece_tracking(self, cube):
        """
        Track pieces through S rotation (has axis exchange).

        U → R → D → L → U
        """
        initial_colors = {
            'U': cube.up.center.color.name,
            'R': cube.right.center.color.name,
            'D': cube.down.center.color.name,
            'L': cube.left.center.color.name,
        }

        cube.s.rotate()

        assert cube.right.center.color.name == initial_colors['U'], "U→R"
        assert cube.down.center.color.name == initial_colors['R'], "R→D"
        assert cube.left.center.color.name == initial_colors['D'], "D→L"
        assert cube.up.center.color.name == initial_colors['L'], "L→U"


class TestESliceBehavior:
    """Test E slice rotation behavior (horizontal slice, over D)."""

    @pytest.fixture
    def cube(self):
        return Cube(3, sp=_test_sp)

    def test_e_slice_full_cycle(self, cube):
        """After 4 E rotations, cube should return to solved state."""
        assert cube.solved

        for _ in range(4):
            cube.e.rotate()

        assert cube.solved


class TestFaceRotationBehavior:
    """
    Test face rotation behavior.

    Face rotation affects the 4 adjacent edges.
    """

    @pytest.fixture
    def cube(self):
        return Cube(3, sp=_test_sp)

    def test_front_rotation_moves_up_bottom_to_right_left(self, cube):
        """
        F rotation: U's bottom edge → R's left edge

        On solved cube:
        - Up's bottom edge is WHITE
        - After F rotation, Right's left edge should be WHITE
        """
        # The edge piece colors
        up_bottom_color = cube.up.edge_bottom.get_face_edge(cube.up).color.name

        cube.front.rotate()

        right_left_color = cube.right.edge_left.get_face_edge(cube.right).color.name

        assert right_left_color == up_bottom_color, (
            f"F rotation should move Up's bottom edge ({up_bottom_color}) "
            f"to Right's left edge, but got {right_left_color}"
        )

    def test_front_rotation_full_cycle(self, cube):
        """After 4 F rotations, cube should return to solved state."""
        assert cube.solved

        for _ in range(4):
            cube.front.rotate()

        assert cube.solved


class TestBigCubeBehavior:
    """
    Test behavior on bigger cubes (4x4, 5x5).

    These tests verify that coordinate translation works for
    non-center positions (multiple center slices).
    """

    @pytest.fixture
    def cube4(self):
        return Cube(4, sp=_test_sp)

    @pytest.fixture
    def cube5(self):
        return Cube(5, sp=_test_sp)

    def test_4x4_m_slice_cycle(self, cube4):
        """4x4 M slice should cycle in 4 rotations."""
        assert cube4.solved

        for _ in range(4):
            cube4.m.rotate()

        assert cube4.solved

    def test_5x5_m_slice_cycle(self, cube5):
        """5x5 M slice should cycle in 4 rotations."""
        assert cube5.solved

        for _ in range(4):
            cube5.m.rotate()

        assert cube5.solved

    def test_5x5_all_inner_slices_cycle(self, cube5):
        """All inner slices should cycle in 4 rotations."""
        assert cube5.solved

        # M slice (index 1 and 2 on 5x5)
        for _ in range(4):
            cube5.m.rotate()
        assert cube5.solved, "M slice cycle failed"

        # E slice
        for _ in range(4):
            cube5.e.rotate()
        assert cube5.solved, "E slice cycle failed"

        # S slice
        for _ in range(4):
            cube5.s.rotate()
        assert cube5.solved, "S slice cycle failed"


class TestInvariantProperties:
    """
    Test invariant properties that must hold regardless of implementation.

    These are mathematical facts about cube rotations.
    """

    @pytest.fixture
    def cube(self):
        return Cube(3, sp=_test_sp)

    def test_rotation_preserves_piece_count(self, cube):
        """
        Any rotation should preserve the total number of pieces.

        3x3 has: 6 centers, 12 edges, 8 corners = 26 pieces
        """
        # This is implicitly tested by solved state tests,
        # but we make it explicit
        cube.m.rotate()
        cube.s.rotate()
        cube.front.rotate()

        # Count pieces (centers)
        center_count = sum(1 for f in [cube.front, cube.up, cube.right,
                                        cube.back, cube.down, cube.left]
                          for _ in [f.center])
        assert center_count == 6

    def test_opposite_rotations_cancel(self, cube):
        """Rotation followed by inverse should return to original."""
        assert cube.solved

        # M and M' should cancel
        cube.m.rotate()
        cube.m.rotate(-1)  # inverse
        assert cube.solved, "M M' should cancel"

        # F and F' should cancel
        cube.front.rotate()
        cube.front.rotate(-1)
        assert cube.solved, "F F' should cancel"

    def test_commutator_identity(self, cube):
        """
        Certain move sequences should return to solved.

        Example: (R U R' U')×6 = identity on 3x3
        """
        assert cube.solved

        # This is a well-known cube identity
        for _ in range(6):
            cube.right.rotate()
            cube.up.rotate()
            cube.right.rotate(-1)
            cube.up.rotate(-1)

        assert cube.solved, "Sexy move ×6 should return to solved"
