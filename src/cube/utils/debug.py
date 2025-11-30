"""
Debug utilities for cube state inspection.

This module provides functions to dump detailed cube state information
for debugging purposes, especially for tracking down cache-related bugs.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cube.model.cube import Cube


def dump_cube_state(cube: "Cube", label: str = "Cube State") -> None:
    """
    Dump detailed cube state information to stdout.

    This includes:
    - Basic cube info (size, solved status)
    - All parts with their colors_id, position_id, and cache state
    - The full state dictionary from cqr.get_sate()

    Args:
        cube: The cube to dump state for
        label: A label to identify this dump in the output
    """
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

    # Dump all parts with cache state
    print("-" * 70)
    print("Parts State (fixed_id -> colors, colors_id cache, position_id cache)")
    print("-" * 70)

    all_parts = cube.get_all_parts()
    for part in sorted(all_parts, key=lambda p: str(p.fixed_id)):
        # Access cache state directly (these are the lazy-initialized caches)
        colors_cache = getattr(part, '_colors_id_by_colors', None)
        pos_cache = getattr(part, '_colors_id_by_pos', None)

        # Get actual values (this will initialize cache if not set)
        colors_id = part.colors_id
        position_id = part.position_id

        print(f"  {part.fixed_id}")
        print(f"    colors: {part.colors}")
        print(f"    colors_id: {colors_id} (cache was: {colors_cache})")
        print(f"    position_id: {position_id} (cache was: {pos_cache})")

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


def dump_cube_state_compact(cube: "Cube", label: str = "Cube State") -> None:
    """
    Dump compact cube state information to stdout.

    A shorter version of dump_cube_state for quick inspection.

    Args:
        cube: The cube to dump state for
        label: A label to identify this dump in the output
    """
    print()
    print(f"=== DEBUG: {label} ===")
    print(f"Size: {cube.size}, Solved: {cube.solved}, ModCounter: {cube._modify_counter}")

    state = cube.cqr.get_sate()
    print(f"State entries: {len(state)}")

    # Just show cache status for parts
    all_parts = cube.get_all_parts()
    cached_colors = sum(1 for p in all_parts if getattr(p, '_colors_id_by_colors', None) is not None)
    cached_pos = sum(1 for p in all_parts if getattr(p, '_colors_id_by_pos', None) is not None)
    print(f"Parts: {len(all_parts)}, colors_id cached: {cached_colors}, position_id cached: {cached_pos}")
    print(f"=== END: {label} ===")
    print()