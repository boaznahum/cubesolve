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
    Markers: 9 floats per vertex (x, y, z, nx, ny, nz, r, g, b) - same as faces
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
from numpy import ndarray

from cube.domain.model.cube_boy import Color
from cube.domain.model.VMarker import VMarker, viewer_get_markers

if TYPE_CHECKING:
    from cube.domain.model._part_slice import PartSlice
    from cube.domain.model.PartEdge import PartEdge

from ._modern_gl_constants import CELL_TEXTURE_KEY

# Number of segments for ring geometry (more = smoother circle)
_RING_SEGMENTS = 32  # Increased for smoother 3D rings

# Marker definitions: name -> (radius_factor, thickness, height_offset)
# Color is now determined dynamically based on face color (complementary)
_MARKER_DEFS: dict[str, tuple[float, float, float]] = {
    "C0": (1.0, 0.8, 0.15),   # Full ring, raised
    "C1": (0.6, 1.0, 0.15),   # Filled circle, raised
    "C2": (1.0, 0.3, 0.15),   # Thin ring, raised
}

# Complementary colors for each cube face color (RGB 0.0-1.0)
# These provide maximum contrast for visibility
_COMPLEMENTARY_COLORS: dict[tuple[float, float, float], tuple[float, float, float]] = {
    # Red face -> Cyan marker
    (1.0, 0.0, 0.0): (0.0, 1.0, 1.0),
    # Green face -> Magenta marker
    (0.0, 1.0, 0.0): (1.0, 0.0, 1.0),
    # Blue face -> Yellow marker
    (0.0, 0.0, 1.0): (1.0, 1.0, 0.0),
    # Yellow face -> Blue/Purple marker
    (1.0, 1.0, 0.0): (0.4, 0.2, 1.0),
    # Orange face -> Cyan marker
    (1.0, 0.5, 0.0): (0.0, 1.0, 1.0),
    # White face -> Dark magenta marker
    (1.0, 1.0, 1.0): (0.6, 0.0, 0.6),
}

# Default marker color if face color not found (bright magenta)
_DEFAULT_MARKER_COLOR = (1.0, 0.0, 1.0)

# Border line color (black)
_LINE_COLOR = (0.0, 0.0, 0.0)


