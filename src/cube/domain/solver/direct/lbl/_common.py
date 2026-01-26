"""Common utilities for LBL (Layer-By-Layer) NxN solver.

This module contains shared context managers and helper functions used
by multiple LBL solver components (NxNCenters2, _LBLSlices, etc.).

MARKER SYSTEM DOCUMENTATION
===========================

This module uses THREE distinct marker systems for center-piece tracking:

┌─────────────────────────────────────────────────────────────────────────────┐
│ MARKER 1: VISUAL CHECKMARK (Visualization Only)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Purpose:   Display green checkmark on solved pieces in GUI                  │
│ Storage:   MarkerManager.add_marker(edge, "checkmark", ...)                 │
│ Set by:    _mark_slice_with_v_mark_if_solved() when PUT_SOLVED_MARKERS=True │
│ Cleared:   Managed by MarkerManager lifecycle (not cleared here)            │
│ Used for:  User feedback only - NOT used by solver algorithm                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ MARKER 2: SOLVED FLAG (Solver Algorithm)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ Purpose:   Track which pieces are solved to avoid destroying them           │
│ Storage:   piece.edge.moveable_attributes["NxNCenters2_center_pice_solved"] │
│            = True                                                           │
│ Set by:    _mark_piece_solved() [via _mark_slice_with_v_mark_if_solved()]   │
│ Checked:   _is_cent_piece_solved()                                          │
│ Cleared:   Persists until cube reset - NOT cleared during solving           │
│ Used for:  Algorithm uses this to skip already-solved pieces and avoid      │
│            destroying them when moving other pieces                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ MARKER 3: ROW TRACKING (Solver Algorithm)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Purpose:   Track which center slices belong to current row being solved     │
│ Storage:   cs.moveable_attributes[__CENTER_SLICE_TRACK_KEY] = column_index  │
│ Key:       __CENTER_SLICE_TRACK_KEY (UUID generated at module load)         │
│ Set by:    _track_center_slice(cs, column)                                  │
│ Checked:   _is_center_slice() returns column or None                        │
│ Cleared:   clear_center_slice() / clear_all_tracking() in setup_l1 finally  │
│ Used for:  _iterate_all_tracked_slices_index() yields Points of tracked     │
│            slices for the algorithm to process                              │
└─────────────────────────────────────────────────────────────────────────────┘

LIFECYCLE DIAGRAM
=================

    setup_l1() context manager
         │
         ├─── position_l1()          # Position white face down
         │
         │    ┌─────────────────────────────────────────────┐
         │    │ For each row slice:                         │
         │    │                                             │
         │    │   _track_row_slices() context               │
         │    │        │                                    │
         │    │        ├── _track_center_slice()            │
         │    │        │   (set MARKER 3 on all row slices) │
         │    │        │                                    │
         │    │        ├── _mark_slice_with_v_mark_if_      │
         │    │        │   solved()                         │
         │    │        │   (set MARKER 1 + MARKER 2)        │
         │    │        │                                    │
         │    │        └── NOTE: MARKER 3 NOT cleared here! │
         │    │            (accumulates for protection)     │
         │    └─────────────────────────────────────────────┘
         │
         └─── finally: clear_all_tracking()   # Clear all MARKER 3
                       (MARKER 2 persists!)

WHY MARKER 2 AND 3 ARE SEPARATE:
================================
- MARKER 2 (solved flag): Persists forever. Tracks "this piece is in final
  position". Never cleared during solving - ensures solved pieces are never
  accidentally destroyed by later operations.

- MARKER 3 (row tracking): Temporary per-solving-session. Tracks "which slices
  am I currently working on". Cleared when all rows are done. Used to iterate
  over pieces that need processing.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from itertools import chain
from typing import TYPE_CHECKING, Iterable, Sequence, Any, Generator

from cube.domain.geometric.geometry_types import Point
from cube.domain.model import CenterSlice, PartSlice, EdgeWing, Face
from cube.domain.model.Cube import Cube
from cube.domain.model.Slice import Slice
from cube.domain.solver.direct.lbl import _lbl_config
from cube.domain.solver.direct.lbl._lbl_config import PUT_SOLVED_MARKERS
from cube.domain.tracker.FacesTrackerHolder import FacesTrackerHolder

_V_CHECKMARK = "checkmark"

if TYPE_CHECKING:
    from cube.domain.solver.common.SolverHelper import SolverHelper
    from cube.domain.tracker.trackers import FaceTracker


# =============================================================================
# Clear all types of markers
# =============================================================================

def clear_all_type_of_markers(cube: Cube) -> None:
    """Clear all types of markers from the cube (MARKER 2 + MARKER 3)."""
    clear_all_center_slices_tracking(cube)
    clear_solved_markers(cube)

# =============================================================================
# MARKER 2: SOLVED FLAG (Solver Algorithm)
# =============================================================================
# Tracks which pieces are solved to avoid destroying them.
# Persists until cube reset.

__SOLVED_FLAG_KEY = "NxNCenters2_center_pice_solved"


def _is_cent_piece_marked_solved(center_piece: CenterSlice) -> bool:
    """Check if a center-piece is marked as solved (MARKER 2)."""
    return is_slice_solved(center_piece)

def is_slice_solved(part_slice: PartSlice) -> bool:
    """Check if a center-piece is marked as solved (MARKER 2)."""

    # it is enough to search in one edge, they ar enver get apart
    return __SOLVED_FLAG_KEY in part_slice.edges[0].moveable_attributes


def _mark_piece_solved(piece: PartSlice) -> None:
    """Mark a piece as solved in the algorithm (MARKER 2).

    This is solver data, not visualization.
    """
    for edge in piece.edges:
        edge.moveable_attributes[__SOLVED_FLAG_KEY] = True


def clear_solved_markers(cube: Cube) -> None:
    """Clear all solved flags (MARKER 2) from all pieces in the cube.

    This clears the algorithm markers from centers, edges, and corners.

    """

    mm = cube.sp.marker_manager

    _PUT_SOLVED_MARKERS = PUT_SOLVED_MARKERS

    for part_slice in cube.get_all_part_slices():
        for edge in part_slice.edges:
            edge.moveable_attributes.pop(__SOLVED_FLAG_KEY, None)

            if _PUT_SOLVED_MARKERS:
                mm.remove_marker(edge,_V_CHECKMARK, moveable=True)




# =============================================================================
# MARKER 1 + MARKER 2 COMBINED: Visual Checkmark + Solved Flag
# =============================================================================
# These functions set both visual markers (if enabled) and algorithm markers.


def mark_slices_and_v_mark_if_solved(pieces: Iterable[PartSlice]) -> None:

    for part_slice in pieces:
        mark_slice_and_v_mark_if_solved(part_slice)

def mark_slice_and_v_mark_if_solved(piece: PartSlice) -> bool:
    """Mark a piece with visual checkmark (MARKER 1) and solved flag (MARKER 2).

    Only marks if piece.match_faces is True (piece is in correct position).

    Returns:
        True if piece was solved and marked, False otherwise.
    """
    if not piece.match_faces:
        return False

    # MARKER 1: Visual checkmark (only if enabled)
    if PUT_SOLVED_MARKERS:
        cube = piece.cube

        mf = cube.sp.marker_factory
        mm = cube.sp.marker_manager

        checkmark = mf.checkmark()  # Green checkmark

        # visualization only
        for edge in piece.edges:
            mm.add_marker(edge, _V_CHECKMARK, checkmark, moveable=True)

    # MARKER 2: Algorithm solved flag
    _mark_piece_solved(piece)

    return True



# =============================================================================
# MARKER 3: ROW TRACKING (Solver Algorithm)
# =============================================================================
# Tracks which center slices belong to current row being solved.
# Temporary - cleared when all rows are done.

__CENTER_SLICE_TRACK_KEY = str(uuid.uuid4())


def _track_center_slice(cs: CenterSlice, column: int) -> None:
    # boaz remove column it is not used, change from int to bool
    """Mark a center slice as being tracked for the current row (MARKER 3)."""
    cs.moveable_attributes[__CENTER_SLICE_TRACK_KEY] = 0


def _is_center_slice(cs: CenterSlice) -> bool:

    # boaz remove column it is not used

    """Check if a center slice is tracked and return its column (MARKER 3).

    Returns:
        Column index if tracked, None otherwise.
    """
    # the default is boolean False !!!
    x = cs.moveable_attributes[__CENTER_SLICE_TRACK_KEY]

    #boaz: becuase damm moveable_attributes has default bool !!!
    if type(x) is int:
        return True
    else:
        return False


def clear_center_slice(cs: CenterSlice) -> None:
    """Clear tracking marker from a single center slice (MARKER 3)."""
    cs.moveable_attributes.pop(__CENTER_SLICE_TRACK_KEY, None)


def _clear_is_center_slice(cs: CenterSlice) -> None:
    """Alias for clear_center_slice."""
    clear_center_slice(cs)


def clear_all_center_slices_tracking(cube: Cube) -> None:
    """Clear all center slice tracking markers from the cube (MARKER 3)."""
    for c in cube.centers:
        for cc in c.all_slices:
            clear_center_slice(cc)


def _iterate_all_tracked_center_slices_index(target_face: FaceTracker) -> Iterator[Point]:
    """Iterate over all tracked center slices on a face (MARKER 3).

    Yields:
        Point for each center slice that has tracking marker set.
    """
    for cs in target_face.face.center.all_slices:
        if _is_center_slice(cs):  # BUG FIX: was "is not None" which is always True
            rc = cs.index
            yield Point(*rc)


# =============================================================================
# UTILITY FUNCTIONS (Not marker-related)
# =============================================================================


def position_l1(slv: SolverHelper, l1_white_tracker: FaceTracker) -> None:
    """Position L1 (white face) down.

    Args:
        slv: Solver element providing access to cmn.bring_face_down
        l1_white_tracker: The Layer 1 face tracker to position down
    """
    slv.cmn.bring_face_down(l1_white_tracker.face)
    assert l1_white_tracker.face is slv.cube.down


class setup_l1:
    """Context manager for L1 position setup and tracking lifecycle.

    Positions L1 (white face) down for solving. Tracking is accumulated
    during solving (via _track_row_slices) and cleared only here when
    all slices are done. This protects solved pieces from being destroyed.

    Usage:
        with setup_l1(slv, l1_tracker) as l1_setup:
            # ... solve slices ...
            if parity_detected:
                l1_setup.realign()  # Re-position L1 after parity changed orientation
    """

    __slots__ = ["_slv", "_l1_tracker"]

    def __init__(self, slv: SolverHelper, l1_white_tracker: FaceTracker) -> None:
        self._slv = slv
        self._l1_tracker = l1_white_tracker

    def __enter__(self) -> "setup_l1":
        position_l1(self._slv, self._l1_tracker)
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        clear_all_center_slices_tracking(self._slv.cube)

    def realign(self) -> None:
        """Re-position L1 down after cube orientation changed (e.g., after parity fix)."""
        position_l1(self._slv, self._l1_tracker)


def _get_side_face_trackers(
        th: FacesTrackerHolder, l1_tracker: FaceTracker
) -> list[FaceTracker]:
    """Get trackers for side faces (not Layer 1 or its opposite).

    Args:
        th: FacesTrackerHolder with all 6 face trackers
        l1_tracker: The Layer 1 face tracker (to exclude with its opposite)

    Returns:
        List of 4 side face trackers
    """
    l1_opposite_face = l1_tracker.face.opposite
    side_trackers = [t for t in th.trackers
                     if t.face is not l1_tracker.face and t.face is not l1_opposite_face]


    # boaz: a patch to make bug reproducable even if we switch solution to diffrent trackers
    # Sort by color name to ensure consistent processing order
    if _lbl_config.PATCH_ORDER_ORTHOGONAL_FACES:
        return sorted(side_trackers, key=lambda t: t.color.name)


def _get_row_pieces(cube, l1_tracker: FaceTracker, slice_row: int) -> Generator[PartSlice]:
    """Get all pieces (center slices and/or edge wings) at a given slice row.

    Args:
        l1_tracker: Face tracker for Layer 1 face
        slice_row: Distance from L1 face (0 = closest to L1)

    Yields:
        PartSlice objects at the given row based on config flags
        (BIG_LBL_RESOLVE_CENTER_SLICES and BIG_LBL_RESOLVE_EDGES_SLICES)
    """

    # Get the slice sandwiched between L1 face and its opposite
    # (e.g., L1=D → E slice, L1=L → M slice, L1=F → S slice)
    slice_name = cube.layout.get_slice_sandwiched_between_face_and_opposite(l1_tracker.face_name)
    slice_layout = cube.layout.get_slice(slice_name)

    n_slices = cube.n_slices

    # Convert L1-relative distance to slice coordinate system
    cube_slice_index = slice_layout.distance_from_face_to_slice_index(
        l1_tracker.face_name, slice_row, n_slices
    )

    slice_name = cube.layout.get_slice_sandwiched_between_face_and_opposite(l1_tracker.face_name)
    slice_obj: Slice = cube.get_slice(slice_name)

    # Get edge wings and center slices at this slice index
    # We only care about center slices (index [1])
    pieces: tuple[Sequence[EdgeWing], Sequence[CenterSlice]] = slice_obj.get_slices_by_index(cube_slice_index)

    pieces_to_test: list[Iterable[PartSlice[Any]]] = []
    if _lbl_config.BIG_LBL_RESOLVE_CENTER_SLICES:
        pieces_to_test.append(pieces[1])
    if _lbl_config.BIG_LBL_RESOLVE_EDGES_SLICES:
        pieces_to_test.append(pieces[0])

    yield from chain(*pieces_to_test)


def get_center_row_pieces(cube,
                          l1_tracker: FaceTracker, for_face_t: FaceTracker | None, slice_row: int
                          ) -> Generator[CenterSlice]:
    #boaz: take cube from l1_tracker
    """Get all pieces (center slices and/or edge wings) at a given slice row.

    Args:
        l1_tracker: Face tracker for Layer 1 face
        slice_row: Distance from L1 face (0 = closest to L1)

    Yields:
        PartSlice objects at the given row based on config flags
        (BIG_LBL_RESOLVE_CENTER_SLICES and BIG_LBL_RESOLVE_EDGES_SLICES)
        :param cube:
        :param slice_row:
        :param l1_tracker:
        :param for_face_t: if None then for all faces
    """

    # Get the slice sandwiched between L1 face and its opposite
    # (e.g., L1=D → E slice, L1=L → M slice, L1=F → S slice)
    slice_name = cube.layout.get_slice_sandwiched_between_face_and_opposite(l1_tracker.face_name)
    slice_layout = cube.layout.get_slice(slice_name)

    # Convert L1-relative distance to slice coordinate system
    cube_slice_index = slice_layout.distance_from_face_to_slice_index(

        l1_tracker.face_name, slice_row, cube.n_slices  # claude: why we need to pass n_slices !!! it should be in sized layout - slice !!
    )

    slice_name = cube.layout.get_slice_sandwiched_between_face_and_opposite(l1_tracker.face_name)
    slice_obj: Slice = cube.get_slice(slice_name)

    # Get edge wings and center slices at this slice index
    # We only care about center slices (index [1])
    pieces: tuple[Sequence[EdgeWing], Sequence[CenterSlice]] = slice_obj.get_slices_by_index(cube_slice_index)


    if for_face_t is None:
        yield from pieces[1]
    else:

        for_face: Face = for_face_t.face

        # claude: to be optimized, most it is duplication of the method above
        for cs in pieces[1]:
            if cs.face is for_face:
                yield cs

def get_edge_row_pieces(cube,
                          l1_tracker: FaceTracker, slice_row: int
                          ) -> Generator[EdgeWing]:
    # calude: patch path third time code is duplicated


    for cp in _get_row_pieces(cube, l1_tracker,  slice_row):
        if isinstance(cp, EdgeWing):
            yield cp
