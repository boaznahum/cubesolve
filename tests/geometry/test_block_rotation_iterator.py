"""
Test for Block rotation and cell iterator behavior.

Verifies that RotatedBlock preserves cell-to-cell mappings when iterating:
- rotate_preserve_original() returns a RotatedBlock that tracks rotation state
- RotatedBlock.points(n) yields cells in the order that preserves
  the original relative positions (not just row-by-row order)
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
    """Test that Block.rotation preserves cell-to-cell mappings in iterator."""

    @pytest.mark.parametrize("cube_size", [4, 5, 6, 7])
    @pytest.mark.parametrize("n_rotations", [0, 1, 2, 3])  # 0°, 90°, 180°, 270°
    @pytest.mark.parametrize("seed", range(3))  # Fewer random blocks for testing
    def test_block_rotation_preserves_iterator_order(self, cube_size: int, n_rotations: int, seed: int):
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

        # Step 3: Rotate the face n_rotations times (90° clockwise F move each time)
        from cube.domain.algs import Algs
        app.op.play(Algs.F * n_rotations)

        # Step 4: Rotate the block using rotate_preserve_original
        rotated_block = original_block.rotate_preserve_original(n_slices=n, n_rotations=n_rotations)

        # Assert the rotation is correctly detected
        assert rotated_block.n_rotations == n_rotations

        # Verify that we can detect the original normalized block
        # from the rotated corners
        original_detected = rotated_block.detect_original(n_slices=n)

        # Verify that the detected original block matches the original block
        # The detected original should be exactly the same as the original_block
        assert original_detected == original_block, \
            f"Detected original block {original_detected} doesn't match original block {original_block}"


        # Step 5: Iterate over rotated block using points (preserves original order)
        rotated_iterator_order = list(rotated_block.points(n))
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

        # Verify cell-to-cell mapping is preserved
        # The marker at original_iterator_order[0] should now be at rotated_iterator_order[0]
        # The marker at original_iterator_order[1] should now be at rotated_iterator_order[1]
        # etc.
        for i, (orig_point, rot_point) in enumerate(zip(original_iterator_order, rotated_iterator_order)):
            orig_marker = original_markers[(orig_point.row, orig_point.col)]
            rot_marker = rotated_markers.get((rot_point.row, rot_point.col))

            # THIS ASSERTION SHOULD NOW PASS - cell-to-cell mapping is preserved!
            assert rot_marker == orig_marker, \
                f"Cell {i}: marker at rotated[{i}] ({rot_point}) should be '{orig_marker}' but got '{rot_marker}'. " \
                f"Original was at {orig_point}."