def _get_complementary_color(face_color: tuple[float, float, float]) -> tuple[float, float, float]:
    """Get a complementary marker color for maximum contrast.

    Args:
        face_color: RGB tuple (0.0-1.0) of the face color

    Returns:
        RGB tuple for the marker color
    """
    # Round to handle floating point imprecision
    rounded = (round(face_color[0], 1), round(face_color[1], 1), round(face_color[2], 1))
    return _COMPLEMENTARY_COLORS.get(rounded, _DEFAULT_MARKER_COLOR)


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
        part_edge: The PartEdge for this face (for texture lookup from c_attributes)
    """

    __slots__ = [
        'row', 'col', 'part_slice', 'part_edge',
        '_corners',  # [left_bottom, right_bottom, right_top, left_top]
        '_normal',   # Face normal vector
        '_color',    # RGB color tuple
    ]

    def __init__(
        self,
        row: int,
        col: int,
        part_slice: "PartSlice | None",
        part_edge: "PartEdge | None",
        corners: list[ndarray],
        normal: ndarray,
        color: tuple[float, float, float],
    ) -> None:
        """Initialize a cell with geometry.

        Args:
            row: Row index (0 = bottom row)
            col: Column index (0 = left column)
            part_slice: The PartSlice for animation tracking (None for centers on some sizes)
            part_edge: The PartEdge for this face (for texture from c_attributes)
            corners: List of 4 corner positions [lb, rb, rt, lt] as numpy arrays
            normal: Face normal vector (outward direction)
            color: RGB color tuple (0.0-1.0 range)
        """
        self.row = row
        self.col = col
        self.part_slice = part_slice
        self.part_edge = part_edge
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

    def generate_full_uv_vertices(self, dest: list[float]) -> None:
        """Generate triangle vertices with full UV range, applying texture rotation.

        Used for per-cell textures where each cell has its own texture.
        The entire texture maps to the entire cell quad.

        The texture rotation is read from part_edge.texture_direction and applied
        to UV coordinates to make the texture appear rotated.

        UV rotations (to make texture appear rotated CW by direction * 90°):
        - Direction 0 (0°):   lb=(0,0), rb=(1,0), rt=(1,1), lt=(0,1)
        - Direction 1 (90°):  lb=(0,1), rb=(0,0), rt=(1,0), lt=(1,1)
        - Direction 2 (180°): lb=(1,1), rb=(0,1), rt=(0,0), lt=(1,0)
        - Direction 3 (270°): lb=(1,0), rb=(1,1), rt=(0,1), lt=(0,0)

        Appends 6 vertices (2 triangles) to dest.
        Each vertex: x, y, z, nx, ny, nz, r, g, b, u, v (11 floats)

        Args:
            dest: List to append vertex data to
        """
        lb, rb, rt, lt = self._corners
        nx, ny, nz = float(self._normal[0]), float(self._normal[1]), float(self._normal[2])
        r, g, b = self._color

        # Get texture direction from PartEdge (0-3, representing 0°/90°/180°/270° CW)
        direction = 0
        if self.part_edge is not None:
            direction = self.part_edge.texture_direction

        # UV coordinates for each direction
        # Format: (lb_uv, rb_uv, rt_uv, lt_uv)
        # All 4 possible 90° rotation mappings:
        UV_OPTIONS = [
            ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),  # 0: standard (arrow up)
            ((0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)),  # 1: 90° CW (arrow right)
            ((1.0, 1.0), (0.0, 1.0), (0.0, 0.0), (1.0, 0.0)),  # 2: 180° (arrow down)
            ((1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)),  # 3: 270° CW (arrow left)
        ]

        # Map direction to UV option - fixed mapping, decision logic is in Face.py
        UV_INDICES = [0, 3, 2, 1]  # direction 0→option 0, 1→3, 2→2, 3→1
        UV_BY_DIRECTION = [UV_OPTIONS[i] for i in UV_INDICES]
        uv_lb, uv_rb, uv_rt, uv_lt = UV_BY_DIRECTION[direction]

        # Triangle 1: lb, rb, rt
        dest.extend([lb[0], lb[1], lb[2], nx, ny, nz, r, g, b, uv_lb[0], uv_lb[1]])
        dest.extend([rb[0], rb[1], rb[2], nx, ny, nz, r, g, b, uv_rb[0], uv_rb[1]])
        dest.extend([rt[0], rt[1], rt[2], nx, ny, nz, r, g, b, uv_rt[0], uv_rt[1]])

        # Triangle 2: lb, rt, lt
        dest.extend([lb[0], lb[1], lb[2], nx, ny, nz, r, g, b, uv_lb[0], uv_lb[1]])
        dest.extend([rt[0], rt[1], rt[2], nx, ny, nz, r, g, b, uv_rt[0], uv_rt[1]])
        dest.extend([lt[0], lt[1], lt[2], nx, ny, nz, r, g, b, uv_lt[0], uv_lt[1]])

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

    @property
    def cell_texture(self) -> int | None:
        """Get the cell-specific texture handle from c_attributes.

        Returns:
            Texture handle if stored in c_attributes, None otherwise.
        """
        if self.part_edge is None:
            return None
        return self.part_edge.c_attributes.get(CELL_TEXTURE_KEY)

    def get_markers(self) -> Sequence[VMarker] | None:
        """Get markers for this cell from both c_attributes and f_attributes.

        Markers are visual annotations added by the solver during animation
        to highlight pieces being tracked:
        - c_attributes: markers on moving pieces (follow the piece)
        - f_attributes: markers on fixed positions (stay in place)

        Returns:
            Sequence of VMarker enums, or None if no markers.
        """
        if self.part_edge is None:
            return None

        # Get markers from both moving (c_attributes) and fixed (f_attributes)
        c_markers = viewer_get_markers(self.part_edge.c_attributes)
        f_markers = viewer_get_markers(self.part_edge.f_attributes)

        # Combine both lists
        if c_markers and f_markers:
            return list(c_markers) + list(f_markers)
        elif c_markers:
            return c_markers
        elif f_markers:
            return f_markers
        return None

    def has_markers(self) -> bool:
        """Check if this cell has any markers.

        Returns:
            True if cell has markers to render.
        """
        markers = self.get_markers()
        return markers is not None and len(markers) > 0

    def generate_marker_vertices(self, dest: list[float]) -> None:
        """Generate triangle vertices for 3D raised marker rings/circles.

        Creates 3D cylinder/ring geometry for each marker on this cell.
        The marker is a raised cylinder above the cell surface with:
        - Top face (ring or filled circle)
        - Outer cylinder wall
        - Inner cylinder wall (for rings)

        Uses complementary colors for maximum contrast against the face color.

        Appends triangles to dest.
        Each vertex: x, y, z, nx, ny, nz, r, g, b (9 floats)

        Args:
            dest: List to append vertex data to
        """
        markers = self.get_markers()
        if not markers:
            return

        # Calculate cell center and size
        lb, rb, rt, lt = self._corners
        center = (lb + rb + rt + lt) / 4.0

        # Cell size (use minimum of width/height for radius)
        width = float(np.linalg.norm(rb - lb))
        height = float(np.linalg.norm(lt - lb))
        cell_size = min(width, height)

        # Normal vector (already normalized)
        normal = (float(self._normal[0]), float(self._normal[1]), float(self._normal[2]))

        # Get complementary color based on face color for maximum contrast
        marker_color = _get_complementary_color(self._color)

        # Generate geometry for each marker
        for marker in markers:
            marker_def = _MARKER_DEFS.get(marker.value)
            if marker_def is None:
                continue

            radius_factor, thick, height_offset = marker_def

            # Calculate actual radius
            base_radius = cell_size * 0.4  # 40% of cell size
            outer_radius = base_radius * radius_factor
            inner_radius = outer_radius * (1.0 - thick)

            # Height of the 3D cylinder
            marker_height = height_offset * cell_size

            # Generate 3D raised ring/cylinder
            self._generate_3d_ring(
                dest,
                center,
                inner_radius,
                outer_radius,
                marker_height,
                normal,
                marker_color,
            )

    def _generate_3d_ring(
        self,
        dest: list[float],
        base_center: ndarray,
        inner_radius: float,
        outer_radius: float,
        height: float,
        normal: tuple[float, float, float],
        color: tuple[float, float, float],
    ) -> None:
        """Generate a 3D raised ring/cylinder shape.

        Creates a cylinder with:
        - Top face (ring or filled circle)
        - Outer cylinder wall
        - Inner cylinder wall (for rings with inner_radius > 0)

        Args:
            dest: List to append vertex data to
            base_center: Center point at the base (cell surface)
            inner_radius: Inner radius (0 for filled circle)
            outer_radius: Outer radius
            height: Height of the cylinder above the surface
            normal: Face normal vector (nx, ny, nz)
            color: RGB color (0.0-1.0 range)
        """
        nx, ny, nz = normal
        r, g, b = color
        normal_vec = np.array([nx, ny, nz])

        # Top center is offset by height along the normal
        top_center = base_center + normal_vec * height

        # Create two perpendicular vectors in the plane of the ring
        if abs(nx) < 0.9:
            up = np.array([1.0, 0.0, 0.0])
        else:
            up = np.array([0.0, 1.0, 0.0])

        tangent1 = np.cross(normal_vec, up)
        tangent1 = tangent1 / np.linalg.norm(tangent1)
        tangent2 = np.cross(normal_vec, tangent1)

        # Generate segments
        for i in range(_RING_SEGMENTS):
            angle1 = 2 * math.pi * i / _RING_SEGMENTS
            angle2 = 2 * math.pi * (i + 1) / _RING_SEGMENTS

            cos1, sin1 = math.cos(angle1), math.sin(angle1)
            cos2, sin2 = math.cos(angle2), math.sin(angle2)

            # Direction vectors for this segment
            dir1 = cos1 * tangent1 + sin1 * tangent2
            dir2 = cos2 * tangent1 + sin2 * tangent2

            # Points on outer circle (top and bottom)
            outer_top1 = top_center + outer_radius * dir1
            outer_top2 = top_center + outer_radius * dir2
            outer_bot1 = base_center + outer_radius * dir1
            outer_bot2 = base_center + outer_radius * dir2

            # Points on inner circle (top and bottom)
            inner_top1 = top_center + inner_radius * dir1
            inner_top2 = top_center + inner_radius * dir2
            inner_bot1 = base_center + inner_radius * dir1
            inner_bot2 = base_center + inner_radius * dir2

            # === TOP FACE (ring) ===
            # Triangle 1: outer_top1, outer_top2, inner_top1
            for p in [outer_top1, outer_top2, inner_top1]:
                dest.extend([p[0], p[1], p[2], nx, ny, nz, r, g, b])
            # Triangle 2: inner_top1, outer_top2, inner_top2
            for p in [inner_top1, outer_top2, inner_top2]:
                dest.extend([p[0], p[1], p[2], nx, ny, nz, r, g, b])

            # === OUTER WALL ===
            # Outward-facing normal for outer wall
            out_norm1 = dir1
            out_norm2 = dir2
            out_norm_avg = (out_norm1 + out_norm2) / 2
            out_norm_avg = out_norm_avg / np.linalg.norm(out_norm_avg)
            onx, ony, onz = float(out_norm_avg[0]), float(out_norm_avg[1]), float(out_norm_avg[2])

            # Triangle 1: outer_top1, outer_bot1, outer_top2
            for p in [outer_top1, outer_bot1, outer_top2]:
                dest.extend([p[0], p[1], p[2], onx, ony, onz, r, g, b])
            # Triangle 2: outer_top2, outer_bot1, outer_bot2
            for p in [outer_top2, outer_bot1, outer_bot2]:
                dest.extend([p[0], p[1], p[2], onx, ony, onz, r, g, b])

            # === INNER WALL (only if inner_radius > 0) ===
            if inner_radius > 0.001:
                # Inward-facing normal for inner wall (negative of outward)
                inx, iny, inz = -onx, -ony, -onz

                # Triangle 1: inner_top1, inner_top2, inner_bot1
                for p in [inner_top1, inner_top2, inner_bot1]:
                    dest.extend([p[0], p[1], p[2], inx, iny, inz, r, g, b])
                # Triangle 2: inner_top2, inner_bot2, inner_bot1
                for p in [inner_top2, inner_bot2, inner_bot1]:
                    dest.extend([p[0], p[1], p[2], inx, iny, inz, r, g, b])
