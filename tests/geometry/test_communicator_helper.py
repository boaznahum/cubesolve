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
from tabulate import tabulate

from cube.application.AbstractApp import AbstractApp
from cube.domain.algs import Algs
from cube.domain.geometric.cube_boy import FaceName
from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.model.SliceName import SliceName
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.common.big_cube.commun._supported_faces import _get_supported_pairs
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver

# Get supported pairs for parametrization
SUPPORTED_PAIRS = _get_supported_pairs()


def _face_pair_id(pair: tuple[FaceName, FaceName]) -> str:
    """Generate readable test ID for face pair (target<-source)."""
    source, target = pair
    return f"{target.name}<-{source.name}"


if TYPE_CHECKING:
    from cube.domain.model.PartSlice import PartEdge


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
    """Check if edges and corners form a consistent solved-like state.

    WHY NOT USE match_faces?
    ========================
    The obvious approach would be to use Part.match_faces which checks if
    edge/corner colors match their face colors. However, match_faces uses
    face.color which reads from center position (n_slices//2, n_slices//2).

    On even cubes (4x4, 6x6, etc.), this is just ONE of several center pieces.
    When the commutator algorithm moves that specific center piece to another
    face, face.color changes! This causes match_faces to return False even
    though the edges and corners are completely undisturbed.

    Example on 4x4 cube:
    - Before: U face has Yellow centers, face.color = YELLOW
    - Commutator moves center at (1,1) from U to F
    - After: U face.color = BLUE (reads the piece now at position (1,1))
    - Edge on U still has YELLOW sticker
    - match_faces compares YELLOW != BLUE → returns False (WRONG!)

    THE SOLUTION: RELATIVE CONSISTENCY
    ==================================
    Instead of comparing to face colors, check that edges and corners are
    consistent WITH EACH OTHER - like a human would verify a solved cube.

    For each corner (which has 3 colors on 3 faces):
    - Find the 3 edges adjacent to this corner
    - Each edge shares 2 faces with the corner
    - The edge's colors on those faces must match the corner's colors

    Example: Corner at F-U-L has colors (Blue, Yellow, Orange)
    - F-U edge must have Blue on F, Yellow on U
    - F-L edge must have Blue on F, Orange on L
    - U-L edge must have Yellow on U, Orange on L

    If all these relationships hold, the edges and corners are in a valid
    solved configuration - regardless of what the center pieces show.
    """
    # All edges should be reduced (is3x3)
    if not all(e.is3x3 for e in cube.edges):
        return False

    # For each corner, check that adjacent edges have matching colors
    for corner in cube.corners:
        corner_edges = corner._3x3_representative_edges  # 3 PartEdges

        # Check each pair of faces on this corner
        for i in range(3):
            for j in range(i + 1, 3):
                face_i = corner_edges[i].face
                face_j = corner_edges[j].face
                corner_color_on_i = corner_edges[i].color
                corner_color_on_j = corner_edges[j].color

                # Find the edge shared by face_i and face_j
                shared_edge = face_i.find_shared_edge(face_j)
                if shared_edge is None:
                    continue  # Shouldn't happen, but be safe

                # Check edge colors match corner colors on those faces
                edge_color_on_i = shared_edge.get_face_edge(face_i).color
                edge_color_on_j = shared_edge.get_face_edge(face_j).color

                if edge_color_on_i != corner_color_on_i or edge_color_on_j != corner_color_on_j:
                    return False

    return True


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


# =============================================================================
# Tests
# =============================================================================

@pytest.mark.parametrize("cube_size", [4, 7])  # Even cubes have known inner 2x2 issues
def test_create_helper(cube_size: int) -> None:
    """Create a cube and instantiate the helper via a solver."""
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
    solver = CageNxNSolver(app.op)
    helper = CommunicatorHelper(solver)

    assert helper.n_slices == cube_size - 2


