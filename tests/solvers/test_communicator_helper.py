"""
Tests for CommunicatorHelper.

Test structure:
- Iterate all source/target face pairs
- For each (y, x) position in BULR coordinates
- For each of 4 rotations, get source position
- Set a unique attribute on source piece
- Call the communicator helper
- Verify attribute moved to target, not on source
- Verify cube state preserved (edges in position)
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


def _get_all_faces(cube: Cube) -> list[Face]:
    """Get all 6 faces of the cube."""
    return [cube.front, cube.back, cube.up, cube.down, cube.left, cube.right]


def _check_cube_state_preserved(cube: Cube) -> bool:
    """Check if cube state is preserved (edges and corners in position)."""
    # All edges should be reduced (3x3)
    edges_reduced = all(e.is3x3 for e in cube.edges)
    # All edges should be in correct position
    edges_positioned = all(e.match_faces for e in cube.edges)
    # All corners should be in correct position
    corners_positioned = all(corner.match_faces for corner in cube.corners)

    return edges_reduced and edges_positioned and corners_positioned


def _get_center_slice_edge(face: Face, row: int, col: int) -> "PartEdge":
    """Get the PartEdge for a center slice at (row, col)."""
    return face.center.get_center_slice((row, col)).edge


@pytest.mark.parametrize("cube_size", [5, 7])
def test_create_helper(cube_size: int) -> None:
    """Create a cube and instantiate the helper via a solver."""
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
    solver = CageNxNSolver(app.op)
    helper = CommunicatorHelper(solver)

    assert helper.n_slices == cube_size - 2


@pytest.mark.parametrize("cube_size", [5, 7])
def test_communicator_all_face_pairs(cube_size: int) -> None:
    """
    Test communicator for all face pairs with single piece blocks.

    For each source/target pair:
    - Iterate all (y, x) positions
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

    all_faces = _get_all_faces(cube)

    # Verify initial cube state
    assert _check_cube_state_preserved(cube), "Initial cube state should be valid"

    for source_face in all_faces:
        for target_face in all_faces:
            if source_face is target_face:
                continue

            for y in range(n_slices):
                for x in range(n_slices):
                    for rotation in range(4):
                        # Get source position by rotating target position
                        sy, sx = cube.cqr.rotate_point_clockwise((y, x), rotation)

                        # Create unique test attribute
                        test_key = f"test_{uuid.uuid4().hex[:8]}"
                        test_value = uuid.uuid4().hex

                        # Get the source center slice and set attribute
                        source_slice_edge = _get_center_slice_edge(source_face, sy, sx)
                        source_slice_edge.c_attributes[test_key] = test_value

                        # Call the communicator helper
                        helper.do_communicator(
                            source=source_face,
                            target=target_face,
                            target_block=((y, x), (y, x)),  # Single piece block
                            source_block=((sy, sx), (sy, sx)),
                            preserve_state=True
                        )

                        # Verify attribute moved to target
                        target_slice_edge = _get_center_slice_edge(target_face, y, x)
                        assert test_key in target_slice_edge.c_attributes, \
                            f"Attribute should be on target ({target_face.name}, {y}, {x})"
                        assert target_slice_edge.c_attributes[test_key] == test_value, \
                            "Attribute value should match on target"

                        # Verify attribute no longer on source
                        source_slice_edge = _get_center_slice_edge(source_face, sy, sx)
                        assert test_key not in source_slice_edge.c_attributes, \
                            f"Attribute should NOT be on source ({source_face.name}, {sy}, {sx})"

                        # Verify cube state preserved
                        assert _check_cube_state_preserved(cube), \
                            f"Cube state should be preserved after communicator " \
                            f"(source={source_face.name}, target={target_face.name}, " \
                            f"pos=({y},{x}), rotation={rotation})"

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

    # Test position (1, 1) - middle area on 5x5
    y, x = 1, 1
    sy, sx = y, x  # rotation=0, same position

    # Set test attribute
    test_key = "simple_test"
    test_value = "test_value_123"

    source_slice_edge = _get_center_slice_edge(source_face, sy, sx)
    source_slice_edge.c_attributes[test_key] = test_value

    # Execute communicator
    helper.do_communicator(
        source=source_face,
        target=target_face,
        target_block=((y, x), (y, x)),
        source_block=((sy, sx), (sy, sx)),
        preserve_state=True
    )

    # Verify
    target_slice_edge = _get_center_slice_edge(target_face, y, x)
    assert test_key in target_slice_edge.c_attributes
    assert target_slice_edge.c_attributes[test_key] == test_value

    # State should be preserved
    assert _check_cube_state_preserved(cube)
