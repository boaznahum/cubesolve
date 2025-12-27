"""Tests for edge coordinate system consistency per face.

This test verifies that for each face, all its edges agree on the ltr (left-to-right)
coordinate system. When we convert an ltr index to a slice index, the result should
be consistent across all edges of the same face.

See: Issue #53 - Two edges may not agree in face coordinate system
See: docs/design2/edge-coordinate-system.md
"""
import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.model.Face import Face
from cube.domain.model.Edge import Edge


def _check_edges_agree(face: Face, edge1: Edge, edge2: Edge, edge1_name: str, edge2_name: str) -> list[str]:
    """
    Check if two edges agree on the ltr coordinate system for a given face.

    For horizontal edges (top/bottom): ltr goes left-to-right
    For vertical edges (left/right): ltr goes bottom-to-top

    The key insight: if we ask both edges to convert the same ltr index
    for the same face, the behavior should be consistent - i.e., both should
    either invert or not invert, based on the face's coordinate system.

    Returns a list of error messages (empty if edges agree).
    """
    errors = []
    n_slices = edge1.n_slices

    # For each ltr index, check if both edges treat the face consistently
    for ltr_i in range(n_slices):
        # Get slice index from ltr for each edge
        slice_idx1 = edge1.get_slice_index_from_ltr_index(face, ltr_i)
        slice_idx2 = edge2.get_slice_index_from_ltr_index(face, ltr_i)

        # Check if both edges invert or both don't invert
        # They should both map ltr_i to slice index in the same way relative to the face
        inverted1 = (slice_idx1 != ltr_i)
        inverted2 = (slice_idx2 != ltr_i)

        if inverted1 != inverted2:
            errors.append(
                f"Face {face.name}: {edge1_name} and {edge2_name} disagree on ltr={ltr_i}. "
                f"{edge1_name} -> slice {slice_idx1} (inverted={inverted1}), "
                f"{edge2_name} -> slice {slice_idx2} (inverted={inverted2})"
            )

    return errors


@pytest.mark.parametrize("cube_size", [5, 7])
def test_edge_coordinate_consistency_per_face(cube_size: int):
    """
    Test that for each face, opposite edges agree on the ltr coordinate system.

    For a face:
    - top and bottom edges should agree (both horizontal)
    - left and right edges should agree (both vertical)
    """
    app = AbstractApp.create_non_default(cube_size, animation=False)
    cube = app.cube

    all_errors = []

    for face in cube.faces:
        # Check top/bottom edges agree
        errors = _check_edges_agree(
            face,
            face.edge_top, face.edge_bottom,
            "edge_top", "edge_bottom"
        )
        all_errors.extend(errors)

        # Check left/right edges agree
        errors = _check_edges_agree(
            face,
            face.edge_left, face.edge_right,
            "edge_left", "edge_right"
        )
        all_errors.extend(errors)

    if all_errors:
        error_msg = f"Edge coordinate inconsistencies found ({len(all_errors)} issues):\n"
        error_msg += "\n".join(f"  - {e}" for e in all_errors[:10])  # Show first 10
        if len(all_errors) > 10:
            error_msg += f"\n  ... and {len(all_errors) - 10} more"
        pytest.fail(error_msg)


@pytest.mark.parametrize("cube_size", [5, 7])
def test_all_edges_same_direction_consistency(cube_size: int):
    """
    Test that edges with right_top_left_same_direction=False have consistent
    f1/f2 assignment for each face they touch.

    For each face F that appears in edges with same_direction=False:
    - F should be consistently f1 in ALL such edges, OR
    - F should be consistently f2 in ALL such edges
    """
    app = AbstractApp.create_non_default(cube_size, animation=False)
    cube = app.cube

    # Track f1/f2 role for each face across all edges with same_direction=False
    face_roles: dict[str, set[str]] = {}  # face_name -> {"f1", "f2"}

    for edge in cube.edges:
        if not edge.right_top_left_same_direction:
            f1_name = edge._f1.name.value
            f2_name = edge._f2.name.value

            face_roles.setdefault(f1_name, set()).add("f1")
            face_roles.setdefault(f2_name, set()).add("f2")

    # Check for inconsistencies
    inconsistent_faces = []
    for face_name, roles in face_roles.items():
        if len(roles) > 1:
            inconsistent_faces.append(face_name)

    if inconsistent_faces:
        # Gather details for error message
        details = []
        for edge in cube.edges:
            if not edge.right_top_left_same_direction:
                f1_name = edge._f1.name.value
                f2_name = edge._f2.name.value
                details.append(f"  Edge {edge.name}: f1={f1_name}, f2={f2_name}")

        pytest.fail(
            f"Faces with inconsistent f1/f2 roles in same_direction=False edges: {inconsistent_faces}\n"
            f"Edge details:\n" + "\n".join(details)
        )
