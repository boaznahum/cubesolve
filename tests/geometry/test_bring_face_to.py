"""
Tests for CommonOp.bring_face_to - bringing one face to another position.

Tests all 36 face pair combinations:
- 30 valid pairs (source != target): verify face rotation works
- 6 invalid pairs (source == target): verify exception is raised

Test approach:
1. Place a marker on source face's center
2. Call bring_face_to(target, source)
3. Verify marker is now on target face's center
"""

from __future__ import annotations

from itertools import product

import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.exceptions import GeometryError, GeometryErrorCode
from cube.domain.model.Cube import Cube
from cube.domain.model.FaceName import FaceName
from cube.domain.solver.common.CommonOp import CommonOp


# =============================================================================
# Test Data
# =============================================================================

ALL_FACES = list(FaceName)
VALID_FACE_PAIRS = [(t, s) for t, s in product(ALL_FACES, ALL_FACES) if t != s]
SAME_FACE_PAIRS = [(f, f) for f in ALL_FACES]
CUBE_SIZES = [3, 5]


def _face_pair_id(pair: tuple[FaceName, FaceName]) -> str:
    return f"{pair[1].name}->{pair[0].name}"


def _same_face_id(pair: tuple[FaceName, FaceName]) -> str:
    return f"{pair[0].name}=={pair[1].name}"


# =============================================================================
# Helper Functions
# =============================================================================

def create_common_op(cube_size: int) -> tuple[CommonOp, Cube]:
    """Create a CommonOp instance using app's built-in solver."""
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
    return app.slv.cmn, app.op.cube


def place_marker(cube: Cube, face_name: FaceName, marker_value: str) -> None:
    """Place a test marker on the center of a face."""
    face = cube.face(face_name)
    # Use (0, 0) center slice to place a marker
    center_slice = face.center.get_center_slice((0, 0))
    center_slice.edge.c_attributes["test_marker"] = marker_value


def find_marker_on_face(cube: Cube, face_name: FaceName) -> str | None:
    """Search all center slices on a face for a test marker.

    After whole-cube rotation, the marker may be at any coordinate position
    on the target face, not necessarily at (0,0).
    """
    face = cube.face(face_name)
    for center_slice in face.center.all_slices:
        marker = center_slice.edge.c_attributes.get("test_marker")
        if marker is not None:
            return marker
    return None


# =============================================================================
# Tests
# =============================================================================

class TestBringFaceToValid:
    """Tests for valid bring_face_to calls (source != target)."""

    @pytest.mark.parametrize("cube_size", CUBE_SIZES)
    @pytest.mark.parametrize("face_pair", VALID_FACE_PAIRS, ids=_face_pair_id)
    def test_bring_face_to(
        self, cube_size: int, face_pair: tuple[FaceName, FaceName]
    ) -> None:
        """Test that bring_face_to correctly moves source face to target position.

        Verification:
        1. Place marker on source face center
        2. Call bring_face_to(target, source)
        3. Marker should now be on target face center
        """
        target_name, source_name = face_pair
        cmn, cube = create_common_op(cube_size)

        # Create unique marker for this test
        marker_value = f"MARKER_{source_name.name}_to_{target_name.name}"

        # Place marker on source face
        place_marker(cube, source_name, marker_value)

        # Get face objects
        target_face = cube.face(target_name)
        source_face = cube.face(source_name)

        # Call bring_face_to
        cmn.bring_face_to(target_face, source_face)

        # Verify marker is now on target face (search all center slices)
        found_marker = find_marker_on_face(cube, target_name)
        assert found_marker == marker_value, (
            f"bring_face_to({target_name}, {source_name}) failed!\n"
            f"  Expected marker '{marker_value}' on {target_name}\n"
            f"  Found: {found_marker}"
        )


class TestBringFaceToSameFace:
    """Tests for invalid bring_face_to calls (source == target)."""

    @pytest.mark.parametrize("cube_size", CUBE_SIZES)
    @pytest.mark.parametrize("face_pair", SAME_FACE_PAIRS, ids=_same_face_id)
    def test_bring_face_to_same_raises(
        self, cube_size: int, face_pair: tuple[FaceName, FaceName]
    ) -> None:
        """Test that bring_face_to raises GeometryError when source == target."""
        face_name = face_pair[0]
        cmn, cube = create_common_op(cube_size)

        face = cube.face(face_name)

        with pytest.raises(GeometryError) as exc_info:
            cmn.bring_face_to(face, face)

        assert exc_info.value.code == GeometryErrorCode.SAME_FACE, (
            f"Expected SAME_FACE error code, got {exc_info.value.code}"
        )
