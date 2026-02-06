"""
Test for Block rotation and cell iterator behavior.

This test exposes the problem: when a face rotates, the block's cells rotate
with it, but Block.cells iterator always yields cells in row-by-row order based on
the rotated block's coordinates. This means the iterator order does NOT preserve
the relative cell-to-cell mapping - it yields cells at positions [r1,c1], [r1,c2], etc.
rather than following where the original cells actually moved.

EXPECTED BEHAVIOR (what we want):
- Block.rotate() should return a RotatedBlock that tracks cell-to-cell mappings
- Iterating over rotated block should yield cells in the order that preserves
  the original relative positions

ACTUAL BEHAVIOR (what currently fails):
- Block.rotate() just returns a new Block with rotated corner coordinates
- Iterating over rotated block yields cells in row-by-row order of new block
- This does NOT preserve the iterator-to-cell mapping

The test should FAIL until RotatedBlock is properly implemented.
"""

import random
import pytest
import uuid

from cube.application.AbstractApp import AbstractApp
from cube.domain.geometric.geometry_types import Block, Point


def create_app(cube_size: int) -> AbstractApp:
    """Create an app with specified cube size."""
    return AbstractApp.create_non_default(cube_size, animation=False)


class TestBlockRotationIterator:
    """
    Test that Block.rotation preserves cell-to-cell mappings in iterator.

    This test should FAIL until RotatedBlock is properly implemented.
    """

    @pytest.mark.parametrize("cube_size", [4, 5, 6, 7])
    @pytest.mark.parametrize("seed", range(10))  # Multiple random blocks per size
    def test_block_rotation_preserves_iterator_order(self, cube_size: int, seed: int):
        """
        Block.rotate() should preserve cell-to-cell mappings when iterating.

        Test procedure:
        1. Create a cube and get the Front face
        2. Randomly create a Block on the face
        3. Iterate over block cells using Block.cells, placing unique markers
        4. Rotate the face (F move)
        5. Rotate the block using Block.rotate_clockwise()
        6. Iterate over rotated block cells
        7. Verify markers match expected positions

        This test EXPOSES the problem: the iterator order changes after rotation
        even though we want to preserve the relative cell-to-cell mapping.
        """
        # Setup
        random.seed(seed)
        app = create_app(cube_size)
        cube = app.cube
        face = cube.front
        n = cube.n_slices

        # Step 1: Randomly create a Block
        # Ensure block is not too small (at least 2x2)
        r1 = random.randint(0, n - 2)
        c1 = random.randint(0, n - 2)
        r2 = random.randint(r1 + 1, n - 1)
        c2 = random.randint(c1 + 1, n - 1)

        original_block = Block(Point(r1, c1), Point(r2, c2))

        # Step 2: Place unique markers on each cell in the block
        marker_key = f"marker_{uuid.uuid4().hex[:8]}"
        original_markers = {}  # Map: cell_coord -> marker_value

        for idx, point in enumerate(original_block.cells):
            # Get the center slice at this position
            center_slice = face.center.get_center_slice((point.row, point.col))

            # Set a unique marker for this cell
            marker_value = f"cell_{idx}"
            center_slice.edge.moveable_attributes[marker_key] = marker_value
            original_markers[(point.row, point.col)] = marker_value

        # Record the iterator order (this is what we want to preserve)
        original_iterator_order = list(original_block.cells)

        # Step 3: Rotate the face (90° clockwise F move)
        from cube.domain.algs import Algs
        app.op.play(Algs.F)

        # Step 4: Rotate the block using Block.rotate_clockwise()
        rotated_block = original_block.rotate_clockwise(n_slices=n, n_rotations=1)

        # Step 5: Iterate over rotated block and collect markers
        rotated_iterator_order = list(rotated_block.cells)
        rotated_markers = {}

        for idx, point in enumerate(rotated_iterator_order):
            center_slice = face.center.get_center_slice((point.row, point.col))
            marker = center_slice.edge.moveable_attributes.get(marker_key)
            if marker:
                rotated_markers[(point.row, point.col)] = marker

        # Step 6: Verify the expected behavior
        # We expect that:
        # - The rotated block should contain the same number of cells
        # - The first cell in rotated iterator should have the marker from the first cell in original iterator
        # - The second cell in rotated iterator should have the marker from the second cell in original iterator
        # - And so on...
        #
        # This PRESERVES the relative cell-to-cell relationship

        assert len(original_iterator_order) == len(rotated_iterator_order), \
            f"Block size changed after rotation: original={len(original_iterator_order)}, rotated={len(rotated_iterator_order)}"

        # THIS IS WHAT WE WANT TO PRESERVE:
        # The marker at original_iterator_order[0] should now be at rotated_iterator_order[0]
        # The marker at original_iterator_order[1] should now be at rotated_iterator_order[1]
        # etc.

        for i, (orig_point, rot_point) in enumerate(zip(original_iterator_order, rotated_iterator_order)):
            orig_marker = original_markers[(orig_point.row, orig_point.col)]
            rot_marker = rotated_markers.get((rot_point.row, rot_point.col))

            # THIS ASSERTION SHOULD FAIL - exposing the problem
            assert rot_marker == orig_marker, \
                f"Cell {i}: marker at rotated[{i}] ({rot_point}) should be '{orig_marker}' but got '{rot_marker}'. " \
                f"Original was at {orig_point}."

    @pytest.mark.parametrize("cube_size", [6, 7])  # Only larger cubes to avoid out-of-bounds
    @pytest.mark.parametrize("n_rotations", [1, 2, 3])  # 90°, 180°, 270°
    def test_all_rotation_angles_preserve_mappings(self, cube_size: int, n_rotations: int):
        """
        Test that all rotation angles (90°, 180°, 270°) preserve cell mappings.

        Uses a fixed 2x3 block at position (1,2) for reproducibility.
        """
        # Setup
        app = create_app(cube_size)
        cube = app.cube
        face = cube.front
        n = cube.n_slices

        # Use a fixed 2x3 block starting at (1, 2)
        original_block = Block(Point(1, 2), Point(2, 4))

        # Place markers
        marker_key = f"marker_{uuid.uuid4().hex[:8]}"
        original_markers = {}

        for idx, point in enumerate(original_block.cells):
            center_slice = face.center.get_center_slice((point.row, point.col))
            marker_value = f"cell_{idx}"
            center_slice.edge.moveable_attributes[marker_key] = marker_value
            original_markers[(point.row, point.col)] = marker_value

        original_iterator_order = list(original_block.cells)

        # Rotate the face n times
        from cube.domain.algs import Algs
        for _ in range(n_rotations):
            app.op.play(Algs.F)

        # Rotate the block
        rotated_block = original_block.rotate_clockwise(n_slices=n, n_rotations=n_rotations)
        rotated_iterator_order = list(rotated_block.cells)

        # Collect markers from rotated positions
        rotated_markers = {}
        for point in rotated_iterator_order:
            center_slice = face.center.get_center_slice((point.row, point.col))
            marker = center_slice.edge.moveable_attributes.get(marker_key)
            if marker:
                rotated_markers[(point.row, point.col)] = marker

        # Verify cell-to-cell mapping is preserved
        assert len(original_iterator_order) == len(rotated_iterator_order), \
            f"Block size changed: {len(original_iterator_order)} -> {len(rotated_iterator_order)}"

        for i, (orig_point, rot_point) in enumerate(zip(original_iterator_order, rotated_iterator_order)):
            orig_marker = original_markers[(orig_point.row, orig_point.col)]
            rot_marker = rotated_markers.get((rot_point.row, rot_point.col))

            # THIS SHOULD FAIL - exposing the problem
            assert rot_marker == orig_marker, \
                f"Rotation {n_rotations}*90°, cell {i}: expected marker '{orig_marker}' " \
                f"(from {orig_point}), got '{rot_marker}' (at {rot_point})"

    @pytest.mark.parametrize("cube_size", [5, 6, 7])
    def test_iterator_order_changes_with_rotation(self, cube_size: int):
        """
        Document that the iterator order DOES change after rotation.

        This test documents the CURRENT (incorrect) behavior to understand
        what needs to be fixed.
        """
        app = create_app(cube_size)
        cube = app.cube
        n = cube.n_slices

        # Use a 2x3 block for clear demonstration
        original_block = Block(Point(1, 2), Point(2, 4))

        # Original iterator order
        original_order = list(original_block.cells)

        # Rotate the block (without rotating the face) - for documentation
        rotated_90 = original_block.rotate_clockwise(n_slices=n, n_rotations=1)
        rotated_180 = original_block.rotate_clockwise(n_slices=n, n_rotations=2)
        rotated_270 = original_block.rotate_clockwise(n_slices=n, n_rotations=3)
        rotated_90 = original_block.rotate_clockwise(n_slices=n, n_rotations=1)
        rotated_180 = original_block.rotate_clockwise(n_slices=n, n_rotations=2)
        rotated_270 = original_block.rotate_clockwise(n_slices=n, n_rotations=3)

        order_90 = list(rotated_90.cells)
        order_180 = list(rotated_180.cells)
        order_270 = list(rotated_270.cells)

        # The iterator orders are all different - documenting the problem
        # What we observe: the iterator yields positions in row-by-row order
        # based on the rotated block's corner coordinates
        # It does NOT track where each original cell moved to

        # Document that the orders are different
        # This is EXPECTED to fail until we implement RotatedBlock properly

        # The blocks have different shapes after rotation
        # (2x3 horizontal) -> (3x2 vertical) -> (2x3 horizontal) -> (3x2 vertical)

        # What we observe: the iterator just yields positions in row-by-row order
        # based on the rotated block's corner coordinates
        # It does NOT track where each original cell moved to

        # This test documents the problem - we need RotatedBlock to track cell mappings
        pytest.fail("TODO: Implement RotatedBlock that tracks cell-to-cell mappings. "
                     "Current Block.rotate() only changes corner coordinates, "
                     "so the iterator yields positions in row-by-row order of the new block shape, "
                     "not following where original cells actually moved.")
