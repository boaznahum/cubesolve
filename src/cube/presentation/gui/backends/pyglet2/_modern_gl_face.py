"""
Modern GL Face - One face of the cube with its cells.

This module manages the geometry for one of the 6 cube faces.
It creates and manages the cells (facelets) on that face.

Cell Layout (looking at face from outside the cube):
    Row 2 (top):    [corner_TL] [edge_T  ] [corner_TR]
    Row 1 (middle): [edge_L   ] [center  ] [edge_R   ]
    Row 0 (bottom): [corner_BL] [edge_B  ] [corner_BR]
                     Col 0       Col 1      Col 2

    For NxN cubes:
    - Corners are always at (0,0), (0,last), (last,0), (last,last)
    - Edges fill the borders between corners
    - Center fills the interior (size-2) x (size-2) area

Coordinate System:
    Each face has a local 2D coordinate system defined by:
    - right: Direction from left edge to right edge
    - up: Direction from bottom edge to top edge
    - normal: Outward direction (computed as cross(right, up))

    Cell positions are computed relative to face center using
    these direction vectors.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy import ndarray

from cube.domain.model.cube_boy import Color, FaceName

from ._modern_gl_cell import ModernGLCell
from ._modern_gl_constants import (
    CELL_GAP_RATIO,
    COLOR_TO_RGB,
    HALF_CUBE_SIZE,
)

if TYPE_CHECKING:
    from cube.domain.model._part_slice import PartSlice
    from cube.domain.model.Face import Face
    from cube.domain.model.PartEdge import PartEdge


class ModernGLFace:
    """One face of the cube, containing size x size cells.

    Cell Layout:
        row 2: [TL] [T ] [TR]   (top row)
        row 1: [L ] [C ] [R ]   (middle row)
        row 0: [BL] [B ] [BR]   (bottom row)
               col0 col1 col2

    Attributes:
        face_name: Which face this is (F, B, R, L, U, D)
        center: Face center position in world space
        right: "Right" direction vector on this face
        up: "Up" direction vector on this face
        normal: Outward normal vector
    """

    __slots__ = [
        'face_name', 'center', 'right', 'up', 'normal',
        '_cells', '_size',
    ]

    def __init__(
        self,
        face_name: FaceName,
        center: ndarray,
        right: ndarray,
        up: ndarray,
        size: int,
    ) -> None:
        """Initialize a face.

        Args:
            face_name: Which face (F, B, R, L, U, D)
            center: Center position in world space
            right: Direction vector for "right" on this face
            up: Direction vector for "up" on this face
            size: Cube size (3 for 3x3, etc.)
        """
        self.face_name = face_name
        self.center = center
        self.right = right
        self.up = up
        self._size = size

        # Compute normal (outward direction)
        self.normal = np.cross(right, up)
        self.normal = self.normal / np.linalg.norm(self.normal)

        # Cells will be created when update() is called
        self._cells: list[ModernGLCell] = []

    def update(self, cube_face: "Face") -> None:
        """Update cells from current cube state.

        Creates new cell objects with current colors from the cube.

        Args:
            cube_face: The cube Face object with current colors
        """
        self._cells.clear()
        size = self._size

        # Face geometry
        face_size = HALF_CUBE_SIZE * 2  # Full face size
        cell_size = face_size / size

        for row in range(size):
            for col in range(size):
                # Get color and part_slice for this cell
                color = self._get_cell_color(cube_face, row, col)
                rgb = COLOR_TO_RGB.get(color, (0.5, 0.5, 0.5))
                part_slice = self._get_cell_part_slice(cube_face, row, col)

                # Get PartEdge for this face (for texture lookup from c_attributes)
                part_edge = part_slice.get_face_edge(cube_face) if part_slice else None

                # Calculate cell corners
                corners = self._calc_cell_corners(row, col, cell_size)

                cell = ModernGLCell(
                    row=row,
                    col=col,
                    part_slice=part_slice,
                    part_edge=part_edge,
                    corners=corners,
                    normal=self.normal,
                    color=rgb,
                )
                self._cells.append(cell)

    def _calc_cell_corners(
        self,
        row: int,
        col: int,
        cell_size: float,
    ) -> list[ndarray]:
        """Calculate the 4 corners of a cell in world space.

        Args:
            row: Row index (0 = bottom)
            col: Column index (0 = left)
            cell_size: Size of one cell

        Returns:
            List of 4 corners: [left_bottom, right_bottom, right_top, left_top]
        """
        # Cell position relative to face center
        # (0,0) is at bottom-left of face, centered at (-HALF_CUBE_SIZE, -HALF_CUBE_SIZE)
        x0 = -HALF_CUBE_SIZE + col * cell_size
        y0 = -HALF_CUBE_SIZE + row * cell_size
        x1 = x0 + cell_size
        y1 = y0 + cell_size

        # Apply small gap for grid effect
        gap = cell_size * CELL_GAP_RATIO
        x0 += gap
        y0 += gap
        x1 -= gap
        y1 -= gap

        # Convert to world space using face orientation
        left_bottom = self.center + x0 * self.right + y0 * self.up
        right_bottom = self.center + x1 * self.right + y0 * self.up
        right_top = self.center + x1 * self.right + y1 * self.up
        left_top = self.center + x0 * self.right + y1 * self.up

        return [left_bottom, right_bottom, right_top, left_top]

    def _get_cell_part_slice(self, face: "Face", row: int, col: int) -> "PartSlice | None":
        """Get the PartSlice at a cell position.

        Cell Layout (like legacy _FaceBoard):
            row 2: [corner_TL] [edge_T   ] [corner_TR]
            row 1: [edge_L   ] [center   ] [edge_R   ]
            row 0: [corner_BL] [edge_B   ] [corner_BR]
                    col 0       col 1       col 2

        For NxN cubes, edges have (size-2) slices and center has (size-2)^2.

        Args:
            face: The cube Face object
            row: Row index (0 = bottom)
            col: Column index (0 = left)

        Returns:
            PartSlice for this cell, or None
        """
        size = face.cube.size
        last = size - 1

        is_bottom_row = (row == 0)
        is_top_row = (row == last)
        is_left_col = (col == 0)
        is_right_col = (col == last)
        is_interior_row = (0 < row < last)
        is_interior_col = (0 < col < last)

        # Corners (at the 4 corners of the face)
        if is_bottom_row and is_left_col:
            return face.corner_bottom_left.slice
        if is_bottom_row and is_right_col:
            return face.corner_bottom_right.slice
        if is_top_row and is_left_col:
            return face.corner_top_left.slice
        if is_top_row and is_right_col:
            return face.corner_top_right.slice

        # Edges (borders between corners)
        # Slice index is offset by 1 because corners take positions 0 and last
        if is_bottom_row and is_interior_col:
            return face.edge_bottom.get_slice_by_ltr_index(face, col - 1)
        if is_top_row and is_interior_col:
            return face.edge_top.get_slice_by_ltr_index(face, col - 1)
        if is_left_col and is_interior_row:
            return face.edge_left.get_slice_by_ltr_index(face, row - 1)
        if is_right_col and is_interior_row:
            return face.edge_right.get_slice_by_ltr_index(face, row - 1)

        # Center (interior cells)
        if is_interior_row and is_interior_col:
            return face.center.get_slice((row - 1, col - 1))

        return None

    def _get_cell_color(self, face: "Face", row: int, col: int) -> Color:
        """Get the color of a cell.

        Delegates to _get_cell_part_slice and gets the color from the edge.

        Args:
            face: The cube Face object
            row: Row index (0 = bottom)
            col: Column index (0 = left)

        Returns:
            Color enum for this cell
        """
        part_slice = self._get_cell_part_slice(face, row, col)
        if part_slice is not None:
            return part_slice.get_face_edge(face).color
        return face.original_color

    @property
    def cells(self) -> list[ModernGLCell]:
        """Get all cells on this face."""
        return self._cells

    def get_center_point(self) -> ndarray:
        """Get the center point of this face in world space."""
        return self.center.copy()

    def get_part_edge_at_cell(self, cube_face: "Face", row: int, col: int) -> "PartEdge | None":
        """Get the PartEdge at a cell position.

        Combines _get_cell_part_slice + get_face_edge for mouse picking.

        Args:
            cube_face: The cube Face object
            row: Row index (0 = bottom)
            col: Column index (0 = left)

        Returns:
            PartEdge at this cell, or None
        """
        part_slice = self._get_cell_part_slice(cube_face, row, col)
        if part_slice is None:
            return None
        return part_slice.get_face_edge(cube_face)
