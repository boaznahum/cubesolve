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

    # === Ray-Plane Intersection for Mouse Picking ===

    def find_facet_by_ray(
        self,
        ray_origin: np.ndarray,
        ray_direction: np.ndarray,
    ) -> tuple[FaceName, int, int, np.ndarray, np.ndarray] | None:
        """Find which cube facet (cell) is hit by a ray.

        Uses ray-plane intersection for each of the 6 cube faces.
        Returns the closest hit.

        Args:
            ray_origin: Ray start point in world space (3D)
            ray_direction: Ray direction in world space (3D, normalized)

        Returns:
            Tuple of (face_name, row, col, right_dir, up_dir) or None if no hit.
            - face_name: Which face was hit (F, B, R, L, U, D)
            - row, col: Cell indices on that face
            - right_dir, up_dir: Face orientation vectors for drag direction
        """
        size = self._cube.size
        face_size = FACE_OFFSET * 2
        cell_size = face_size / size

        best_hit: tuple[FaceName, int, int, np.ndarray, np.ndarray] | None = None
        best_t = float('inf')

        for face_name, (center, right, up) in _FACE_TRANSFORMS.items():
            center_np = np.array(center, dtype=np.float32)
            right_np = np.array(right, dtype=np.float32)
            up_np = np.array(up, dtype=np.float32)

            # Face normal is cross(right, up)
            normal = np.cross(right_np, up_np)
            normal = normal / np.linalg.norm(normal)

            # Ray-plane intersection: t = (center - origin) . normal / (direction . normal)
            denom = np.dot(ray_direction, normal)
            if abs(denom) < 1e-6:
                continue  # Ray parallel to plane

            t = np.dot(center_np - ray_origin, normal) / denom
            if t < 0:
                continue  # Intersection behind ray origin

            if t >= best_t:
                continue  # Further than current best

            # Calculate intersection point
            hit_point = ray_origin + t * ray_direction

            # Convert to face-local coordinates (relative to center)
            local = hit_point - center_np
            local_x = np.dot(local, right_np)  # Position along right direction
            local_y = np.dot(local, up_np)     # Position along up direction

            # Check if within face bounds
            if abs(local_x) > FACE_OFFSET or abs(local_y) > FACE_OFFSET:
                continue  # Outside face

            # Convert to cell indices
            # local_x ranges from -FACE_OFFSET to +FACE_OFFSET
            # Map to 0..size
            col = int((local_x + FACE_OFFSET) / cell_size)
            row = int((local_y + FACE_OFFSET) / cell_size)

            # Clamp to valid range
            col = max(0, min(size - 1, col))
            row = max(0, min(size - 1, row))

            best_t = t
            best_hit = (face_name, row, col, right_np, up_np)

        return best_hit

    def _setup_view_matrix(self, vs) -> None:
        """Set up the modelview matrix from view state.

        This ensures the modelview matrix is current for picking operations
        that happen outside of on_draw().

        Args:
            vs: Application view state containing rotation angles and offset
        """
        import math

        self._renderer.load_identity()

        # Apply offset translation (camera distance)
        offset = vs.offset
        self._renderer.translate(float(offset[0]), float(offset[1]), float(offset[2]))

        # Apply initial rotation (base orientation)
        self._renderer.rotate(math.degrees(vs.alpha_x_0), 1, 0, 0)
        self._renderer.rotate(math.degrees(vs.alpha_y_0), 0, 1, 0)
        self._renderer.rotate(math.degrees(vs.alpha_z_0), 0, 0, 1)

        # Apply user-controlled rotation (from mouse drag)
        self._renderer.rotate(math.degrees(vs.alpha_x), 1, 0, 0)
        self._renderer.rotate(math.degrees(vs.alpha_y), 0, 1, 0)
        self._renderer.rotate(math.degrees(vs.alpha_z), 0, 0, 1)

    def screen_to_ray(
        self,
        screen_x: float,
        screen_y: float,
        window_width: int,
        window_height: int,
        vs=None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Convert screen coordinates to a ray in world space.

        Args:
            screen_x: X coordinate in pixels (0 = left)
            screen_y: Y coordinate in pixels (0 = bottom in OpenGL)
            window_width: Window width in pixels
            window_height: Window height in pixels
            vs: Optional view state - if provided, recalculates the view matrix

        Returns:
            Tuple of (ray_origin, ray_direction) both as numpy arrays
        """
        # Recalculate view matrix if view state provided
        if vs is not None:
            self._setup_view_matrix(vs)

        # Get inverse MVP matrix from renderer
        inv_mvp = self._renderer.get_inverse_mvp()

        # Convert screen to NDC (-1 to 1)
        ndc_x = (2.0 * screen_x / window_width) - 1.0
        ndc_y = (2.0 * screen_y / window_height) - 1.0

        # Create two points: near plane (z=-1) and far plane (z=1)
        near_ndc = np.array([ndc_x, ndc_y, -1.0, 1.0], dtype=np.float32)
        far_ndc = np.array([ndc_x, ndc_y, 1.0, 1.0], dtype=np.float32)

        # Unproject to world space
        near_world = np.matmul(inv_mvp, near_ndc)
        far_world = np.matmul(inv_mvp, far_ndc)

        # Perspective divide
        near_world = near_world[:3] / near_world[3]
        far_world = far_world[:3] / far_world[3]

        # Ray from near to far
        ray_origin = near_world
        ray_direction = far_world - near_world
        ray_direction = ray_direction / np.linalg.norm(ray_direction)

        print(f"[RAY] ndc=({ndc_x:.2f}, {ndc_y:.2f}), origin={ray_origin}, dir={ray_direction}", flush=True)

        return ray_origin, ray_direction

    def find_facet_at_screen(
        self,
        screen_x: float,
        screen_y: float,
        window_width: int,
        window_height: int,
        vs=None,
    ) -> tuple[FaceName, int, int, np.ndarray, np.ndarray] | None:
        """Find which cube facet is under the given screen position.

        Combines screen_to_ray() and find_facet_by_ray() for easy mouse picking.

        Args:
            screen_x: X coordinate in pixels
            screen_y: Y coordinate in pixels
            window_width: Window width
            window_height: Window height
            vs: Optional view state for matrix recalculation

        Returns:
            Tuple of (face_name, row, col, right_dir, up_dir) or None
        """
        ray_origin, ray_direction = self.screen_to_ray(
            screen_x, screen_y, window_width, window_height, vs
        )
        return self.find_facet_by_ray(ray_origin, ray_direction)

    def get_part_edge_at_screen(
        self,
        screen_x: float,
        screen_y: float,
        window_width: int,
        window_height: int,
        vs=None,
    ) -> tuple | None:
        """Find the PartEdge at screen position.

        This is the main interface for mouse picking - returns the same format
        as the legacy GCubeViewer.find_facet() method.

        Args:
            screen_x: X coordinate in pixels
            screen_y: Y coordinate in pixels
            window_width: Window width
            window_height: Window height
            vs: Optional view state for matrix recalculation

        Returns:
            Tuple of (PartEdge, right_dir, up_dir) or None
            - PartEdge: The cube part edge that was clicked
            - right_dir: Face's "right" direction vector (for drag detection)
            - up_dir: Face's "up" direction vector (for drag detection)
        """
        from cube.domain.model.PartEdge import PartEdge

        result = self.find_facet_at_screen(
            screen_x, screen_y, window_width, window_height, vs
        )
        if result is None:
            return None

        face_name, row, col, right_dir, up_dir = result

        # Get the face from the cube
        face = self._cube.face(face_name)
        size = self._cube.size

        # Convert (row, col) to PartEdge
        part_edge = self._get_part_edge_at_cell(face, row, col, size)
        if part_edge is None:
            return None

        return (part_edge, right_dir, up_dir)

    def _get_part_edge_at_cell(self, face, row: int, col: int, size: int):
        """Get the PartEdge at a specific cell on a face.

        Args:
            face: The Face object
            row: Row index (0 = bottom)
            col: Column index (0 = left)
            size: Cube size

        Returns:
            PartEdge for this cell, or None
        """
        from cube.domain.model.PartEdge import PartEdge

        last = size - 1

        # Corners (at the 4 corners of the face)
        if row == 0 and col == 0:
            return face.corner_bottom_left.slice.get_face_edge(face)
        if row == 0 and col == last:
            return face.corner_bottom_right.slice.get_face_edge(face)
        if row == last and col == 0:
            return face.corner_top_left.slice.get_face_edge(face)
        if row == last and col == last:
            return face.corner_top_right.slice.get_face_edge(face)

        # For 3x3 cube
        if size == 3:
            # Edges (middle of each border)
            if row == 0 and col == 1:
                return face.edge_bottom.get_slice_by_ltr_index(face, 0).get_face_edge(face)
            if row == last and col == 1:
                return face.edge_top.get_slice_by_ltr_index(face, 0).get_face_edge(face)
            if row == 1 and col == 0:
                return face.edge_left.get_slice_by_ltr_index(face, 0).get_face_edge(face)
            if row == 1 and col == last:
                return face.edge_right.get_slice_by_ltr_index(face, 0).get_face_edge(face)

            # Center
            if row == 1 and col == 1:
                return face.center.get_slice((0, 0)).get_face_edge(face)
        else:
            # NxN cube

            # Bottom edge (excluding corners)
            if row == 0 and 0 < col < last:
                idx = col - 1
                return face.edge_bottom.get_slice_by_ltr_index(face, idx).get_face_edge(face)

            # Top edge (excluding corners)
            if row == last and 0 < col < last:
                idx = col - 1
                return face.edge_top.get_slice_by_ltr_index(face, idx).get_face_edge(face)

            # Left edge (excluding corners)
            if col == 0 and 0 < row < last:
                idx = row - 1
                return face.edge_left.get_slice_by_ltr_index(face, idx).get_face_edge(face)

            # Right edge (excluding corners)
            if col == last and 0 < row < last:
                idx = row - 1
                return face.edge_right.get_slice_by_ltr_index(face, idx).get_face_edge(face)

            # Center (the middle area)
            if 0 < row < last and 0 < col < last:
                center_row = row - 1
                center_col = col - 1
                return face.center.get_slice((center_row, center_col)).get_face_edge(face)

        return None
