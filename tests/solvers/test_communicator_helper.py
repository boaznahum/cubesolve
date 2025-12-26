"""
Tests for CommunicatorHelper.

Test structure:
- Iterate all source/target face pairs
- For each (y, x) position in LTR coordinates
- For each of 4 rotations, get source position
- Set a unique attribute on source piece
- Call the communicator helper
- Verify attribute moved to target, not on source
- Verify cube state preserved (edges in position)

Coordinate Systems:
- LTR (Left-to-Right): (ltr_y, ltr_x) where (0,0) is bottom-left
  - ltr_y increases upward (along left edge)
  - ltr_x increases rightward (along bottom edge)
- Index: (idx_row, idx_col) used by get_center_slice()
  - Translation uses edge_left for Y and edge_bottom for X
"""

import uuid
from typing import TYPE_CHECKING

import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.solver.common.big_cube.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver

if TYPE_CHECKING:
    from cube.domain.model._part_slice import PartEdge


# =============================================================================
# Coordinate Translation Helpers
# =============================================================================

def ltr_to_center_index(face: Face, ltr_y: int, ltr_x: int) -> tuple[int, int]:
    """
    Translate LTR coordinates to center index coordinates.

    Args:
        face: The face to get index for
        ltr_y: Y in LTR system (0 = bottom, increases upward along left edge)
        ltr_x: X in LTR system (0 = left, increases rightward along bottom edge)

    Returns:
        (idx_row, idx_col) for use with face.center.get_center_slice()
    """
    # Use edge_left for Y → row translation
    idx_row = face.edge_left.get_slice_index_from_ltr_index(face, ltr_y)
    # Use edge_bottom for X → col translation
    idx_col = face.edge_bottom.get_slice_index_from_ltr_index(face, ltr_x)
    return idx_row, idx_col


def center_index_to_ltr(face: Face, idx_row: int, idx_col: int) -> tuple[int, int]:
    """
    Translate center index coordinates to LTR coordinates.

    Args:
        face: The face to get LTR for
        idx_row: Row index from get_center_slice()
        idx_col: Column index from get_center_slice()

    Returns:
        (ltr_y, ltr_x) in LTR system
    """
    ltr_y = face.edge_left.get_ltr_index_from_slice_index(face, idx_row)
    ltr_x = face.edge_bottom.get_ltr_index_from_slice_index(face, idx_col)
    return ltr_y, ltr_x


# =============================================================================
# Test Helper Functions
# =============================================================================

def _check_cube_state_preserved(cube: Cube) -> bool:
    """Check if cube state is preserved (edges and corners in position)."""
    # All edges should be reduced (3x3)
    edges_reduced = all(e.is3x3 for e in cube.edges)
    # All edges should be in correct position
    edges_positioned = all(e.match_faces for e in cube.edges)
    # All corners should be in correct position
    corners_positioned = all(corner.match_faces for corner in cube.corners)

    return edges_reduced and edges_positioned and corners_positioned


def _is_center_position(n_slices: int, ltr_y: int, ltr_x: int) -> bool:
    """
    Check if (ltr_y, ltr_x) is the exact center of the grid.

    For odd n_slices, the center is (mid, mid) which is invariant under rotation.
    The commutator algorithm cannot move the center piece.

    Args:
        n_slices: Number of center slices (cube_size - 2)
        ltr_y, ltr_x: Position in LTR coordinates

    Returns:
        True if this is the center position (for odd n_slices)
    """
    if n_slices % 2 == 0:
        return False  # Even grids have no single center
    mid = n_slices // 2
    return ltr_y == mid and ltr_x == mid


def _get_center_slice_edge_by_ltr(face: Face, ltr_y: int, ltr_x: int) -> "PartEdge":
    """
    Get the PartEdge for a center slice using LTR coordinates.

    Args:
        face: The face to get the slice from
        ltr_y: Y in LTR system (0 = bottom, increases upward)
        ltr_x: X in LTR system (0 = left, increases rightward)

    Returns:
        The PartEdge at that position
    """
    idx_row, idx_col = ltr_to_center_index(face, ltr_y, ltr_x)
    return face.center.get_center_slice((idx_row, idx_col)).edge


# =============================================================================
# Tests
# =============================================================================

@pytest.mark.parametrize("cube_size", [5, 7])
def test_create_helper(cube_size: int) -> None:
    """Create a cube and instantiate the helper via a solver."""
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
    solver = CageNxNSolver(app.op)
    helper = CommunicatorHelper(solver)

    assert helper.n_slices == cube_size - 2