@pytest.mark.parametrize("cube_size", range(3, 9))  # All cube sizes
@pytest.mark.parametrize("face_pair", SUPPORTED_PAIRS, ids=_face_pair_id)
def test_communicator_supported_pairs(cube_size: int, face_pair: tuple[FaceName, FaceName]) -> None:
    """
    Test communicator for a specific face pair using the new execute_communicator API.

    VALIDATES THE 3-CYCLE PATTERN: s1 → t → s2 → s1
    ==================================================
    The block communicator moves exactly 3 pieces in a cycle:
    - s1: source point (natural source position)
    - t: target point (target block position)
    - s2: intermediate point (computed via target rotation on source face)

    For the given source/target pair:
    - Iterate all translation results (1 for adjacent, 2 for opposite faces)
    - Iterate all (ltr_y, ltr_x) positions in LTR coordinates
    - For each of 4 rotations, compute source position via execute_communicator (dry_run)
    - Place unique attribute on source piece
    - Execute communicator with new API
    - VERIFY 3-CYCLE POINTS: s1, t, s2 are correctly computed
    - Verify attribute moved from s1 to t (via s2)
    - Verify cube state preserved

    Known Limitations (Even Cubes):
    - Inner 2x2 positions may fail with M-slice sources (Up/Down/Back) due to
      M slice gap < 2. These positions work with E-slice sources (Left/Right).
    - Position (n//2, n//2) is truly unsupported by ALL sources.
    """
    source_face_name, target_face_name = face_pair

    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
    solver = CageNxNSolver(app.op)
    helper = CommunicatorHelper(solver)
    cube = app.cube
    n_slices = cube.n_slices

    # Determine how many translation results to iterate.
    # Adjacent faces have 1 result, opposite faces have 2 (one per axis).
    # We iterate ALL results to ensure no bugs are hidden by lucky ordering.
    is_adjacent = cube.layout.is_adjacent(source_face_name, target_face_name)
    result_count = 1 if is_adjacent else 2

    # Collect all failures and successes
    failures: list[dict[str, object]] = []
    successes: list[dict[str, object]] = []

    # Verify initial cube state
    assert _check_cube_state_preserved(cube), "Initial cube state should be valid"

    # Iterate over all translation results.
    # For opposite faces, there are 2 valid results (one per axis) - test BOTH
    # to ensure no bugs are hidden by lucky ordering.
    for result_index in range(result_count):
        # Set the class variable to select which result to use
        CommunicatorHelper._test_result_index = result_index

        for ltr_y in range(n_slices):
            for ltr_x in range(n_slices):
                # Skip center position for odd cubes (invariant under rotation)
                if _is_center_position(n_slices, ltr_y, ltr_x):
                    continue

                source_face: Face = cube.face(source_face_name)
                target_face: Face = cube.face(target_face_name)

                target_point = (ltr_y, ltr_x)

                # Use NEW API: execute_communicator with dry_run to get natural source
                # and the 3-cycle points (s1, t, s2) WITHOUT modifying the cube
                target_block = (target_point, target_point)

                for rotation in range(4):
                    # Reset cube to pristine state for each test iteration
                    cube = app.cube
                    cube.reset()
                    solver = CageNxNSolver(app.op)
                    helper = CommunicatorHelper(solver)

                    # Re-get faces from reset cube
                    source_face = cube.face(source_face_name)
                    target_face = cube.face(target_face_name)

                    target_block = (target_point, target_point)

                    # Get the cycle points from dry_run
                    dry_result = helper.execute_communicator(
                        source_face=source_face,
                        target_face=target_face,
                        target_block=target_block,
                        dry_run=True
                    )

                    # if dry_result.slice_name is not SliceName.M:
                    #     continue

                    # but we should also rotate source point
                    source_point = dry_result.source_point  # Natural source position
                    assert target_point == dry_result.target_point
                    second_replaced_with_target_point_on_source = dry_result.second_replaced_with_target_point_on_source  # Intermediate position on source

                    # When we rotate the natural source, we also rotate s1 and s2 (both on source)
                    rotated_s1 = cube.cqr.rotate_point_clockwise(source_point, rotation)
                    rotated_s2 = cube.cqr.rotate_point_clockwise(second_replaced_with_target_point_on_source, rotation)
                    # t_point stays the same (on target face)

                    # ================================================================
                    # PLACE UNIQUE MARKERS ON ALL 3 CYCLE POINTS
                    # ================================================================
                    marker_source_key = f"marker_s1_{uuid.uuid4().hex[:8]}"
                    marker_source_value = f"s1_{uuid.uuid4().hex[:4]}"

                    marker_target_key = f"marker_t_{uuid.uuid4().hex[:8]}"
                    marker_target_value = f"t_{uuid.uuid4().hex[:4]}"

                    marker_second_key = f"marker_s2_{uuid.uuid4().hex[:8]}"
                    marker_second_value = f"s2_{uuid.uuid4().hex[:4]}"

                    # Mark s1 on source face
                    source_point_piece = source_face.center.get_center_slice(source_point).edge
                    source_point_piece.c_attributes[marker_source_key] = marker_source_value

                    # Mark t on target face
                    target_point_piece = target_face.center.get_center_slice(target_point).edge
                    target_point_piece.c_attributes[marker_target_key] = marker_target_value

                    # Mark s2 on source face
                    second_source_point_piece = (
                        source_face.center.get_center_slice(second_replaced_with_target_point_on_source).edge)
                    second_source_point_piece.c_attributes[marker_second_key] = marker_second_value

                    # ================================================================
                    # EXECUTE COMMUNICATOR
                    # ================================================================
                    result = helper.execute_communicator(
                        source_face=source_face,
                        target_face=target_face,
                        target_block=target_block,
                        source_block=(source_point, source_point),
                        preserve_state=True,
                        dry_run=False
                    )

                    alg = result.algorithm or Algs.NOOP

                    # Check cube state using relative consistency (not face.color)
                    state_preserved = _check_cube_state_preserved(cube)

                    # Common record data
                    record = {
                        "rotation": rotation,
                        "target_point": target_point,
                        "natural_source_point": result.natural_source,
                        "source_point": result.natural_source,
                        "second_point_on_source": second_replaced_with_target_point_on_source,
                        "rotated_s1": rotated_s1,
                        "rotated_s2": rotated_s2,
                        "alg": alg,
                    }

                    # ================================================================
                    # VALIDATE 3-CYCLE: s1 → t → s2 → s1
                    # ================================================================
                    if not state_preserved:
                        failures.append({**record, "type": "state_not_preserved"})
                        continue

                    # Check marker_s1: should move from s1 to t
                    target_point_piece = target_face.center.get_center_slice(target_point).edge
                    if marker_source_key not in target_point_piece.c_attributes:
                        failures.append({**record, "type": "marker_s1_not_at_t"})
                        continue
                    if target_point_piece.c_attributes[marker_source_key] != marker_source_value:
                        failures.append({**record, "type": "marker_s1_value_mismatch"})
                        continue

                    # Check marker_t: should move from t to s2
                    # SEARCH for where marker_t actually ended up
                    marker_t_found_location = None
                    marker_t_found_on_face = None

                    # Search on source face
                    for search_y in range(n_slices):
                        for search_x in range(n_slices):
                            search_point = (search_y, search_x)
                            search_piece = source_face.center.get_center_slice(search_point).edge
                            if marker_target_key in search_piece.c_attributes:
                                marker_t_found_location = search_point
                                marker_t_found_on_face = "SOURCE"
                                break
                        if marker_t_found_location:
                            break

                    # Search on target face if not found on source
                    if not marker_t_found_location:
                        for search_y in range(n_slices):
                            for search_x in range(n_slices):
                                search_point = (search_y, search_x)
                                search_piece = target_face.center.get_center_slice(search_point).edge
                                if marker_target_key in search_piece.c_attributes:
                                    marker_t_found_location = search_point
                                    marker_t_found_on_face = "TARGET"
                                    break
                            if marker_t_found_location:
                                break

                    record["marker_t_found_location"] = marker_t_found_location
                    record["marker_t_found_on_face"] = marker_t_found_on_face

                    second_source_point_piece = source_face.center.get_center_slice(second_replaced_with_target_point_on_source).edge
                    if marker_target_key not in second_source_point_piece.c_attributes:
                        failures.append({**record, "type": "marker_t_not_at_s2"})
                        continue
                    if second_source_point_piece.c_attributes[marker_target_key] != marker_target_value:
                        failures.append({**record, "type": "marker_t_value_mismatch"})
                        continue

                    # Check marker_s2: should move from s2 back to s1
                    source_point_piece = source_face.center.get_center_slice(source_point).edge
                    if marker_second_key not in source_point_piece.c_attributes:
                        failures.append({**record, "type": "marker_s2_not_at_s1"})
                        continue
                    if source_point_piece.c_attributes[marker_second_key] != marker_second_value:
                        failures.append({**record, "type": "marker_s2_value_mismatch"})
                        continue

                    # Verify markers are NOT in their original positions (they moved!)
                    # marker_s1 original position was s1 (on source face)
                    source_point_piece = source_face.center.get_center_slice(source_point).edge
                    if marker_source_key in source_point_piece.c_attributes:
                        failures.append({**record, "type": "marker_s1_still_on_original_s1"})
                        continue

                    # marker_t original position was t (on target face)
                    target_point_piece = target_face.center.get_center_slice(target_point).edge
                    if marker_target_key in target_point_piece.c_attributes:
                        failures.append({**record, "type": "marker_t_still_on_original_t"})
                        continue

                    # marker_s2 original position was s2 (on source face)
                    second_source_point_piece = source_face.center.get_center_slice(second_replaced_with_target_point_on_source).edge
                    if marker_second_key in second_source_point_piece.c_attributes:
                        failures.append({**record, "type": "marker_s2_still_on_original_s2"})
                        continue

                    # All checks passed - record success
                    # Add marker_t location info (should be at rotated_s2 on source face)
                    record["marker_t_found_on_face"] = "SOURCE"
                    record["marker_t_found_location"] = rotated_s2
                    successes.append({**record, "type": "OK_3CYCLE"})

    # At end of test, report all failures in a table
    if failures:
        # Get target points that have failures
        failed_targets = {f['target_point'] for f in failures}

        # Get successes for failed target points
        relevant_successes = [s for s in successes if s['target_point'] in failed_targets]

        # Combine failures and successes, sort by target point then type (failures first) then rotation
        all_records = failures + relevant_successes
        all_records.sort(key=lambda x: (
            x['target_point'],
            0 if x['type'] != "OK" else 1,  # Failures before successes
            x['rotation']
        ))

        # Build failure table using tabulate
        header = f"Cube size={cube_size}, {source_face_name.name} -> {target_face_name.name}"

        # Build table rows, inserting separator rows between target point groups
        table_data: list[list[object]] = []
        prev_target: object = None
        for r in all_records:
            # Add separator between different target points
            if prev_target is not None and r['target_point'] != prev_target:
                table_data.append(["---"] * 9)  # 9 columns
            prev_target = r['target_point']

            marker_t_found_on_face = r.get('marker_t_found_on_face', '?')
            marker_t_found_location = r.get('marker_t_found_location', '?')



            table_data.append([
                r['type'],
                r['target_point'],
                r['rotation'],
                r['source_point'],
                f"{marker_t_found_on_face}:{marker_t_found_location}",
                r['second_point_on_source'],
                r['rotated_s1'],
                r['rotated_s2'],
            ])

        # Use multi-line headers to keep table narrow
        headers = ["Type", "Target\nPoint", "Rot", "s1", "t\n(Target)", "Marker_T\nFound", "s2\n(Computed)", "Rotated\nS1", "Rotated\nS2"]
        table_str = tabulate(table_data, headers=headers, tablefmt="simple")

        msg = f"\n{header}\n{'=' * len(header)}\n{table_str}\n\nTotal failures: {len(failures)}"
        assert False, msg


@pytest.mark.parametrize("cube_size", [5])
def test_communicator_raises_on_incompatible_blocks(cube_size: int) -> None:
    """
    Test that ValueError is raised when source block cannot be mapped
    to target block with 0-3 rotations.

    On a 3x3 center grid (5x5 cube), corner positions (0,0) and edge
    positions (0,1) are in different rotation orbits and cannot be aligned.
    """
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
    solver = CageNxNSolver(app.op)
    helper = CommunicatorHelper(solver)
    cube = app.cube

    source_face = cube.up
    target_face = cube.front

    # Target at corner position (0,0) - corner orbit: (0,0)→(2,0)→(2,2)→(0,2)
    # Source at edge position (0,1) - edge orbit: (0,1)→(1,0)→(2,1)→(1,2)
    # These are in different rotation orbits and cannot be aligned

    target_block = ((0, 0), (0, 0))  # Corner in LTR
    source_block = ((0, 1), (0, 1))  # Edge in LTR (different orbit)

    with pytest.raises(ValueError, match="Cannot align"):
        helper.do_communicator(
            source_face=source_face,
            target_face=target_face,
            target_block=target_block,
            source_block=source_block,
            preserve_state=True
        )
