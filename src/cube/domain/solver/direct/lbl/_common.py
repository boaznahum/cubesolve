"""Common utilities for LBL (Layer-By-Layer) NxN solver.

This module contains shared context managers and helper functions used
by multiple LBL solver components (NxNCenters2, _LBLSlices, etc.).

MARKER SYSTEM DOCUMENTATION
===========================

This module uses THREE distinct marker systems for center piece tracking:

┌─────────────────────────────────────────────────────────────────────────────┐
│ MARKER 1: VISUAL CHECKMARK (Visualization Only)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Purpose:   Display green checkmark on solved pieces in GUI                  │
│ Storage:   MarkerManager.add_marker(edge, "checkmark", ...)                 │
│ Set by:    _mark_piece_with_v_mark_if_solved()                              │
│ Cleared:   Managed by MarkerManager lifecycle (not cleared here)            │
│ Used for:  User feedback only - NOT used by solver algorithm                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ MARKER 2: SOLVED FLAG (Solver Algorithm)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ Purpose:   Track which pieces are solved to avoid destroying them           │
│ Storage:   center_piece.edge.moveable_attributes["NxNCenters2_center_pice_  │
│            solved"] = True                                                  │
│ Set by:    _mark_center_piece_solved() [via _mark_piece_with_v_mark_if_     │
│            solved()]                                                        │
│ Checked:   _is_cent_piece_solved()                                          │
│ Cleared:   Persists until cube reset - NOT cleared during solving           │
│ Used for:  Algorithm uses this to skip already-solved pieces and avoid      │
│            destroying them when moving other pieces                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ MARKER 3: ROW TRACKING (Solver Algorithm)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Purpose:   Track which center slices belong to current row being solved     │
│ Storage:   cs.moveable_attributes[CENTER_SLICE_TRACK_KEY] = column_index    │
│ Key:       CENTER_SLICE_TRACK_KEY = "xxxxxxx"                               │
│ Set by:    _tracke_center_slice(cs, column)                                 │
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
         │    │        ├── _tracke_center_slice()           │
         │    │        │   (set MARKER 3 on all row slices) │
         │    │        │                                    │
         │    │        ├── _mark_piece_with_v_mark_if_      │
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
from contextlib import contextmanager
from typing import TYPE_CHECKING

from cube.domain.geometric.geometry_types import Point
from cube.domain.model import CenterSlice, PartSlice
from cube.domain.solver.direct.lbl._lbl_config import PUT_SOLVED_MARKERS
from cube.domain.tracker.FacesTrackerHolder import FacesTrackerHolder

if TYPE_CHECKING:
    from cube.domain.solver.common.SolverElement import SolverElement
    from cube.domain.tracker.trackers import FaceTracker

# Key used in moveable_attributes to track center slices during solving
__CENTER_SLICE_TRACK_KEY = str(uuid.uuid4())


def position_l1(slv: SolverElement, l1_white_tracker: FaceTracker) -> None:
    """Position L1 (white face) down.

    Args:
        slv: Solver element providing access to cmn.bring_face_down
        l1_white_tracker: The Layer 1 face tracker to position down
    """
    slv.cmn.bring_face_down(l1_white_tracker.face)
    assert l1_white_tracker.face is slv.cube.down


def clear_center_slice(cs: CenterSlice) -> None:
    """Clear tracking marker from a single center slice.

    Args:
        cs: The center slice to clear
    """
    cs.moveable_attributes.pop(__CENTER_SLICE_TRACK_KEY, None)


def clear_all_tracking(slv: SolverElement) -> None:
    """Clear all center slice tracking markers from the cube.

    Args:
        slv: Solver element providing access to cube.centers
    """
    for c in slv.cube.centers:
        for cc in c.all_slices:
            clear_center_slice(cc)


@contextmanager
def setup_l1(slv: SolverElement, l1_white_tracker: FaceTracker) -> Iterator[None]:
    """Setup L1 position and manage tracking lifecycle.

    Positions L1 (white face) down for solving. Tracking is accumulated
    during solving (via _track_row_slices) and cleared only here when
    all slices are done. This protects solved pieces from being destroyed.

    Args:
        slv: Solver element providing access to cube operations
        l1_white_tracker: The Layer 1 face tracker

    Yields:
        None - context manager for setup/cleanup lifecycle
    """
    position_l1(slv, l1_white_tracker)
    try:
        yield
    finally:
        clear_all_tracking(slv)


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
    return [t for t in th.trackers
            if t.face is not l1_tracker.face and t.face is not l1_opposite_face]


def _is_cent_piece_solved(center_piece: CenterSlice) -> bool:
    # this si solver data not visualization
    return "NxNCenters2_center_pice_solved" in center_piece.edge.moveable_attributes


def _mark_piece_solved(piece: PartSlice) -> None:
    # this si solver data not visualization
    for edge in piece.edges:
        edge.moveable_attributes["NxNCenters2_center_pice_solved"] = True


def _mark_slice_with_v_mark_if_solved(piece: PartSlice) -> bool:

    # if piece.by_positon_colors != frozenset(req_color):
    #     return

    if not piece.match_faces:
        return False

    if PUT_SOLVED_MARKERS:
        cube = piece.cube

        mf = cube.sp.marker_factory
        mm = cube.sp.marker_manager

        checkmark = mf.checkmark()  # Green checkmark

        # visualization only
        for edge in piece.edges:
            mm.add_marker(edge, "checkmark", checkmark, moveable=True)

    # this is algorithm !!!
    _mark_piece_solved(piece)

    return True

def _mark_center_piece_with_v_mark_if_solved(center_piece: CenterSlice) -> None:
    _mark_slice_with_v_mark_if_solved(center_piece)

def _track_center_slice(cs: CenterSlice, column: int):

    # self.debug(f"Tracking cent slice {cs.index} column {column}")

    cs.moveable_attributes[__CENTER_SLICE_TRACK_KEY] = column


def _is_center_slice(cs: CenterSlice) -> int | None:

    # the default is boolean False !!!
    x = cs.moveable_attributes[__CENTER_SLICE_TRACK_KEY]

    # print(f"x: {x}")

    if type(x) is int:
        return x
    else:
        return None


def _clear_is_center_slice(cs: CenterSlice) -> None:
    clear_center_slice(cs)


def _iterate_all_tracked_slices_index(target_face: FaceTracker) -> Iterator[Point]:
    for cs in target_face.face.center.all_slices:
        if _is_center_slice(cs) is not None:
            rc = cs.index
            yield Point(*rc)
