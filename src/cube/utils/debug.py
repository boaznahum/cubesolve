"""
Debug utilities for cube state inspection.

This module provides functions to dump detailed cube state information
for debugging purposes, especially for tracking down cache-related bugs.

See docs/design/domain_model.md for the cube structure:
- cube.get_all_parts() returns Collection[PartSlice]
- PartSlice has: colors_id, _colors_id_by_colors
- Part has: colors_id, position_id, _colors_id_by_colors, _colors_id_by_pos
- PartSlice._parent gives access to the parent Part
"""

from __future__ import annotations

from collections.abc import Collection
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model._part_slice import PartSlice
    from cube.domain.model._elements import PartColorsID


def dump_cube_state(cube: Cube, label: str = "Cube State") -> None:
    """
    Dump detailed cube state information to stdout.

    This includes:
    - Basic cube info (size, solved status)
    - All PartSlices with their colors_id and cache state
    - Parent Part info (position_id) when available
    - The full state dictionary from cqr.get_sate()

    Args:
        cube: The cube to dump state for
        label: A label to identify this dump in the output
    """
    # TODO: is it dead code?
    return

    print()
    print("=" * 70)
    print(f"DEBUG: {label}")
    print("=" * 70)

    # Basic info
    print(f"Cube size: {cube.size}")
    print(f"Solved: {cube.solved}")
    print(f"Modify counter: {cube._modify_counter}")
    print()

    # Get full state
    state = cube.cqr.get_sate()
    print(f"State entries: {len(state)}")
    print()

    # Dump all PartSlices with cache state
    print("-" * 70)
    print("PartSlices State (fixed_id -> colors, colors_id cache)")
    print("-" * 70)

    all_slices: Collection[PartSlice] = cube.get_all_parts()
    for slice_ in sorted(all_slices, key=lambda p: str(p.fixed_id)):
        # PartSlice has _colors_id_by_colors (initialized in __init__)
        slice_colors_cache: PartColorsID | None = slice_._colors_id_by_colors

        # Get actual value (this will initialize cache if not set)
        slice_colors_id: PartColorsID = slice_.colors_id

        print(f"  {slice_.fixed_id}")
        print(f"    colors: {slice_.colors}")
        print(f"    colors_id: {slice_colors_id} (cache was: {slice_colors_cache})")

        # Access parent Part for position_id (only Part has this)
        parent = slice_._parent
        if parent is not None:
            part_colors_cache: PartColorsID | None = parent._colors_id_by_colors
            part_pos_cache: PartColorsID | None = parent._colors_id_by_pos
            part_colors_id: PartColorsID = parent.colors_id
            part_position_id: PartColorsID = parent.position_id
            print(f"    Part colors_id: {part_colors_id} (cache was: {part_colors_cache})")
            print(f"    Part position_id: {part_position_id} (cache was: {part_pos_cache})")

    print()
    print("-" * 70)
    print("Full State Dictionary")
    print("-" * 70)
    for fixed_id, colors in sorted(state.items(), key=lambda x: str(x[0])):
        print(f"  {fixed_id} -> {colors}")

    print()
    print("=" * 70)
    print(f"END DEBUG: {label}")
    print("=" * 70)
    print()


def dump_cube_state_compact(cube: Cube, label: str = "Cube State") -> None:
    """
    Dump compact cube state information to stdout.

    A shorter version of dump_cube_state for quick inspection.

    Args:
        cube: The cube to dump state for
        label: A label to identify this dump in the output
    """
    # TODO: is it dead code?
    print()
    print(f"=== DEBUG: {label} ===")
    print(f"Size: {cube.size}, Solved: {cube.solved}, ModCounter: {cube._modify_counter}")

    state = cube.cqr.get_sate()
    print(f"State entries: {len(state)}")

    # Show cache status for PartSlices (have _colors_id_by_colors)
    all_slices: Collection[PartSlice] = cube.get_all_parts()
    slices_cached: int = sum(1 for s in all_slices if s._colors_id_by_colors is not None)
    print(f"PartSlices: {len(all_slices)}, colors_id cached: {slices_cached}")

    # Show cache status for unique Parts (have both _colors_id_by_colors and _colors_id_by_pos)
    unique_parts: set[int] = set()  # Track by id() to avoid duplicates
    parts_colors_cached: int = 0
    parts_pos_cached: int = 0
    for s in all_slices:
        if s._parent is not None and id(s._parent) not in unique_parts:
            unique_parts.add(id(s._parent))
            if s._parent._colors_id_by_colors is not None:
                parts_colors_cached += 1
            if s._parent._colors_id_by_pos is not None:
                parts_pos_cached += 1
    print(f"Parts: {len(unique_parts)}, colors_id cached: {parts_colors_cached}, position_id cached: {parts_pos_cached}")

    print(f"=== END: {label} ===")
    print()