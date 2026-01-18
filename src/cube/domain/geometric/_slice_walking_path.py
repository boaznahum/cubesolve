"""
Slice Walking Path - Coordinate transformation for slices on faces.

This module provides functions to convert between slice coordinates (slice_index, slot)
and face coordinates (row, col) for each of the 8 cases.

Human-readable inputs:
- entry_edge: The edge where the slice enters the face
- rotating_edge: The edge shared with the rotating face (where slice[0] is located)

The module internally derives the 3 characteristics:
- H/V: is_horizontal (entry edge is top/bottom vs left/right)
- C/F: is_index_inverted (slice[0] near origin vs far from origin)
- A/I: is_slot_inverted (slot increases in +X/+Y direction vs opposite)

Documentation:
- _walking_info_case1_entry_bottom_rotating_left.md
- _walking_info_case2_entry_top_rotating_left.md
- _walking_info_case3_entry_bottom_rotating_right.md
- _walking_info_case4_entry_top_rotating_right.md
- _walking_info_case5_entry_left_rotating_bottom.md
- _walking_info_case6_entry_right_rotating_bottom.md
- _walking_info_case7_entry_left_rotating_top.md
- _walking_info_case8_entry_right_rotating_top.md
- _walking_info_summary.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from cube.domain.geometric.types import (
    CenterToSlice,
    Point,
    SliceToCenter,
    SliceToEntryEdge,
)
from cube.domain.model._elements import EdgePosition

if TYPE_CHECKING:
    from cube.domain.model.Face import Face

# Aliases for backward compatibility with existing code
SliceToCenterFn = SliceToCenter
SliceToEntryEdgeFn = SliceToEntryEdge
CenterToSliceFn = CenterToSlice


@dataclass(frozen=True)
class SliceWalkingInfo:
    """
    Coordinate transformation functions for a slice on a face.

    This is the output of create_walking_info() - it provides
    functions to convert between slice coordinates and face coordinates.

    All functions accept n_slices as their FIRST parameter, allowing
    the same SliceWalkingInfo to work with any cube size.
    """

    # Convert slice coord to face coord: (n_slices, slice_index, slot) -> (row, col)
    slice_to_center: SliceToCenterFn

    # Given slice_index, compute piece index on entry edge: (n_slices, slice_index) -> int
    slice_to_entry_edge: SliceToEntryEdgeFn

    # Convert face coord to slice coord: (n_slices, row, col) -> (slice_index, slot)
    center_to_slice: CenterToSliceFn

    # The 3 characteristics that define the formula
    is_horizontal: bool
    is_index_inverted: bool
    is_slot_inverted: bool


def create_walking_info(
    face: Face,
    entry_edge_position: EdgePosition,
    rotating_edge_position: EdgePosition,
) -> SliceWalkingInfo:
    """
    Create coordinate transformation functions for a slice on a face.

    All returned functions accept n_slices as their FIRST parameter, allowing
    the same SliceWalkingInfo to work with any cube size.

    Args:
        face: The face that the slice is on
        entry_edge_position: The edge where the slice enters the face (LEFT, RIGHT, TOP, BOTTOM)
        rotating_edge_position: The edge shared with the rotating face - where slice[0] is located

    Returns:
        SliceWalkingInfo with the three transformation functions.

    Example:
        # Slice enters from BOTTOM, rotating face is on the LEFT
        info = create_walking_info(face=my_face,
                                   entry_edge_position=EdgePosition.BOTTOM,
                                   rotating_edge_position=EdgePosition.LEFT)

        # Convert slice coord to face coord (for a 5x5 cube with n_slices=3)
        face_coord = info.slice_to_center(n_slices=3, slice_index=0, slot=1)
        # Returns FaceCoord(row=1, col=0)

        # Convert face coord back to slice coord
        slice_coord = info.center_to_slice(n_slices=3, row=1, col=0)
        # Returns SliceCoord(slice_index=0, slot=1)

    The 8 cases derived from entry_edge and rotating_edge:

    | Case | entry_edge | rotating_edge | Slice Orientation | Formula (row, col)           |
    |------|------------|---------------|-------------------|------------------------------|
    | 1    | BOTTOM     | LEFT          | VERTICAL          | (slot, sindex)               |
    | 2    | TOP        | LEFT          | VERTICAL          | (inv(slot), sindex)          |
    | 3    | BOTTOM     | RIGHT         | VERTICAL          | (slot, inv(sindex))          |
    | 4    | TOP        | RIGHT         | VERTICAL          | (inv(slot), inv(sindex))     |
    | 5    | LEFT       | BOTTOM        | HORIZONTAL        | (sindex, slot)               |
    | 6    | RIGHT      | BOTTOM        | HORIZONTAL        | (sindex, inv(slot))          |
    | 7    | LEFT       | TOP           | HORIZONTAL        | (inv(sindex), slot)          |
    | 8    | RIGHT      | TOP           | HORIZONTAL        | (inv(sindex), inv(slot))     |

    Where inv(x) = n_slices - 1 - x
    See _walking_info_case{N}_entry_{entry}_rotating_{rotating}.md for diagrams
    """

    # Derive the 3 characteristics from human inputs
    #
    # H/V: Horizontal if entry is TOP or BOTTOM, Vertical if entry is LEFT or RIGHT
    is_horizontal = entry_edge_position in (EdgePosition.TOP, EdgePosition.BOTTOM)

    # C/F: Close if rotating edge is at origin side, Far if opposite
    #   For horizontal: LEFT is close (col=0), RIGHT is far (col=n-1)
    #   For vertical: BOTTOM is close (row=0), TOP is far (row=n-1)
    if is_horizontal:
        is_index_inverted = rotating_edge_position == EdgePosition.RIGHT  # Far
    else:
        is_index_inverted = rotating_edge_position == EdgePosition.TOP  # Far

    # A/I: Aligned if slot increases in +row or +col direction
    #   For horizontal: BOTTOM entry = slot goes up (+row) = Aligned
    #                   TOP entry = slot goes down (-row) = Inverted
    #   For vertical: LEFT entry = slot goes right (+col) = Aligned
    #                 RIGHT entry = slot goes left (-col) = Inverted
    if is_horizontal:
        is_slot_inverted = entry_edge_position == EdgePosition.TOP
    else:
        is_slot_inverted = entry_edge_position == EdgePosition.RIGHT

    # Select the appropriate formula based on the 3 characteristics
    # All functions take n_slices as first parameter and return Point (tuple[int, int])
    if is_horizontal:
        # Entry BOTTOM/TOP → VERTICAL slices: row = slot (or inv), col = sindex (or inv)
        if not is_index_inverted and not is_slot_inverted:
            # Case 1: Entry BOTTOM, Rotating LEFT
            # See: _walking_info_case1_entry_bottom_rotating_left.md
            def slice_to_center(n_slices: int, slice_index: int, slot: int) -> Point:
                return (slot, slice_index)  # (row, col)

            def center_to_slice(n_slices: int, row: int, col: int) -> Point:
                return (col, row)  # (slice_index, slot)

        elif not is_index_inverted and is_slot_inverted:
            # Case 2: Entry TOP, Rotating LEFT
            # See: _walking_info_case2_entry_top_rotating_left.md
            def slice_to_center(n_slices: int, slice_index: int, slot: int) -> Point:
                return (n_slices - 1 - slot, slice_index)  # (row, col)

            def center_to_slice(n_slices: int, row: int, col: int) -> Point:
                return (col, n_slices - 1 - row)  # (slice_index, slot)

        elif is_index_inverted and not is_slot_inverted:
            # Case 3: Entry BOTTOM, Rotating RIGHT
            # See: _walking_info_case3_entry_bottom_rotating_right.md
            def slice_to_center(n_slices: int, slice_index: int, slot: int) -> Point:
                return (slot, n_slices - 1 - slice_index)  # (row, col)

            def center_to_slice(n_slices: int, row: int, col: int) -> Point:
                return (n_slices - 1 - col, row)  # (slice_index, slot)

        else:
            # Case 4: Entry TOP, Rotating RIGHT
            # See: _walking_info_case4_entry_top_rotating_right.md
            def slice_to_center(n_slices: int, slice_index: int, slot: int) -> Point:
                return (n_slices - 1 - slot, n_slices - 1 - slice_index)  # (row, col)

            def center_to_slice(n_slices: int, row: int, col: int) -> Point:
                return (n_slices - 1 - col, n_slices - 1 - row)  # (slice_index, slot)
    else:
        # Entry LEFT/RIGHT → HORIZONTAL slices: row = sindex (or inv), col = slot (or inv)
        if not is_index_inverted and not is_slot_inverted:
            # Case 5: Entry LEFT, Rotating BOTTOM
            # See: _walking_info_case5_entry_left_rotating_bottom.md
            def slice_to_center(n_slices: int, slice_index: int, slot: int) -> Point:
                return (slice_index, slot)  # (row, col)

            def center_to_slice(n_slices: int, row: int, col: int) -> Point:
                return (row, col)  # (slice_index, slot)

        elif not is_index_inverted and is_slot_inverted:
            # Case 6: Entry RIGHT, Rotating BOTTOM
            # See: _walking_info_case6_entry_right_rotating_bottom.md
            def slice_to_center(n_slices: int, slice_index: int, slot: int) -> Point:
                return (slice_index, n_slices - 1 - slot)  # (row, col)

            def center_to_slice(n_slices: int, row: int, col: int) -> Point:
                return (row, n_slices - 1 - col)  # (slice_index, slot)

        elif is_index_inverted and not is_slot_inverted:
            # Case 7: Entry LEFT, Rotating TOP
            # See: _walking_info_case7_entry_left_rotating_top.md
            def slice_to_center(n_slices: int, slice_index: int, slot: int) -> Point:
                return (n_slices - 1 - slice_index, slot)  # (row, col)

            def center_to_slice(n_slices: int, row: int, col: int) -> Point:
                return (n_slices - 1 - row, col)  # (slice_index, slot)

        else:
            # Case 8: Entry RIGHT, Rotating TOP
            # See: _walking_info_case8_entry_right_rotating_top.md
            def slice_to_center(n_slices: int, slice_index: int, slot: int) -> Point:
                return (n_slices - 1 - slice_index, n_slices - 1 - slot)  # (row, col)

            def center_to_slice(n_slices: int, row: int, col: int) -> Point:
                return (n_slices - 1 - row, n_slices - 1 - col)  # (slice_index, slot)

    # slice_to_entry_edge: Given slice_index, compute edge's internal slice index
    #
    # Flow:
    # 1. Convert slice_index to face's center coordinate (row or col)
    # 2. That coordinate is the face's ltr (left-to-right) for the entry edge
    # 3. Translate face's ltr to edge's internal slice index using edge's method
    #
    # For VERTICAL slices (entry BOTTOM/TOP): slice_index → col, col is ltr
    # For HORIZONTAL slices (entry LEFT/RIGHT): slice_index → row, row is ltr

    entry_edge = face.get_edge(entry_edge_position)

    def slice_to_entry_edge(n_slices: int, slice_index: int) -> int:
        # Step 1: Convert slice_index to face's ltr coordinate
        if is_index_inverted:
            face_ltr = n_slices - 1 - slice_index
        else:
            face_ltr = slice_index

        # Step 2: Translate face's ltr to edge's internal slice index
        return entry_edge.get_slice_index_from_ltr_index_arbitrary_n_slices(n_slices, face, face_ltr)

    return SliceWalkingInfo(
        slice_to_center=slice_to_center,
        slice_to_entry_edge=slice_to_entry_edge,
        center_to_slice=center_to_slice,
        is_horizontal=is_horizontal,
        is_index_inverted=is_index_inverted,
        is_slot_inverted=is_slot_inverted,
    )
