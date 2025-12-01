"""
Modern OpenGL Cube Viewer for pyglet2 backend.

This viewer renders a Rubik's cube using modern OpenGL (shaders, VBOs)
instead of legacy immediate mode rendering.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from cube.domain.model.cube_boy import Color, FaceName

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.presentation.gui.backends.pyglet2.ModernGLRenderer import ModernGLRenderer


# Color mapping: cube color enum -> RGB (0-1 normalized)
_COLORS: dict[Color, tuple[float, float, float]] = {
    Color.WHITE: (1.0, 1.0, 1.0),
    Color.YELLOW: (1.0, 0.84, 0.0),
    Color.GREEN: (0.0, 0.61, 0.28),
    Color.BLUE: (0.0, 0.27, 0.68),
    Color.RED: (0.72, 0.07, 0.20),
    Color.ORANGE: (1.0, 0.35, 0.0),
}

# Face positions in 3D space
# Each face has: center point, right direction, up direction
# Cube is centered at origin with faces at distance FACE_OFFSET
FACE_OFFSET = 50.0  # Half the cube size

_FACE_TRANSFORMS: dict[FaceName, tuple[
    tuple[float, float, float],  # center
    tuple[float, float, float],  # right direction
    tuple[float, float, float],  # up direction
]] = {
    FaceName.F: ((0, 0, FACE_OFFSET), (1, 0, 0), (0, 1, 0)),      # Front: +Z
    FaceName.B: ((0, 0, -FACE_OFFSET), (-1, 0, 0), (0, 1, 0)),    # Back: -Z
    FaceName.R: ((FACE_OFFSET, 0, 0), (0, 0, -1), (0, 1, 0)),     # Right: +X
    FaceName.L: ((-FACE_OFFSET, 0, 0), (0, 0, 1), (0, 1, 0)),     # Left: -X
    FaceName.U: ((0, FACE_OFFSET, 0), (1, 0, 0), (0, 0, -1)),     # Up: +Y
    FaceName.D: ((0, -FACE_OFFSET, 0), (1, 0, 0), (0, 0, 1)),     # Down: -Y
}


class ModernGLCubeViewer:
    """Renders a Rubik's cube using modern OpenGL.

    This is a simplified viewer that works with ModernGLRenderer.
    It generates triangle data for all cube facets and renders them
    in batches for efficiency.
    """

    def __init__(self, cube: Cube, renderer: ModernGLRenderer) -> None:
        """Initialize the cube viewer.

        Args:
            cube: The cube model to render
            renderer: The modern GL renderer to use
        """
        self._cube = cube
        self._renderer = renderer

        # Cached triangle data (position + color interleaved)
        # Will be rebuilt when cube state changes
        self._face_triangles: np.ndarray | None = None
        self._line_data: np.ndarray | None = None

        # Track if we need to rebuild
        self._dirty = True

    def update(self) -> None:
        """Mark the viewer as needing update.

        Call this when cube state changes.
        """
        self._dirty = True

    def draw(self) -> None:
        """Draw the cube.

        Rebuilds geometry if cube state changed, then renders.
        """
        if self._dirty:
            self._rebuild_geometry()
            self._dirty = False

        # Draw filled faces
        if self._face_triangles is not None and len(self._face_triangles) > 0:
            self._renderer.draw_colored_triangles(self._face_triangles)

        # Draw grid lines
        if self._line_data is not None and len(self._line_data) > 0:
            self._renderer.draw_colored_lines(self._line_data, line_width=2.0)

    def _rebuild_geometry(self) -> None:
        """Rebuild all geometry from current cube state."""
        cube = self._cube
        size = cube.size

        # Collect all triangle vertices (6 floats per vertex: x,y,z,r,g,b)
        face_verts: list[float] = []
        line_verts: list[float] = []

        # For each face of the cube
        for face_name in FaceName:
            face = cube.face(face_name)
            transform = _FACE_TRANSFORMS[face_name]
            center = np.array(transform[0], dtype=np.float32)
            right = np.array(transform[1], dtype=np.float32)
            up = np.array(transform[2], dtype=np.float32)

            # Face size in world units
            face_size = FACE_OFFSET * 2
            cell_size = face_size / size

            # Generate quads for each cell on this face
            for row in range(size):
                for col in range(size):
                    # Get color for this cell
                    color = self._get_cell_color(face, row, col, size)
                    r, g, b = _COLORS.get(color, (0.5, 0.5, 0.5))

                    # Calculate cell position
                    # Cell (0,0) is bottom-left, (size-1, size-1) is top-right
                    x0 = -FACE_OFFSET + col * cell_size
                    y0 = -FACE_OFFSET + row * cell_size
                    x1 = x0 + cell_size
                    y1 = y0 + cell_size

                    # Apply small gap between cells for grid effect
                    gap = cell_size * 0.02
                    x0 += gap
                    y0 += gap
                    x1 -= gap
                    y1 -= gap

                    # Calculate 4 corners in world space
                    bl = center + x0 * right + y0 * up
                    br = center + x1 * right + y0 * up
                    tr = center + x1 * right + y1 * up
                    tl = center + x0 * right + y1 * up

                    # Two triangles for quad: (bl, br, tr) and (bl, tr, tl)
                    for v in [bl, br, tr, bl, tr, tl]:
                        face_verts.extend([v[0], v[1], v[2], r, g, b])

                    # Border lines (black)
                    line_color = (0.0, 0.0, 0.0)
                    for p1, p2 in [(bl, br), (br, tr), (tr, tl), (tl, bl)]:
                        line_verts.extend([
                            p1[0], p1[1], p1[2], *line_color,
                            p2[0], p2[1], p2[2], *line_color
                        ])

        self._face_triangles = np.array(face_verts, dtype=np.float32)
        self._line_data = np.array(line_verts, dtype=np.float32)

    def _get_cell_color(self, face, row: int, col: int, size: int) -> Color:
        """Get the color of a cell on a face.

        Args:
            face: The Face object
            row: Row index (0 = bottom)
            col: Column index (0 = left)
            size: Cube size

        Returns:
            Color enum value for this cell
        """
        # Map (row, col) to the cube's internal part structure
        # The face has 9 parts for 3x3: corners, edges, center

        # For 3x3 cube:
        # row=2: top-left corner, top edge, top-right corner
        # row=1: left edge, center, right edge
        # row=0: bottom-left corner, bottom edge, bottom-right corner

        # For NxN, we need to map to the correct slice within each part
        if size == 3:
            return self._get_cell_color_3x3(face, row, col)
        else:
            return self._get_cell_color_nxn(face, row, col, size)

    def _get_cell_color_3x3(self, face, row: int, col: int) -> Color:
        """Get cell color for 3x3 cube (simpler case)."""
        # Corners
        if row == 0 and col == 0:
            return face.corner_bottom_left.slice.get_face_edge(face).color
        if row == 0 and col == 2:
            return face.corner_bottom_right.slice.get_face_edge(face).color
        if row == 2 and col == 0:
            return face.corner_top_left.slice.get_face_edge(face).color
        if row == 2 and col == 2:
            return face.corner_top_right.slice.get_face_edge(face).color

        # Edges (single slice for 3x3)
        if row == 0 and col == 1:
            return face.edge_bottom.get_slice_by_ltr_index(face, 0).get_face_edge(face).color
        if row == 2 and col == 1:
            return face.edge_top.get_slice_by_ltr_index(face, 0).get_face_edge(face).color
        if row == 1 and col == 0:
            return face.edge_left.get_slice_by_ltr_index(face, 0).get_face_edge(face).color
        if row == 1 and col == 2:
            return face.edge_right.get_slice_by_ltr_index(face, 0).get_face_edge(face).color

        # Center (single cell for 3x3)
        if row == 1 and col == 1:
            return face.center.get_slice((0, 0)).get_face_edge(face).color

        # Fallback
        return face.original_color

    def _get_cell_color_nxn(self, face, row: int, col: int, size: int) -> Color:
        """Get cell color for NxN cube."""
        # For NxN, the layout is:
        # - Corners at (0,0), (0, size-1), (size-1, 0), (size-1, size-1)
        # - Edges along the borders (excluding corners)
        # - Center fills the middle (size-2) x (size-2) area

        last = size - 1

        # Corners
        if row == 0 and col == 0:
            return face.corner_bottom_left.slice.get_face_edge(face).color
        if row == 0 and col == last:
            return face.corner_bottom_right.slice.get_face_edge(face).color
        if row == last and col == 0:
            return face.corner_top_left.slice.get_face_edge(face).color
        if row == last and col == last:
            return face.corner_top_right.slice.get_face_edge(face).color

        # Edges
        n_slices = size - 2  # Number of edge wing slices

        # Bottom edge
        if row == 0 and 0 < col < last:
            idx = col - 1  # 0-based index within edge
            return face.edge_bottom.get_slice_by_ltr_index(face, idx).get_face_edge(face).color

        # Top edge
        if row == last and 0 < col < last:
            idx = col - 1
            return face.edge_top.get_slice_by_ltr_index(face, idx).get_face_edge(face).color

        # Left edge
        if col == 0 and 0 < row < last:
            idx = row - 1
            return face.edge_left.get_slice_by_ltr_index(face, idx).get_face_edge(face).color

        # Right edge
        if col == last and 0 < row < last:
            idx = row - 1
            return face.edge_right.get_slice_by_ltr_index(face, idx).get_face_edge(face).color

        # Center (the middle area)
        if 0 < row < last and 0 < col < last:
            # Map to center slice grid
            center_row = row - 1
            center_col = col - 1
            return face.center.get_slice((center_row, center_col)).get_face_edge(face).color

        # Fallback
        return face.original_color
