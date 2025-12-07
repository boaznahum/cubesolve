"""
Modern GL Cell - One facelet on a cube face.

This module manages the geometry for a single cell (sticker/facelet)
on a cube face. It generates vertex data for VBO-based rendering.

Geometry Layout:
    A cell is a quad with 4 corners:

    left_top -------- right_top
        |                |
        |     center     |
        |                |
    left_bottom ---- right_bottom

    The quad is rendered as 2 triangles:
    - Triangle 1: left_bottom, right_bottom, right_top
    - Triangle 2: left_bottom, right_top, left_top

Vertex Format:
    Non-textured: 9 floats per vertex (x, y, z, nx, ny, nz, r, g, b)
    Textured: 11 floats per vertex (x, y, z, nx, ny, nz, r, g, b, u, v)
    Lines: 6 floats per vertex (x, y, z, r, g, b)
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy import ndarray

from cube.domain.model.cube_boy import Color

if TYPE_CHECKING:
    from cube.domain.model._part_slice import PartSlice

# Border line color (black)
_LINE_COLOR = (0.0, 0.0, 0.0)


class ModernGLCell:
    """One cell (facelet/sticker) on a cube face.

    Manages geometry generation for a single cell including:
    - Quad corners in 3D space
    - Triangle vertices for face rendering
    - Line vertices for border rendering
    - UV coordinates for texture mapping

    Attributes:
        row: Row index on the face (0 = bottom)
        col: Column index on the face (0 = left)
        part_slice: The PartSlice this cell represents (for animation)
    """

    __slots__ = [
        'row', 'col', 'part_slice',
        '_corners',  # [left_bottom, right_bottom, right_top, left_top]
        '_normal',   # Face normal vector
        '_color',    # RGB color tuple
    ]

    def __init__(
        self,
        row: int,
        col: int,
        part_slice: "PartSlice | None",
        corners: list[ndarray],
        normal: ndarray,
        color: tuple[float, float, float],
    ) -> None:
        """Initialize a cell with geometry.

        Args:
            row: Row index (0 = bottom row)
            col: Column index (0 = left column)
            part_slice: The PartSlice for animation tracking (None for centers on some sizes)
            corners: List of 4 corner positions [lb, rb, rt, lt] as numpy arrays
            normal: Face normal vector (outward direction)
            color: RGB color tuple (0.0-1.0 range)
        """
        self.row = row
        self.col = col
        self.part_slice = part_slice
        self._corners = corners
        self._normal = normal
        self._color = color

    def generate_face_vertices(self, dest: list[float]) -> None:
        """Generate triangle vertices for face rendering (non-textured).

        Appends 6 vertices (2 triangles) to dest.
        Each vertex: x, y, z, nx, ny, nz, r, g, b (9 floats)

        Args:
            dest: List to append vertex data to
        """
        lb, rb, rt, lt = self._corners
        nx, ny, nz = float(self._normal[0]), float(self._normal[1]), float(self._normal[2])
        r, g, b = self._color

        # Triangle 1: left_bottom, right_bottom, right_top
        # Triangle 2: left_bottom, right_top, left_top
        for v in [lb, rb, rt, lb, rt, lt]:
            dest.extend([v[0], v[1], v[2], nx, ny, nz, r, g, b])

    def generate_textured_vertices(
        self,
        dest: list[float],
        size: int,
    ) -> None:
        """Generate triangle vertices for textured rendering.

        Appends 6 vertices (2 triangles) to dest.
        Each vertex: x, y, z, nx, ny, nz, r, g, b, u, v (11 floats)

        UV coordinates map this cell to a portion of the face texture:
        - Cell at (row=0, col=0) maps to bottom-left of texture
        - Cell at (row=size-1, col=size-1) maps to top-right

        Args:
            dest: List to append vertex data to
            size: Cube size (for UV calculation)
        """
        lb, rb, rt, lt = self._corners
        nx, ny, nz = float(self._normal[0]), float(self._normal[1]), float(self._normal[2])
        r, g, b = self._color

        # UV coordinates for this cell's portion of the texture
        u0 = self.col / size
        v0 = self.row / size
        u1 = (self.col + 1) / size
        v1 = (self.row + 1) / size

        # Triangle 1: lb(u0,v0), rb(u1,v0), rt(u1,v1)
        dest.extend([lb[0], lb[1], lb[2], nx, ny, nz, r, g, b, u0, v0])
        dest.extend([rb[0], rb[1], rb[2], nx, ny, nz, r, g, b, u1, v0])
        dest.extend([rt[0], rt[1], rt[2], nx, ny, nz, r, g, b, u1, v1])

        # Triangle 2: lb(u0,v0), rt(u1,v1), lt(u0,v1)
        dest.extend([lb[0], lb[1], lb[2], nx, ny, nz, r, g, b, u0, v0])
        dest.extend([rt[0], rt[1], rt[2], nx, ny, nz, r, g, b, u1, v1])
        dest.extend([lt[0], lt[1], lt[2], nx, ny, nz, r, g, b, u0, v1])

    def generate_line_vertices(self, dest: list[float]) -> None:
        """Generate line vertices for cell border.

        Appends 8 vertices (4 line segments) to dest.
        Each vertex: x, y, z, r, g, b (6 floats)

        Args:
            dest: List to append vertex data to
        """
        lb, rb, rt, lt = self._corners
        lr, lg, lb_color = _LINE_COLOR

        # 4 edges: bottom, right, top, left
        for p1, p2 in [(lb, rb), (rb, rt), (rt, lt), (lt, lb)]:
            dest.extend([p1[0], p1[1], p1[2], lr, lg, lb_color])
            dest.extend([p2[0], p2[1], p2[2], lr, lg, lb_color])

    @property
    def color_enum(self) -> Color:
        """Get the Color enum for this cell (for texture grouping)."""
        # Reverse lookup from RGB to Color enum
        # This is used for grouping cells by color for texture rendering
        from ._modern_gl_constants import RGB_TO_COLOR
        return RGB_TO_COLOR.get(self._color, Color.WHITE)
