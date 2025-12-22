"""Static geometry utilities for NxN center solving.

This module provides static utility functions for center piece geometry:
- Block/point coordinate transformations
- Range intersection checks
- Block size calculations
- Face color counting

For face tracker management, use FaceTrackerHolder instead.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Tuple, TypeAlias

from cube.domain.model import Color
from cube.domain.model.Face import Face
from cube.domain.solver.common.FaceTracker import FaceTracker


# Type aliases for clarity
Point: TypeAlias = Tuple[int, int]
Block: TypeAlias = Tuple[Point, Point]


class NxNCentersHelper:
    """Static geometry utilities for NxN center solving.

    All methods are static - no instance needed.

    For face tracker management, use FaceTrackerHolder instead:
        with FaceTrackerHolder(solver) as holder:
            face_colors = holder.get_face_colors()
            # ... solve ...
    """

    # =========================================================================
    # STATIC GEOMETRY UTILITIES
    # =========================================================================
    # These are pure utility functions for center piece geometry calculations.
    # They don't depend on any solver state - only on coordinates and colors.

    @staticmethod
    def _is_face_solved(face: Face, color: Color) -> bool:
        """Check if a face's center is solved with the specified color.

        A face is "solved" when:
        1. Its center is reduced to a 3x3 virtual center (all pieces same color)
        2. That color matches the expected color

        Args:
            face: The face to check.
            color: The expected color for this face.

        Returns:
            True if face center is 3x3 and matches color.
        """
        is_3x3 = face.center.is3x3
        slice_color = face.center.get_center_slice((0, 0)).color
        return is_3x3 and slice_color == color

    @staticmethod
    def _count_missing(face: Face, color: Color) -> int:
        """Count how many center pieces are NOT the expected color.

        Useful for measuring how much work remains on a face.

        Args:
            face: The face to check.
            color: The expected color.

        Returns:
            Number of center pieces that don't match color.
        """
        n = 0
        for s in face.center.all_slices:
            if s.color != color:
                n += 1
        return n

    @staticmethod
    def _has_color_on_face(face: Face, color: Color) -> bool:
        """Check if a face has at least one piece of the specified color.

        Args:
            face: The face to check.
            color: The color to look for.

        Returns:
            True if any center piece on this face has the color.
        """
        for s in face.center.all_slices:
            if s.color == color:
                return True
        return False

    @staticmethod
    def _block_size(rc1: Point, rc2: Point) -> int:
        """Calculate the number of pieces in a rectangular block.

        Args:
            rc1: One corner of block (row, column).
            rc2: Other corner of block (row, column).

        Returns:
            Width × Height of the block.
        """
        return (abs(rc2[0] - rc1[0]) + 1) * (abs(rc2[1] - rc1[1]) + 1)

    @staticmethod
    def _block_dimensions(rc1: Point, rc2: Point) -> Tuple[int, int]:
        """Get the dimensions (rows, columns) of a block.

        Args:
            rc1: One corner of block.
            rc2: Other corner of block.

        Returns:
            Tuple of (height, width).
        """
        return (abs(rc2[0] - rc1[0]) + 1), (abs(rc2[1] - rc1[1]) + 1)

    @staticmethod
    def _ranges_intersect(range_1: Tuple[int, int], range_2: Tuple[int, int]) -> bool:
        """Check if two 1D ranges overlap.

        Used to determine if two blocks would interfere during a commutator.

        Visual:
                     x3--------------x4
               x1--------x2

        Ranges DON'T intersect if: x3 > x2 OR x4 < x1

        Args:
            range_1: First range (x1, x2).
            range_2: Second range (x3, x4).

        Returns:
            True if ranges overlap.
        """
        x1, x2 = range_1
        x3, x4 = range_2

        # After rotation points may swap coordinates
        if x1 > x2:
            x1, x2 = x2, x1
        if x3 > x4:
            x3, x4 = x4, x3

        if x3 > x2:
            return False
        if x4 < x1:
            return False
        return True

    @staticmethod
    def _iter_2d_range(rc1: Point, rc2: Point) -> Iterator[Point]:
        """Iterate over all points in a 2D rectangular block.

        Points are yielded row by row, columns advancing faster.

        Args:
            rc1: One corner of block.
            rc2: Other corner of block.

        Yields:
            Each (row, column) point in the block.
        """
        r1, c1 = rc1
        r2, c2 = rc2

        if r1 > r2:
            r1, r2 = r2, r1
        if c1 > c2:
            c1, c2 = c2, c1

        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                yield r, c

    @staticmethod
    def _count_colors_on_block(color: Color, source_face: Face,
                               rc1: Point, rc2: Point,
                               ignore_if_back: bool = False) -> int:
        """Count pieces matching a color within a block on a face.

        Args:
            color: The color to count.
            source_face: The face containing the block.
            rc1: One corner of block (in front-face coordinates).
            rc2: Other corner of block (in front-face coordinates).
            ignore_if_back: If False and face is back, coordinates are inverted.

        Returns:
            Number of pieces in the block matching color.
        """
        count, _ = NxNCentersHelper._count_colors_and_trackers_on_block(
            color, source_face, rc1, rc2, ignore_if_back
        )
        return count

    @staticmethod
    def _count_colors_and_trackers_on_block(
        color: Color, source_face: Face,
        rc1: Point, rc2: Point,
        ignore_if_back: bool = False
    ) -> Tuple[int, int]:
        """Count pieces matching color AND tracker slices in a block.

        The back face has inverted coordinates relative to front face.
        This function handles the coordinate transformation unless
        ignore_if_back=True.

        Args:
            color: The color to count.
            source_face: The face containing the block.
            rc1: One corner (front-face coordinates).
            rc2: Other corner (front-face coordinates).
            ignore_if_back: If True, don't transform back-face coordinates.

        Returns:
            Tuple of (color_count, tracker_count).
        """
        cube = source_face.cube
        fix_back_coords = not ignore_if_back and source_face is cube.back

        if fix_back_coords:
            # Back face is mirrored in both directions relative to front
            inv = cube.inv
            rc1 = (inv(rc1[0]), inv(rc1[1]))
            rc2 = (inv(rc2[0]), inv(rc2[1]))

        r1, c1 = rc1
        r2, c2 = rc2

        if r1 > r2:
            r1, r2 = r2, r1
        if c1 > c2:
            c1, c2 = c2, c1

        _count = 0
        _trackers = 0
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                center_slice = source_face.center.get_center_slice((r, c))
                if color == center_slice.color:
                    _count += 1
                if not _trackers and FaceTracker.is_track_slice(center_slice):
                    _trackers += 1

        return _count, _trackers
