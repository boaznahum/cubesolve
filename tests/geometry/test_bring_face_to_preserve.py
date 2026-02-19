"""
Tests for CommonOp.bring_face_to_preserve - bringing one face to another while preserving a third.

This tests constrained whole-cube rotations that keep one face fixed.

Test approach:
1. Place markers on source face center AND preserve face center
2. Call bring_face_to_preserve(target, source, preserve)
3. Verify source marker is now on target face
4. Verify preserve marker is still on preserve face (face didn't move)
"""

from __future__ import annotations

import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.exceptions import GeometryError, GeometryErrorCode
from cube.domain.geometric import cube_boy
from cube.domain.geometric.cube_layout import CubeLayout
from cube.domain.model.Cube import Cube
from cube.domain.model.FaceName import FaceName
from cube.domain.solver.common.CommonOp import CommonOp
from tests.test_utils import _test_sp


# =============================================================================
# Test Data - Generated from geometry layer (no hardcoded cycles)
# =============================================================================

CUBE_SIZES = [3, 5]


def _get_layout() -> CubeLayout:
    """Get a CubeLayout instance to query geometry."""
    return cube_boy.get_boy_layout(_test_sp)


def get_valid_combinations() -> list[tuple[FaceName, FaceName, FaceName]]:
    """Generate all valid (target, source, preserve) combinations.

    Valid when get_bring_face_alg_preserve doesn't raise.
    """
    layout = _get_layout()
    valid = []
    for preserve in FaceName:
        for source in FaceName:
            for target in FaceName:
                if source != target:
                    try:
                        layout.get_bring_face_alg_preserve(target, source, preserve)
                        valid.append((target, source, preserve))
                    except GeometryError:
                        pass  # Invalid combination
    return valid


def get_invalid_combinations() -> list[tuple[FaceName, FaceName, FaceName]]:
    """Generate invalid combinations (raises INVALID_PRESERVE_ROTATION)."""
    layout = _get_layout()
    invalid = []
    for preserve in FaceName:
        for source in FaceName:
            for target in FaceName:
                if source != target:
                    try:
                        layout.get_bring_face_alg_preserve(target, source, preserve)
                    except GeometryError as e:
                        if e.code == GeometryErrorCode.INVALID_PRESERVE_ROTATION:
                            invalid.append((target, source, preserve))
    return invalid


def get_same_face_combinations() -> list[tuple[FaceName, FaceName, FaceName]]:
    """Generate combinations where source == target (raises SAME_FACE)."""
    same = []
    for preserve in FaceName:
        for face in FaceName:
            if face != preserve:  # source/target can't be preserve face anyway
                same.append((face, face, preserve))
    return same


VALID_COMBINATIONS = get_valid_combinations()
INVALID_COMBINATIONS = get_invalid_combinations()
SAME_FACE = get_same_face_combinations()


def _valid_id(combo: tuple[FaceName, FaceName, FaceName]) -> str:
    target, source, preserve = combo
    return f"{source.name}->{target.name}_keep_{preserve.name}"


def _invalid_id(combo: tuple[FaceName, FaceName, FaceName]) -> str:
    target, source, preserve = combo
    return f"{source.name}->{target.name}_keep_{preserve.name}"


# =============================================================================
# Helper Functions
# =============================================================================

def create_common_op(cube_size: int) -> tuple[CommonOp, Cube]:
    """Create a CommonOp instance using app's built-in solver."""
    app = AbstractApp.create_app(cube_size=cube_size)
    return app.slv.cmn, app.op.cube


def place_marker(cube: Cube, face_name: FaceName, marker_value: str) -> None:
    """Place a test marker on the center of a face."""
    face = cube.face(face_name)
    center_slice = face.center.get_center_slice((0, 0))
    center_slice.edge.moveable_attributes["test_marker"] = marker_value


def find_marker_on_face(cube: Cube, face_name: FaceName) -> str | None:
    """Search all center slices on a face for a test marker."""
    face = cube.face(face_name)
    for center_slice in face.center.all_slices:
        marker = center_slice.edge.moveable_attributes.get("test_marker")
        if marker is not None:
            return marker
    return None


# =============================================================================
# Tests
# =============================================================================

class TestBringFaceToPreserveValid:
    """Tests for valid bring_face_to_preserve calls."""

    @pytest.mark.parametrize("cube_size", CUBE_SIZES)
    @pytest.mark.parametrize("combo", VALID_COMBINATIONS, ids=_valid_id)
    def test_bring_face_to_preserve(
        self, cube_size: int, combo: tuple[FaceName, FaceName, FaceName]
    ) -> None:
        """Test bring_face_to_preserve moves source while keeping preserve fixed."""
        target_name, source_name, preserve_name = combo
        cmn, cube = create_common_op(cube_size)

        # Create unique markers
        source_marker = f"SOURCE_{source_name.name}"
        preserve_marker = f"PRESERVE_{preserve_name.name}"

        # Place markers
        place_marker(cube, source_name, source_marker)
        place_marker(cube, preserve_name, preserve_marker)

        # Get face objects
        target_face = cube.face(target_name)
        source_face = cube.face(source_name)
        preserve_face = cube.face(preserve_name)

        # Call bring_face_to_preserve
        cmn.bring_face_to_preserve(target_face, source_face, preserve_face)

        # Verify source marker moved to target
        found_source = find_marker_on_face(cube, target_name)
        assert found_source == source_marker, (
            f"Source marker should be on {target_name}, found: {found_source}"
        )

        # Verify preserve marker stayed on preserve face
        found_preserve = find_marker_on_face(cube, preserve_name)
        assert found_preserve == preserve_marker, (
            f"Preserve face {preserve_name} should not have moved!"
        )


class TestBringFaceToPreserveSameFace:
    """Tests for source == target (should do nothing)."""

    @pytest.mark.parametrize("cube_size", CUBE_SIZES)
    @pytest.mark.parametrize("combo", SAME_FACE, ids=_invalid_id)
    def test_same_face_does_nothing(
        self, cube_size: int, combo: tuple[FaceName, FaceName, FaceName]
    ) -> None:
        """Test that bring_face_to_preserve does nothing when source == target."""
        target_name, source_name, preserve_name = combo
        cmn, cube = create_common_op(cube_size)

        face = cube.face(source_name)
        preserve_face = cube.face(preserve_name)

        # Place a marker to verify cube unchanged
        marker = "SAME_FACE_TEST"
        place_marker(cube, source_name, marker)

        # Should silently return, not raise
        cmn.bring_face_to_preserve(face, face, preserve_face)

        # Marker should still be on the same face
        assert find_marker_on_face(cube, source_name) == marker


class TestBringFaceToPreserveInvalid:
    """Tests for impossible rotations (should raise GeometryError)."""

    @pytest.mark.parametrize("cube_size", CUBE_SIZES)
    @pytest.mark.parametrize("combo", INVALID_COMBINATIONS, ids=_invalid_id)
    def test_invalid_rotation_raises(
        self, cube_size: int, combo: tuple[FaceName, FaceName, FaceName]
    ) -> None:
        """Test that bring_face_to_preserve raises when rotation is impossible."""
        target_name, source_name, preserve_name = combo
        cmn, cube = create_common_op(cube_size)

        target_face = cube.face(target_name)
        source_face = cube.face(source_name)
        preserve_face = cube.face(preserve_name)

        with pytest.raises(GeometryError) as exc_info:
            cmn.bring_face_to_preserve(target_face, source_face, preserve_face)

        assert exc_info.value.code == GeometryErrorCode.INVALID_PRESERVE_ROTATION