@pytest.mark.parametrize("cube_size", [5, 7])
def test_communicator_supported_pairs(cube_size: int) -> None:
    """
    Test communicator for currently supported face pairs.

    For each source/target pair:
    - Iterate all (ltr_y, ltr_x) positions in LTR coordinates
    - For each of 4 rotations, compute source position
    - Place unique attribute on source
    - Execute communicator
    - Verify attribute moved to target
    - Verify cube state preserved
    """
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
    solver = CageNxNSolver(app.op)
    helper = CommunicatorHelper(solver)
    cube = app.cube
    n_slices = cube.n_slices

    # Verify initial cube state
    assert _check_cube_state_preserved(cube), "Initial cube state should be valid"

    # Use helper's announcement of supported pairs
    supported_pairs = helper.get_supported_pairs()

    for source_face, target_face in supported_pairs:

            for ltr_y in range(n_slices):
                for ltr_x in range(n_slices):
                    # Skip center position for odd cubes (invariant under rotation)
                    if _is_center_position(n_slices, ltr_y, ltr_x):
                        continue

                    for rotation in range(4):
                        # Get expected source LTR by mapping target → source
                        expected_src_ltr = helper.get_expected_source_ltr(
                            source_face, target_face, (ltr_y, ltr_x)
                        )
                        # Rotate on SOURCE face (physical rotation)
                        src_ltr_y, src_ltr_x = helper.rotate_ltr_on_face(
                            source_face, expected_src_ltr, rotation
                        )

                        # Create unique test attribute
                        test_key = f"test_{uuid.uuid4().hex[:8]}"
                        test_value = uuid.uuid4().hex

                        # Get the source center slice and set attribute (using LTR coords)
                        source_slice_edge = _get_center_slice_edge_by_ltr(
                            source_face, src_ltr_y, src_ltr_x
                        )
                        source_slice_edge.c_attributes[test_key] = test_value

                        # Call the communicator helper (with LTR coordinates)
                        helper.do_communicator(
                            source=source_face,
                            target=target_face,
                            target_block=((ltr_y, ltr_x), (ltr_y, ltr_x)),
                            source_block=((src_ltr_y, src_ltr_x), (src_ltr_y, src_ltr_x)),
                            preserve_state=True
                        )

                        # Verify attribute moved to target (using LTR coords)
                        target_slice_edge = _get_center_slice_edge_by_ltr(
                            target_face, ltr_y, ltr_x
                        )
                        assert test_key in target_slice_edge.c_attributes, \
                            f"Attribute should be on target ({target_face.name}, " \
                            f"ltr_y={ltr_y}, ltr_x={ltr_x})"
                        assert target_slice_edge.c_attributes[test_key] == test_value, \
                            "Attribute value should match on target"

                        # Verify attribute no longer on source
                        source_slice_edge = _get_center_slice_edge_by_ltr(
                            source_face, src_ltr_y, src_ltr_x
                        )
                        assert test_key not in source_slice_edge.c_attributes, \
                            f"Attribute should NOT be on source ({source_face.name}, " \
                            f"ltr_y={src_ltr_y}, ltr_x={src_ltr_x})"

                        # Verify cube state preserved
                        assert _check_cube_state_preserved(cube), \
                            f"Cube state should be preserved after communicator " \
                            f"(source={source_face.name}, target={target_face.name}, " \
                            f"pos=({ltr_y},{ltr_x}), rotation={rotation})"

                        # Clean up: remove the test attribute for next iteration
                        if test_key in target_slice_edge.c_attributes:
                            del target_slice_edge.c_attributes[test_key]


@pytest.mark.parametrize("cube_size", [5])
def test_communicator_simple_case(cube_size: int) -> None:
    """
    Simple test case: Front target, Up source, single position.
    This mirrors the old helper's default behavior.
    """
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
    solver = CageNxNSolver(app.op)
    helper = CommunicatorHelper(solver)
    cube = app.cube

    source_face = cube.up
    target_face = cube.front

    # Test position (0, 1) - NOT the center (center is invariant for odd cubes)
    # For 5x5 cube with 3x3 center, (1,1) is the exact center which can't be moved
    ltr_y, ltr_x = 0, 1
    src_ltr_y, src_ltr_x = ltr_y, ltr_x  # rotation=0, same position

    # Set test attribute
    test_key = "simple_test"
    test_value = "test_value_123"

    source_slice_edge = _get_center_slice_edge_by_ltr(source_face, src_ltr_y, src_ltr_x)
    source_slice_edge.c_attributes[test_key] = test_value

    # Execute communicator
    helper.do_communicator(
        source=source_face,
        target=target_face,
        target_block=((ltr_y, ltr_x), (ltr_y, ltr_x)),
        source_block=((src_ltr_y, src_ltr_x), (src_ltr_y, src_ltr_x)),
        preserve_state=True
    )

    # Verify
    target_slice_edge = _get_center_slice_edge_by_ltr(target_face, ltr_y, ltr_x)
    assert test_key in target_slice_edge.c_attributes
    assert target_slice_edge.c_attributes[test_key] == test_value

    # State should be preserved
    assert _check_cube_state_preserved(cube)
