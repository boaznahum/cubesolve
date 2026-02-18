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
from typing import TYPE_CHECKING

import numpy as np
from numpy import ndarray

from cube.application.markers import MarkerConfig, MarkerShape, get_markers_from_part_edge
from cube.application.markers._marker_creator_protocol import MarkerCreator
from cube.domain.geometric.cube_boy import Color
from cube.domain.tracker.FacesTrackerHolder import FacesTrackerHolder

if TYPE_CHECKING:
    from cube.domain.model.PartSlice import PartSlice
    from cube.domain.model.PartEdge import PartEdge

from ._modern_gl_constants import CELL_TEXTURE_KEY

# Number of segments for ring geometry (more = smoother circle)
_RING_SEGMENTS = 32  # Increased for smoother 3D rings

# Marker definitions now come from MarkerConfig - no static definitions needed

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

# Tracker indicator configuration (small filled circle showing tracker's assigned color)
# These indicators appear on center slices that are marked as tracker anchors (even cubes)
# TODO: Move to ConfigProtocol for runtime configurability
_TRACKER_INDICATOR_RADIUS_FACTOR = 0.25  # 25% of cell size (smaller than markers)
_TRACKER_INDICATOR_HEIGHT = 0.10         # Height offset above surface
_TRACKER_INDICATOR_OUTLINE_WIDTH = 0.15  # Black outline width as fraction of radius
_TRACKER_INDICATOR_OUTLINE_COLOR = (0.0, 0.0, 0.0)  # Black outline for visibility

# Border line color (black)
_LINE_COLOR = (0.0, 0.0, 0.0)


# Simple line-based font for character markers
# Each character is defined as list of line segments: (x1, y1, x2, y2)
# Coordinates are normalized: -1 to 1 range, centered at origin
_CHAR_SEGMENTS: dict[str, list[tuple[float, float, float, float]]] = {
    # Letters
    "A": [(-0.5, -1, 0, 1), (0, 1, 0.5, -1), (-0.3, 0, 0.3, 0)],
    "B": [(-0.4, -1, -0.4, 1), (-0.4, 1, 0.3, 1), (0.3, 1, 0.4, 0.5), (0.4, 0.5, 0.3, 0),
          (-0.4, 0, 0.3, 0), (0.3, 0, 0.4, -0.5), (0.4, -0.5, 0.3, -1), (0.3, -1, -0.4, -1)],
    "C": [(0.4, 0.7, 0, 1), (0, 1, -0.4, 0.5), (-0.4, 0.5, -0.4, -0.5),
          (-0.4, -0.5, 0, -1), (0, -1, 0.4, -0.7)],
    "D": [(-0.4, -1, -0.4, 1), (-0.4, 1, 0.2, 1), (0.2, 1, 0.4, 0.5),
          (0.4, 0.5, 0.4, -0.5), (0.4, -0.5, 0.2, -1), (0.2, -1, -0.4, -1)],
    "E": [(-0.4, -1, -0.4, 1), (-0.4, 1, 0.4, 1), (-0.4, 0, 0.2, 0), (-0.4, -1, 0.4, -1)],
    "F": [(-0.4, -1, -0.4, 1), (-0.4, 1, 0.4, 1), (-0.4, 0, 0.2, 0)],
    "G": [(0.4, 0.7, 0, 1), (0, 1, -0.4, 0.5), (-0.4, 0.5, -0.4, -0.5),
          (-0.4, -0.5, 0, -1), (0, -1, 0.4, -0.5), (0.4, -0.5, 0.4, 0), (0.4, 0, 0, 0)],
    "H": [(-0.4, -1, -0.4, 1), (0.4, -1, 0.4, 1), (-0.4, 0, 0.4, 0)],
    "I": [(-0.2, 1, 0.2, 1), (0, 1, 0, -1), (-0.2, -1, 0.2, -1)],
    "J": [(0.4, 1, 0.4, -0.5), (0.4, -0.5, 0, -1), (0, -1, -0.4, -0.5)],
    "K": [(-0.4, -1, -0.4, 1), (0.4, 1, -0.4, 0), (-0.4, 0, 0.4, -1)],
    "L": [(-0.4, 1, -0.4, -1), (-0.4, -1, 0.4, -1)],
    "M": [(-0.4, -1, -0.4, 1), (-0.4, 1, 0, 0), (0, 0, 0.4, 1), (0.4, 1, 0.4, -1)],
    "N": [(-0.4, -1, -0.4, 1), (-0.4, 1, 0.4, -1), (0.4, -1, 0.4, 1)],
    "O": [(0, 1, -0.4, 0.5), (-0.4, 0.5, -0.4, -0.5), (-0.4, -0.5, 0, -1),
          (0, -1, 0.4, -0.5), (0.4, -0.5, 0.4, 0.5), (0.4, 0.5, 0, 1)],
    "P": [(-0.4, -1, -0.4, 1), (-0.4, 1, 0.3, 1), (0.3, 1, 0.4, 0.5),
          (0.4, 0.5, 0.3, 0), (0.3, 0, -0.4, 0)],
    "Q": [(0, 1, -0.4, 0.5), (-0.4, 0.5, -0.4, -0.5), (-0.4, -0.5, 0, -1),
          (0, -1, 0.4, -0.5), (0.4, -0.5, 0.4, 0.5), (0.4, 0.5, 0, 1), (0.1, -0.3, 0.5, -1)],
    "R": [(-0.4, -1, -0.4, 1), (-0.4, 1, 0.3, 1), (0.3, 1, 0.4, 0.5),
          (0.4, 0.5, 0.3, 0), (0.3, 0, -0.4, 0), (0, 0, 0.4, -1)],
    "S": [(0.4, 0.7, 0, 1), (0, 1, -0.4, 0.5), (-0.4, 0.5, 0.4, -0.5),
          (0.4, -0.5, 0, -1), (0, -1, -0.4, -0.7)],
    "T": [(-0.4, 1, 0.4, 1), (0, 1, 0, -1)],
    "U": [(-0.4, 1, -0.4, -0.5), (-0.4, -0.5, 0, -1), (0, -1, 0.4, -0.5), (0.4, -0.5, 0.4, 1)],
    "V": [(-0.4, 1, 0, -1), (0, -1, 0.4, 1)],
    "W": [(-0.4, 1, -0.2, -1), (-0.2, -1, 0, 0), (0, 0, 0.2, -1), (0.2, -1, 0.4, 1)],
    "X": [(-0.4, 1, 0.4, -1), (-0.4, -1, 0.4, 1)],
    "Y": [(-0.4, 1, 0, 0), (0.4, 1, 0, 0), (0, 0, 0, -1)],
    "Z": [(-0.4, 1, 0.4, 1), (0.4, 1, -0.4, -1), (-0.4, -1, 0.4, -1)],
    # Digits
    "0": [(0, 1, -0.4, 0.5), (-0.4, 0.5, -0.4, -0.5), (-0.4, -0.5, 0, -1),
          (0, -1, 0.4, -0.5), (0.4, -0.5, 0.4, 0.5), (0.4, 0.5, 0, 1)],
    "1": [(-0.2, 0.5, 0, 1), (0, 1, 0, -1), (-0.3, -1, 0.3, -1)],
    "2": [(-0.4, 0.5, 0, 1), (0, 1, 0.4, 0.5), (0.4, 0.5, -0.4, -1), (-0.4, -1, 0.4, -1)],
    "3": [(-0.4, 1, 0.4, 1), (0.4, 1, 0, 0), (0, 0, 0.4, 0), (0.4, 0, 0.4, -0.5),
          (0.4, -0.5, 0, -1), (0, -1, -0.4, -1)],
    "4": [(-0.4, 1, -0.4, 0), (-0.4, 0, 0.4, 0), (0.4, 1, 0.4, -1)],
    "5": [(0.4, 1, -0.4, 1), (-0.4, 1, -0.4, 0), (-0.4, 0, 0.4, 0),
          (0.4, 0, 0.4, -0.5), (0.4, -0.5, 0, -1), (0, -1, -0.4, -0.7)],
    "6": [(0.4, 0.7, 0, 1), (0, 1, -0.4, 0.5), (-0.4, 0.5, -0.4, -0.5),
          (-0.4, -0.5, 0, -1), (0, -1, 0.4, -0.5), (0.4, -0.5, 0.4, 0),
          (0.4, 0, -0.4, 0)],
    "7": [(-0.4, 1, 0.4, 1), (0.4, 1, 0, -1)],
    "8": [(0, 1, -0.3, 0.7), (-0.3, 0.7, -0.3, 0.3), (-0.3, 0.3, 0, 0),
          (0, 0, 0.3, 0.3), (0.3, 0.3, 0.3, 0.7), (0.3, 0.7, 0, 1),
          (0, 0, -0.4, -0.3), (-0.4, -0.3, -0.4, -0.7), (-0.4, -0.7, 0, -1),
          (0, -1, 0.4, -0.7), (0.4, -0.7, 0.4, -0.3), (0.4, -0.3, 0, 0)],
    "9": [(-0.4, -0.7, 0, -1), (0, -1, 0.4, -0.5), (0.4, -0.5, 0.4, 0.5),
          (0.4, 0.5, 0, 1), (0, 1, -0.4, 0.5), (-0.4, 0.5, -0.4, 0),
          (-0.4, 0, 0.4, 0)],
    # Symbols
    "+": [(-0.4, 0, 0.4, 0), (0, -0.6, 0, 0.6)],
    "-": [(-0.4, 0, 0.4, 0)],
    "*": [(-0.3, 0.3, 0.3, -0.3), (-0.3, -0.3, 0.3, 0.3), (-0.4, 0, 0.4, 0)],
    "/": [(-0.3, -1, 0.3, 1)],
    "?": [(0, -1, 0, -0.8), (0, -0.3, 0, 0), (0, 0, 0.3, 0.3), (0.3, 0.3, 0.3, 0.7),
          (0.3, 0.7, 0, 1), (0, 1, -0.3, 0.7)],
}


def _get_char_segments(char: str) -> list[tuple[float, float, float, float]]:
    """Get line segments for a character.

    Args:
        char: Single uppercase character

    Returns:
        List of (x1, y1, x2, y2) line segments in normalized coordinates.
    """
    return _CHAR_SEGMENTS.get(char, _CHAR_SEGMENTS.get("?", []))


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


class ModernGLCellToolkit:
    """MarkerToolkit implementation for the modern (VBO-based) renderer.

    Translates abstract marker drawing primitives into vertex data appended
    to destination lists for VBO rendering.

    Implements the MarkerToolkit protocol.
    """

    __slots__ = [
        '_triangle_dest', '_line_dest', '_corners', '_normal', '_color',
        '_cell_size', '_complementary',
    ]

    def __init__(
        self,
        triangle_dest: list[float],
        line_dest: list[float] | None,
        corners: list[ndarray],
        normal: ndarray,
        color: tuple[float, float, float],
    ) -> None:
        self._triangle_dest = triangle_dest
        self._line_dest = line_dest
        self._corners = corners
        self._normal = normal
        self._color = color

        # Calculate cell size
        lb, rb, _rt, lt = corners
        width = float(np.linalg.norm(rb - lb))
        height = float(np.linalg.norm(lt - lb))
        self._cell_size = min(width, height)

        self._complementary = _get_complementary_color(color)

    @property
    def face_color(self) -> tuple[float, float, float]:
        return self._color

    @property
    def complementary_color(self) -> tuple[float, float, float]:
        return self._complementary

    def draw_ring(
        self,
        inner_radius: float,
        outer_radius: float,
        color: tuple[float, float, float],
        height: float,
    ) -> None:
        lb, rb, rt, lt = self._corners
        center = (lb + rb + rt + lt) / 4.0
        normal = (float(self._normal[0]), float(self._normal[1]), float(self._normal[2]))

        base_r = self._cell_size * 0.4
        actual_outer = base_r * outer_radius
        actual_inner = base_r * inner_radius
        actual_height = height * self._cell_size

        _generate_3d_ring_standalone(
            self._triangle_dest, center, actual_inner, actual_outer,
            actual_height, normal, color, self._normal,
        )

    def draw_filled_circle(
        self,
        radius: float,
        color: tuple[float, float, float],
        height: float,
    ) -> None:
        self.draw_ring(0.0, radius, color, height)

    def draw_cross(self, color: tuple[float, float, float]) -> None:
        if self._line_dest is None:
            return
        lb, rb, rt, lt = self._corners
        r, g, b = color
        # Draw X from corner to corner
        self._line_dest.extend([lb[0], lb[1], lb[2], r, g, b])
        self._line_dest.extend([rt[0], rt[1], rt[2], r, g, b])
        self._line_dest.extend([rb[0], rb[1], rb[2], r, g, b])
        self._line_dest.extend([lt[0], lt[1], lt[2], r, g, b])

    def draw_arrow(
        self,
        color: tuple[float, float, float],
        direction: float,
        radius_factor: float,
        thickness: float,
    ) -> None:
        # Delegate to standalone function
        _generate_arrow_standalone(
            self._triangle_dest, self._corners, self._normal,
            color, direction, radius_factor, thickness,
        )

    def draw_checkmark(
        self,
        color: tuple[float, float, float],
        radius_factor: float,
        thickness: float,
        height_offset: float,
    ) -> None:
        _generate_checkmark_standalone(
            self._triangle_dest, self._corners, self._normal,
            color, radius_factor, thickness, height_offset,
        )

    def draw_bold_cross(
        self,
        color: tuple[float, float, float],
        radius_factor: float,
        thickness: float,
        height_offset: float,
    ) -> None:
        _generate_bold_cross_standalone(
            self._triangle_dest, self._corners, self._normal,
            color, radius_factor, thickness, height_offset,
        )

    def draw_character(
        self,
        character: str,
        color: tuple[float, float, float],
        radius_factor: float,
    ) -> None:
        if self._line_dest is None:
            return
        _generate_character_standalone(
            self._line_dest, self._corners, self._normal,
            character, color, radius_factor,
        )


def _generate_3d_ring_standalone(
    dest: list[float],
    base_center: ndarray,
    inner_radius: float,
    outer_radius: float,
    height: float,
    normal: tuple[float, float, float],
    color: tuple[float, float, float],
    normal_vec_arr: ndarray,
) -> None:
    """Generate a 3D raised ring/cylinder shape (standalone version).

    Identical to ModernGLCell._generate_3d_ring but callable without a cell instance.
    """
    nx, ny, nz = normal
    r, g, b = color

    top_center = base_center + normal_vec_arr * height

    if abs(nx) < 0.9:
        up = np.array([1.0, 0.0, 0.0])
    else:
        up = np.array([0.0, 1.0, 0.0])

    tangent1 = np.cross(normal_vec_arr, up)
    tangent1 = tangent1 / np.linalg.norm(tangent1)
    tangent2 = np.cross(normal_vec_arr, tangent1)

    for i in range(_RING_SEGMENTS):
        angle1 = 2 * math.pi * i / _RING_SEGMENTS
        angle2 = 2 * math.pi * (i + 1) / _RING_SEGMENTS

        cos1, sin1 = math.cos(angle1), math.sin(angle1)
        cos2, sin2 = math.cos(angle2), math.sin(angle2)

        dir1 = cos1 * tangent1 + sin1 * tangent2
        dir2 = cos2 * tangent1 + sin2 * tangent2

        outer_top1 = top_center + outer_radius * dir1
        outer_top2 = top_center + outer_radius * dir2
        outer_bot1 = base_center + outer_radius * dir1
        outer_bot2 = base_center + outer_radius * dir2

        inner_top1 = top_center + inner_radius * dir1
        inner_top2 = top_center + inner_radius * dir2
        inner_bot1 = base_center + inner_radius * dir1
        inner_bot2 = base_center + inner_radius * dir2

        # TOP FACE
        for p in [outer_top1, outer_top2, inner_top1]:
            dest.extend([p[0], p[1], p[2], nx, ny, nz, r, g, b])
        for p in [inner_top1, outer_top2, inner_top2]:
            dest.extend([p[0], p[1], p[2], nx, ny, nz, r, g, b])

        # OUTER WALL
        out_norm_avg = (dir1 + dir2) / 2
        out_norm_avg = out_norm_avg / np.linalg.norm(out_norm_avg)
        onx, ony, onz = float(out_norm_avg[0]), float(out_norm_avg[1]), float(out_norm_avg[2])

        for p in [outer_top1, outer_bot1, outer_top2]:
            dest.extend([p[0], p[1], p[2], onx, ony, onz, r, g, b])
        for p in [outer_top2, outer_bot1, outer_bot2]:
            dest.extend([p[0], p[1], p[2], onx, ony, onz, r, g, b])

        # INNER WALL
        if inner_radius > 0.001:
            inx, iny, inz = -onx, -ony, -onz
            for p in [inner_top1, inner_top2, inner_bot1]:
                dest.extend([p[0], p[1], p[2], inx, iny, inz, r, g, b])
            for p in [inner_top2, inner_bot2, inner_bot1]:
                dest.extend([p[0], p[1], p[2], inx, iny, inz, r, g, b])


def _generate_arrow_standalone(
    dest: list[float],
    corners: list[ndarray],
    normal: ndarray,
    color: tuple[float, float, float],
    direction: float,
    radius_factor: float,
    thickness: float,
) -> None:
    """Generate filled arrow marker vertices."""
    lb, rb, rt, lt = corners
    nx, ny, nz = float(normal[0]), float(normal[1]), float(normal[2])
    r, g, b = color

    center = (lb + rb + rt + lt) / 4.0
    right_vec = (rb - lb) / 2.0
    up_vec = (lt - lb) / 2.0
    height_offset = normal * 0.15

    angle_rad = math.radians(direction)
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
    dir_vec = right_vec * cos_a + up_vec * sin_a
    perp_vec = right_vec * (-sin_a) + up_vec * cos_a

    shaft_length = radius_factor * 0.7
    shaft_width = thickness * 0.12
    head_length = 0.3
    head_width = thickness * 0.25

    shaft_start = center - dir_vec * shaft_length * 0.4 + height_offset
    shaft_end = center + dir_vec * shaft_length * 0.4 + height_offset

    s1 = shaft_start - perp_vec * shaft_width
    s2 = shaft_start + perp_vec * shaft_width
    s3 = shaft_end + perp_vec * shaft_width
    s4 = shaft_end - perp_vec * shaft_width

    for v in [s1, s2, s3, s1, s3, s4]:
        dest.extend([v[0], v[1], v[2], nx, ny, nz, r, g, b])

    head_tip = shaft_end + dir_vec * head_length
    head_base1 = shaft_end - perp_vec * head_width
    head_base2 = shaft_end + perp_vec * head_width

    for v in [head_base1, head_base2, head_tip]:
        dest.extend([v[0], v[1], v[2], nx, ny, nz, r, g, b])


def _generate_checkmark_standalone(
    dest: list[float],
    corners: list[ndarray],
    normal_vec: ndarray,
    color: tuple[float, float, float],
    radius_factor: float,
    thickness: float,
    height_offset: float,
) -> None:
    """Generate checkmark (plus sign) marker vertices."""
    lb, rb, rt, lt = corners
    center = (lb + rb + rt + lt) / 4.0
    cell_width = float(np.linalg.norm(rb - lb))
    cell_height = float(np.linalg.norm(lt - lb))
    cell_size = min(cell_width, cell_height)
    nx, ny, nz = float(normal_vec[0]), float(normal_vec[1]), float(normal_vec[2])
    r, g, b = color

    outer_radius = cell_size * 0.3 * radius_factor
    stroke_half_width = cell_size * 0.06 * thickness
    box_height = height_offset * cell_size

    right_vec = (rb - lb)
    up_vec_local = (lt - lb)
    right_unit = right_vec / np.linalg.norm(right_vec)
    up_unit = up_vec_local / np.linalg.norm(up_vec_local)

    def add_box(half_w: float, half_h: float, h: float) -> None:
        t0 = center + right_unit * (-half_w) + up_unit * (-half_h) + normal_vec * h
        t1 = center + right_unit * (half_w) + up_unit * (-half_h) + normal_vec * h
        t2 = center + right_unit * (half_w) + up_unit * (half_h) + normal_vec * h
        t3 = center + right_unit * (-half_w) + up_unit * (half_h) + normal_vec * h

        b0 = center + right_unit * (-half_w) + up_unit * (-half_h) + normal_vec * 0.001
        b1 = center + right_unit * (half_w) + up_unit * (-half_h) + normal_vec * 0.001
        b2 = center + right_unit * (half_w) + up_unit * (half_h) + normal_vec * 0.001
        b3 = center + right_unit * (-half_w) + up_unit * (half_h) + normal_vec * 0.001

        # Top face
        dest.extend([t0[0], t0[1], t0[2], nx, ny, nz, r, g, b])
        dest.extend([t1[0], t1[1], t1[2], nx, ny, nz, r, g, b])
        dest.extend([t2[0], t2[1], t2[2], nx, ny, nz, r, g, b])
        dest.extend([t0[0], t0[1], t0[2], nx, ny, nz, r, g, b])
        dest.extend([t2[0], t2[1], t2[2], nx, ny, nz, r, g, b])
        dest.extend([t3[0], t3[1], t3[2], nx, ny, nz, r, g, b])

        walls = [
            (t0, t1, b1, b0, right_unit * 0 - up_unit),
            (t1, t2, b2, b1, right_unit),
            (t2, t3, b3, b2, up_unit),
            (t3, t0, b0, b3, -right_unit),
        ]
        for wt0, wt1, wb1, wb0, wall_dir in walls:
            wn = wall_dir / np.linalg.norm(wall_dir) if np.linalg.norm(wall_dir) > 0.001 else normal_vec
            wnx, wny, wnz = float(wn[0]), float(wn[1]), float(wn[2])
            dest.extend([wt0[0], wt0[1], wt0[2], wnx, wny, wnz, r, g, b])
            dest.extend([wb0[0], wb0[1], wb0[2], wnx, wny, wnz, r, g, b])
            dest.extend([wb1[0], wb1[1], wb1[2], wnx, wny, wnz, r, g, b])
            dest.extend([wt0[0], wt0[1], wt0[2], wnx, wny, wnz, r, g, b])
            dest.extend([wb1[0], wb1[1], wb1[2], wnx, wny, wnz, r, g, b])
            dest.extend([wt1[0], wt1[1], wt1[2], wnx, wny, wnz, r, g, b])

    add_box(outer_radius, stroke_half_width, box_height)
    add_box(stroke_half_width, outer_radius, box_height)


def _generate_bold_cross_standalone(
    dest: list[float],
    corners: list[ndarray],
    normal_vec: ndarray,
    color: tuple[float, float, float],
    radius_factor: float,
    thickness: float,
    height_offset: float,
) -> None:
    """Generate bold cross (X) marker vertices."""
    lb, rb, rt, lt = corners
    center = (lb + rb + rt + lt) / 4.0
    right_vec = (rb - lb) / 2.0
    up_vec = (lt - lb) / 2.0
    cell_width = float(np.linalg.norm(rb - lb))
    cell_height = float(np.linalg.norm(lt - lb))
    cell_size = min(cell_width, cell_height)
    r, g, b = color
    segments = 12

    radius = thickness * 0.14 * cell_size
    height_above = height_offset * cell_size + radius * 0.5
    scale = radius_factor * 0.7

    top_left = center + right_vec * (-0.4 * scale) + up_vec * (0.4 * scale) + normal_vec * height_above
    top_right = center + right_vec * (0.4 * scale) + up_vec * (0.4 * scale) + normal_vec * height_above
    bottom_left = center + right_vec * (-0.4 * scale) + up_vec * (-0.4 * scale) + normal_vec * height_above
    bottom_right = center + right_vec * (0.4 * scale) + up_vec * (-0.4 * scale) + normal_vec * height_above

    def add_capsule(p1: ndarray, p2: ndarray, cap_radius: float) -> None:
        direction = p2 - p1
        length = float(np.linalg.norm(direction))
        if length < 0.001:
            return
        direction = direction / length

        if abs(direction[0]) < 0.9:
            up = np.array([1.0, 0.0, 0.0])
        else:
            up = np.array([0.0, 1.0, 0.0])
        perp1 = np.cross(direction, up)
        perp1 = perp1 / np.linalg.norm(perp1)
        perp2 = np.cross(direction, perp1)

        for i in range(segments):
            angle1 = 2 * math.pi * i / segments
            angle2 = 2 * math.pi * (i + 1) / segments
            cos1, sin1 = math.cos(angle1), math.sin(angle1)
            cos2, sin2 = math.cos(angle2), math.sin(angle2)

            offset1 = (cos1 * perp1 + sin1 * perp2) * cap_radius
            offset2 = (cos2 * perp1 + sin2 * perp2) * cap_radius
            c1_p1 = p1 + offset1
            c2_p1 = p1 + offset2
            c1_p2 = p2 + offset1
            c2_p2 = p2 + offset2
            n1 = cos1 * perp1 + sin1 * perp2
            n2 = cos2 * perp1 + sin2 * perp2

            dest.extend([c1_p1[0], c1_p1[1], c1_p1[2], n1[0], n1[1], n1[2], r, g, b])
            dest.extend([c2_p1[0], c2_p1[1], c2_p1[2], n2[0], n2[1], n2[2], r, g, b])
            dest.extend([c2_p2[0], c2_p2[1], c2_p2[2], n2[0], n2[1], n2[2], r, g, b])
            dest.extend([c1_p1[0], c1_p1[1], c1_p1[2], n1[0], n1[1], n1[2], r, g, b])
            dest.extend([c2_p2[0], c2_p2[1], c2_p2[2], n2[0], n2[1], n2[2], r, g, b])
            dest.extend([c1_p2[0], c1_p2[1], c1_p2[2], n1[0], n1[1], n1[2], r, g, b])

        half_segments = segments // 2
        for end_point, end_dir in [(p1, -direction), (p2, direction)]:
            for j in range(half_segments):
                lat1 = math.pi / 2 * j / half_segments
                lat2 = math.pi / 2 * (j + 1) / half_segments
                cos_lat1, sin_lat1 = math.cos(lat1), math.sin(lat1)
                cos_lat2, sin_lat2 = math.cos(lat2), math.sin(lat2)

                for ii in range(segments):
                    lon1 = 2 * math.pi * ii / segments
                    lon2 = 2 * math.pi * (ii + 1) / segments
                    cos_lon1, sin_lon1 = math.cos(lon1), math.sin(lon1)
                    cos_lon2, sin_lon2 = math.cos(lon2), math.sin(lon2)

                    def sphere_point(cos_lat: float, sin_lat: float, cos_lon: float, sin_lon: float) -> tuple[ndarray, ndarray]:
                        local_n = sin_lat * end_dir + cos_lat * (cos_lon * perp1 + sin_lon * perp2)
                        point = end_point + cap_radius * local_n
                        return point, local_n

                    p1_s, n1_s = sphere_point(cos_lat1, sin_lat1, cos_lon1, sin_lon1)
                    p2_s, n2_s = sphere_point(cos_lat1, sin_lat1, cos_lon2, sin_lon2)
                    p3_s, n3_s = sphere_point(cos_lat2, sin_lat2, cos_lon2, sin_lon2)
                    p4_s, n4_s = sphere_point(cos_lat2, sin_lat2, cos_lon1, sin_lon1)

                    dest.extend([p1_s[0], p1_s[1], p1_s[2], n1_s[0], n1_s[1], n1_s[2], r, g, b])
                    dest.extend([p2_s[0], p2_s[1], p2_s[2], n2_s[0], n2_s[1], n2_s[2], r, g, b])
                    dest.extend([p3_s[0], p3_s[1], p3_s[2], n3_s[0], n3_s[1], n3_s[2], r, g, b])
                    dest.extend([p1_s[0], p1_s[1], p1_s[2], n1_s[0], n1_s[1], n1_s[2], r, g, b])
                    dest.extend([p3_s[0], p3_s[1], p3_s[2], n3_s[0], n3_s[1], n3_s[2], r, g, b])
                    dest.extend([p4_s[0], p4_s[1], p4_s[2], n4_s[0], n4_s[1], n4_s[2], r, g, b])

    add_capsule(top_left, bottom_right, radius)
    add_capsule(bottom_left, top_right, radius)


def _generate_character_standalone(
    dest: list[float],
    corners: list[ndarray],
    normal: ndarray,
    character: str,
    color: tuple[float, float, float],
    radius_factor: float,
) -> None:
    """Generate character line vertices."""
    if not character:
        return

    lb, rb, rt, lt = corners
    center = (lb + rb + rt + lt) / 4.0
    right_vec = (rb - lb) / 2.0
    up_vec = (lt - lb) / 2.0
    height_offset = normal * 0.15
    r, g, b = color

    char = character[0].upper()
    scale = radius_factor * 0.6
    segments = _get_char_segments(char)

    for x1, y1, x2, y2 in segments:
        p1 = center + right_vec * x1 * scale + up_vec * y1 * scale + height_offset
        p2 = center + right_vec * x2 * scale + up_vec * y2 * scale + height_offset
        dest.extend([p1[0], p1[1], p1[2], r, g, b])
        dest.extend([p2[0], p2[1], p2[2], r, g, b])


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

    def generate_cross_line_vertices(self, dest: list[float], markers: list[MarkerCreator] | None = None) -> None:
        """Generate line vertices for cross markers.

        Draws an X (cross) through the cell center for each marker
        with shape == CROSS (origin, on_x, on_y markers).

        Appends 4 vertices per cross (2 line segments forming X) to dest.
        Each vertex: x, y, z, r, g, b (6 floats)

        Args:
            dest: List to append vertex data to
            markers: Optional pre-fetched markers list (avoids repeated lookups)
        """
        if markers is None:
            markers = self.get_markers()
        if not markers:
            return

        # Find cross markers
        cross_markers = [m for m in markers if isinstance(m, MarkerConfig) and m.shape == MarkerShape.CROSS]
        if not cross_markers:
            return

        lb, rb, rt, lt = self._corners

        for marker in cross_markers:
            # Get marker color - use explicit color or default to black
            if marker.color is not None:
                r, g, b = marker.color
            else:
                r, g, b = 0.0, 0.0, 0.0

            # Draw X from corner to corner
            # Line 1: lb to rt (diagonal)
            dest.extend([lb[0], lb[1], lb[2], r, g, b])
            dest.extend([rt[0], rt[1], rt[2], r, g, b])
            # Line 2: rb to lt (other diagonal)
            dest.extend([rb[0], rb[1], rb[2], r, g, b])
            dest.extend([lt[0], lt[1], lt[2], r, g, b])

    def generate_arrow_line_vertices(self, _dest: list[float]) -> None:
        """Generate line vertices for arrow markers (thin outline).

        This is called but generates nothing - arrows are rendered as filled
        triangles via generate_arrow_marker_vertices instead.
        """
        # Arrows are rendered as filled shapes, not lines
        pass

    def generate_arrow_marker_vertices(self, dest: list[float], markers: list[MarkerCreator] | None = None) -> None:
        """Generate filled triangle vertices for arrow markers.

        Draws a thick arrow shape for each marker with shape == ARROW.
        The arrow points in the direction specified by marker.direction:
        - 0° = right (X+ direction)
        - 90° = up (Y+ direction)
        - 180° = left (X- direction)
        - 270° = down (Y- direction)

        Arrow geometry:
        - Rectangular shaft (2 triangles)
        - Triangular arrowhead (1 triangle)

        Appends triangle vertices to dest.
        Each vertex: x, y, z, nx, ny, nz, r, g, b (9 floats)

        Args:
            dest: List to append vertex data to
            markers: Optional pre-fetched markers list (avoids repeated lookups)
        """
        if markers is None:
            markers = self.get_markers()
        if not markers:
            return

        # Find arrow markers
        arrow_markers = [m for m in markers if isinstance(m, MarkerConfig) and m.shape == MarkerShape.ARROW]
        if not arrow_markers:
            return

        lb, rb, rt, lt = self._corners
        nx, ny, nz = float(self._normal[0]), float(self._normal[1]), float(self._normal[2])

        # Calculate cell center and edge vectors
        center = (lb + rb + rt + lt) / 4.0
        right_vec = (rb - lb) / 2.0  # Half-width vector pointing right
        up_vec = (lt - lb) / 2.0     # Half-height vector pointing up

        # Height offset to raise arrows above face surface
        height_offset = self._normal * 0.15

        for marker in arrow_markers:
            # Get marker color
            if marker.color is not None:
                r, g, b = marker.color
            else:
                r, g, b = 0.0, 0.0, 0.0

            # Calculate direction and perpendicular vectors
            angle_rad = math.radians(marker.direction)
            cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)

            # Direction vector in face-local coordinates (0° = right, 90° = up)
            dir_vec = right_vec * cos_a + up_vec * sin_a
            # Perpendicular vector for shaft width
            perp_vec = right_vec * (-sin_a) + up_vec * cos_a

            # Arrow dimensions based on marker properties
            shaft_length = marker.radius_factor * 0.7
            shaft_width = marker.thickness * 0.12  # Shaft thickness
            head_length = 0.3  # Arrowhead length
            head_width = marker.thickness * 0.25   # Arrowhead base width

            # Shaft vertices (rectangle from shaft_start to shaft_end)
            shaft_start = center - dir_vec * shaft_length * 0.4 + height_offset
            shaft_end = center + dir_vec * shaft_length * 0.4 + height_offset

            # Four corners of the shaft rectangle
            s1 = shaft_start - perp_vec * shaft_width
            s2 = shaft_start + perp_vec * shaft_width
            s3 = shaft_end + perp_vec * shaft_width
            s4 = shaft_end - perp_vec * shaft_width

            # Shaft triangles (2 triangles for rectangle)
            for v in [s1, s2, s3, s1, s3, s4]:
                dest.extend([v[0], v[1], v[2], nx, ny, nz, r, g, b])

            # Arrowhead vertices (triangle)
            head_tip = shaft_end + dir_vec * head_length
            head_base1 = shaft_end - perp_vec * head_width
            head_base2 = shaft_end + perp_vec * head_width

            # Arrowhead triangle
            for v in [head_base1, head_base2, head_tip]:
                dest.extend([v[0], v[1], v[2], nx, ny, nz, r, g, b])

    def generate_checkmark_vertices(self, dest: list[float], markers: list[MarkerCreator] | None = None) -> None:
        """Generate triangle vertices for checkmark markers.

        Creates a sharp 3D plus sign (+) shape as an extruded cross with flat top
        and vertical sides - matching the ring markers' crisp appearance.

        Appends triangles to dest.
        Each vertex: x, y, z, nx, ny, nz, r, g, b (9 floats)

        Args:
            dest: List to append vertex data to
            markers: Optional pre-fetched markers list (avoids repeated lookups)
        """
        if markers is None:
            markers = self.get_markers()
        if not markers:
            return

        # Find checkmark markers
        check_markers = [m for m in markers if isinstance(m, MarkerConfig) and m.shape == MarkerShape.CHECKMARK]
        if not check_markers:
            return

        lb, rb, rt, lt = self._corners
        normal_vec = self._normal

        # Calculate cell center and size
        center = (lb + rb + rt + lt) / 4.0
        cell_width = float(np.linalg.norm(rb - lb))
        cell_height = float(np.linalg.norm(lt - lb))
        cell_size = min(cell_width, cell_height)

        # Normal vector for top face
        nx, ny, nz = float(normal_vec[0]), float(normal_vec[1]), float(normal_vec[2])

        for marker in check_markers:
            # Get marker color (green by default)
            if marker.color is not None:
                r, g, b = marker.color
            else:
                r, g, b = 0.0, 0.8, 0.0  # Default green

            # Plus sign dimensions (75% of original size)
            outer_radius = cell_size * 0.3 * marker.radius_factor  # Total extent
            stroke_half_width = cell_size * 0.06 * marker.thickness  # Stroke thickness
            height = marker.height_offset * cell_size  # Extrusion height

            # Use the same _generate_3d_ring method as ring markers for consistent style
            # Draw two perpendicular bars that form the + shape

            # The + is made of two overlapping rectangles:
            # - Horizontal bar (wide, short)
            # - Vertical bar (narrow, tall)
            # We'll generate them as separate 3D boxes

            def add_box(
                half_w: float, half_h: float,  # Half-width and half-height in cell plane
                box_height: float,  # Height above surface
            ) -> None:
                """Add a 3D box centered at the cell center."""
                # Get the cell's right and up vectors
                right_vec = (rb - lb)
                up_vec_local = (lt - lb)
                right_unit = right_vec / np.linalg.norm(right_vec)
                up_unit = up_vec_local / np.linalg.norm(up_vec_local)

                # Four corners of top face
                t0 = center + right_unit * (-half_w) + up_unit * (-half_h) + normal_vec * box_height
                t1 = center + right_unit * (half_w) + up_unit * (-half_h) + normal_vec * box_height
                t2 = center + right_unit * (half_w) + up_unit * (half_h) + normal_vec * box_height
                t3 = center + right_unit * (-half_w) + up_unit * (half_h) + normal_vec * box_height

                # Four corners of bottom face (at surface)
                b0 = center + right_unit * (-half_w) + up_unit * (-half_h) + normal_vec * 0.001
                b1 = center + right_unit * (half_w) + up_unit * (-half_h) + normal_vec * 0.001
                b2 = center + right_unit * (half_w) + up_unit * (half_h) + normal_vec * 0.001
                b3 = center + right_unit * (-half_w) + up_unit * (half_h) + normal_vec * 0.001

                # Top face (2 triangles, normal pointing up)
                dest.extend([t0[0], t0[1], t0[2], nx, ny, nz, r, g, b])
                dest.extend([t1[0], t1[1], t1[2], nx, ny, nz, r, g, b])
                dest.extend([t2[0], t2[1], t2[2], nx, ny, nz, r, g, b])
                dest.extend([t0[0], t0[1], t0[2], nx, ny, nz, r, g, b])
                dest.extend([t2[0], t2[1], t2[2], nx, ny, nz, r, g, b])
                dest.extend([t3[0], t3[1], t3[2], nx, ny, nz, r, g, b])

                # Four side walls
                walls = [
                    (t0, t1, b1, b0, right_unit * 0 - up_unit),   # Bottom wall
                    (t1, t2, b2, b1, right_unit),                  # Right wall
                    (t2, t3, b3, b2, up_unit),                     # Top wall
                    (t3, t0, b0, b3, -right_unit),                 # Left wall
                ]
                for wt0, wt1, wb1, wb0, wall_dir in walls:
                    # Wall normal (outward)
                    wn = wall_dir / np.linalg.norm(wall_dir) if np.linalg.norm(wall_dir) > 0.001 else normal_vec
                    wnx, wny, wnz = float(wn[0]), float(wn[1]), float(wn[2])

                    # Two triangles for the wall quad
                    dest.extend([wt0[0], wt0[1], wt0[2], wnx, wny, wnz, r, g, b])
                    dest.extend([wb0[0], wb0[1], wb0[2], wnx, wny, wnz, r, g, b])
                    dest.extend([wb1[0], wb1[1], wb1[2], wnx, wny, wnz, r, g, b])
                    dest.extend([wt0[0], wt0[1], wt0[2], wnx, wny, wnz, r, g, b])
                    dest.extend([wb1[0], wb1[1], wb1[2], wnx, wny, wnz, r, g, b])
                    dest.extend([wt1[0], wt1[1], wt1[2], wnx, wny, wnz, r, g, b])

            # Draw horizontal bar of the + (wide, short)
            add_box(outer_radius, stroke_half_width, height)

            # Draw vertical bar of the + (narrow, tall)
            add_box(stroke_half_width, outer_radius, height)

    def generate_bold_cross_vertices(self, dest: list[float], markers: list[MarkerCreator] | None = None) -> None:
        """Generate triangle vertices for bold cross (X) markers.

        Creates a thick X shape using capsules (like checkmark but X shape).
        Used for at-risk markers to warn about pieces that may be destroyed.

        Appends triangles to dest.
        Each vertex: x, y, z, nx, ny, nz, r, g, b (9 floats)

        Args:
            dest: List to append vertex data to
            markers: Optional pre-fetched markers list (avoids repeated lookups)
        """
        if markers is None:
            markers = self.get_markers()
        if not markers:
            return

        # Find bold cross markers
        cross_markers = [m for m in markers if isinstance(m, MarkerConfig) and m.shape == MarkerShape.BOLD_CROSS]
        if not cross_markers:
            return

        lb, rb, rt, lt = self._corners
        normal_vec = self._normal

        # Calculate cell center and edge vectors
        center = (lb + rb + rt + lt) / 4.0
        right_vec = (rb - lb) / 2.0  # Half-width vector pointing right
        up_vec = (lt - lb) / 2.0     # Half-height vector pointing up

        # Cell size for scaling
        cell_width = float(np.linalg.norm(rb - lb))
        cell_height = float(np.linalg.norm(lt - lb))
        cell_size = min(cell_width, cell_height)

        # Number of segments for rounded shapes
        segments = 12

        for marker in cross_markers:
            # Get marker color (red by default for at-risk)
            if marker.color is not None:
                r, g, b = marker.color
            else:
                r, g, b = 1.0, 0.2, 0.2  # Default red

            # Capsule radius (tube thickness) - bold strokes
            radius = marker.thickness * 0.14 * cell_size

            # Height above surface
            height_above = marker.height_offset * cell_size + radius * 0.5

            # X dimensions based on radius_factor
            scale = marker.radius_factor * 0.7

            # Four corners of the X (at center height)
            top_left = center + right_vec * (-0.4 * scale) + up_vec * (0.4 * scale) + normal_vec * height_above
            top_right = center + right_vec * (0.4 * scale) + up_vec * (0.4 * scale) + normal_vec * height_above
            bottom_left = center + right_vec * (-0.4 * scale) + up_vec * (-0.4 * scale) + normal_vec * height_above
            bottom_right = center + right_vec * (0.4 * scale) + up_vec * (-0.4 * scale) + normal_vec * height_above

            # Helper: Generate a capsule (cylinder with hemispherical ends) between two points
            def add_capsule(p1: ndarray, p2: ndarray, cap_radius: float) -> None:
                """Add a capsule shape between two 3D points."""
                direction = p2 - p1
                length = float(np.linalg.norm(direction))
                if length < 0.001:
                    return
                direction = direction / length

                # Create perpendicular vectors for the circular cross-section
                if abs(direction[0]) < 0.9:
                    up = np.array([1.0, 0.0, 0.0])
                else:
                    up = np.array([0.0, 1.0, 0.0])
                perp1 = np.cross(direction, up)
                perp1 = perp1 / np.linalg.norm(perp1)
                perp2 = np.cross(direction, perp1)

                # Generate cylinder body
                for i in range(segments):
                    angle1 = 2 * math.pi * i / segments
                    angle2 = 2 * math.pi * (i + 1) / segments

                    cos1, sin1 = math.cos(angle1), math.sin(angle1)
                    cos2, sin2 = math.cos(angle2), math.sin(angle2)

                    offset1 = (cos1 * perp1 + sin1 * perp2) * cap_radius
                    offset2 = (cos2 * perp1 + sin2 * perp2) * cap_radius

                    c1_p1 = p1 + offset1
                    c2_p1 = p1 + offset2
                    c1_p2 = p2 + offset1
                    c2_p2 = p2 + offset2

                    n1 = cos1 * perp1 + sin1 * perp2
                    n2 = cos2 * perp1 + sin2 * perp2

                    # Two triangles for the quad
                    dest.extend([c1_p1[0], c1_p1[1], c1_p1[2], n1[0], n1[1], n1[2], r, g, b])
                    dest.extend([c2_p1[0], c2_p1[1], c2_p1[2], n2[0], n2[1], n2[2], r, g, b])
                    dest.extend([c2_p2[0], c2_p2[1], c2_p2[2], n2[0], n2[1], n2[2], r, g, b])
                    dest.extend([c1_p1[0], c1_p1[1], c1_p1[2], n1[0], n1[1], n1[2], r, g, b])
                    dest.extend([c2_p2[0], c2_p2[1], c2_p2[2], n2[0], n2[1], n2[2], r, g, b])
                    dest.extend([c1_p2[0], c1_p2[1], c1_p2[2], n1[0], n1[1], n1[2], r, g, b])

                # Generate hemispherical end caps
                half_segments = segments // 2
                for end_point, end_dir in [(p1, -direction), (p2, direction)]:
                    for j in range(half_segments):
                        lat1 = math.pi / 2 * j / half_segments
                        lat2 = math.pi / 2 * (j + 1) / half_segments

                        cos_lat1, sin_lat1 = math.cos(lat1), math.sin(lat1)
                        cos_lat2, sin_lat2 = math.cos(lat2), math.sin(lat2)

                        for i in range(segments):
                            lon1 = 2 * math.pi * i / segments
                            lon2 = 2 * math.pi * (i + 1) / segments

                            cos_lon1, sin_lon1 = math.cos(lon1), math.sin(lon1)
                            cos_lon2, sin_lon2 = math.cos(lon2), math.sin(lon2)

                            def sphere_point(cos_lat: float, sin_lat: float, cos_lon: float, sin_lon: float) -> tuple[ndarray, ndarray]:
                                local_n = sin_lat * end_dir + cos_lat * (cos_lon * perp1 + sin_lon * perp2)
                                point = end_point + cap_radius * local_n
                                return point, local_n

                            p1_s, n1_s = sphere_point(cos_lat1, sin_lat1, cos_lon1, sin_lon1)
                            p2_s, n2_s = sphere_point(cos_lat1, sin_lat1, cos_lon2, sin_lon2)
                            p3_s, n3_s = sphere_point(cos_lat2, sin_lat2, cos_lon2, sin_lon2)
                            p4_s, n4_s = sphere_point(cos_lat2, sin_lat2, cos_lon1, sin_lon1)

                            dest.extend([p1_s[0], p1_s[1], p1_s[2], n1_s[0], n1_s[1], n1_s[2], r, g, b])
                            dest.extend([p2_s[0], p2_s[1], p2_s[2], n2_s[0], n2_s[1], n2_s[2], r, g, b])
                            dest.extend([p3_s[0], p3_s[1], p3_s[2], n3_s[0], n3_s[1], n3_s[2], r, g, b])

                            dest.extend([p1_s[0], p1_s[1], p1_s[2], n1_s[0], n1_s[1], n1_s[2], r, g, b])
                            dest.extend([p3_s[0], p3_s[1], p3_s[2], n3_s[0], n3_s[1], n3_s[2], r, g, b])
                            dest.extend([p4_s[0], p4_s[1], p4_s[2], n4_s[0], n4_s[1], n4_s[2], r, g, b])

            # Draw the two diagonal strokes of the X as capsules
            add_capsule(top_left, bottom_right, radius)    # \ stroke
            add_capsule(bottom_left, top_right, radius)    # / stroke

    def generate_character_line_vertices(self, dest: list[float], markers: list[MarkerCreator] | None = None) -> None:
        """Generate line vertices for character markers.

        Draws characters using line segments. Supports letters A-Z, digits 0-9,
        and some common symbols.

        Appends line vertices to dest.
        Each vertex: x, y, z, r, g, b (6 floats)

        Args:
            dest: List to append vertex data to
            markers: Optional pre-fetched markers list (avoids repeated lookups)
        """
        if markers is None:
            markers = self.get_markers()
        if not markers:
            return

        # Find character markers
        char_markers = [m for m in markers if isinstance(m, MarkerConfig) and m.shape == MarkerShape.CHARACTER]
        if not char_markers:
            return

        lb, rb, rt, lt = self._corners

        # Calculate cell center and edge vectors
        center = (lb + rb + rt + lt) / 4.0
        right_vec = (rb - lb) / 2.0  # Half-width vector pointing right
        up_vec = (lt - lb) / 2.0     # Half-height vector pointing up

        # Height offset to raise characters above face surface
        height_offset = self._normal * 0.15

        for marker in char_markers:
            if not marker.character:
                continue

            # Get marker color
            if marker.color is not None:
                r, g, b = marker.color
            else:
                r, g, b = 0.0, 0.0, 0.0

            char = marker.character[0].upper()  # Use first character only
            scale = marker.radius_factor * 0.6

            # Get line segments for this character
            segments = _get_char_segments(char)

            for x1, y1, x2, y2 in segments:
                # Convert normalized coords (-1 to 1) to 3D position
                p1 = center + right_vec * x1 * scale + up_vec * y1 * scale + height_offset
                p2 = center + right_vec * x2 * scale + up_vec * y2 * scale + height_offset

                dest.extend([p1[0], p1[1], p1[2], r, g, b])
                dest.extend([p2[0], p2[1], p2[2], r, g, b])

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
        return self.part_edge.moveable_attributes.get(CELL_TEXTURE_KEY)

    def get_markers(self) -> list[MarkerCreator]:
        """Get markers for this cell from all attribute dictionaries.

        Markers are visual annotations added by the solver during animation
        to highlight pieces being tracked:
        - attributes: fixed position markers
        - c_attributes: markers on moving pieces (follow the piece)
        - f_attributes: markers on fixed positions (stay in place)

        Returns:
            List of MarkerConfig objects, sorted by z_order.
        """
        if self.part_edge is None:
            return []

        return get_markers_from_part_edge(self.part_edge)

    def has_markers(self) -> bool:
        """Check if this cell has any markers.

        Returns:
            True if cell has markers to render.
        """
        return len(self.get_markers()) > 0

    def get_center_position(self) -> ndarray:
        """Get the 3D center position of this cell.

        Returns:
            3D position as numpy array [x, y, z].
        """
        lb, rb, rt, lt = self._corners
        return (lb + rb + rt + lt) / 4.0

    def get_normal(self) -> ndarray:
        """Get the face normal vector for this cell.

        Returns:
            Normal vector as numpy array [nx, ny, nz].
        """
        return self._normal.copy()

    def get_color(self) -> tuple[float, float, float]:
        """Get the face color of this cell.

        Returns:
            RGB tuple (0.0-1.0 range).
        """
        return self._color

    def get_tracker_color(self) -> Color | None:
        """Get the tracker anchor color if this cell is a tracked center.

        For even cubes (4x4, 6x6), the tracker system marks one center slice
        per face as an anchor. This method detects if this cell is such an
        anchor and returns the tracker's assigned color.

        Uses FacesTrackerHolder.get_tracked_edge_color() which is holder-agnostic
        (returns color from ANY holder that marked this edge).

        Returns:
            The Color enum of the tracker's assigned color, or None if not tracked.
        """
        if self.part_edge is None:
            return None

        return FacesTrackerHolder.get_tracked_edge_color(self.part_edge)

    def generate_marker_vertices(self, dest: list[float], line_dest: list[float] | None = None) -> None:
        """Generate triangle vertices for all marker shapes.

        Creates geometry for each marker on this cell using the toolkit pattern.
        Each marker's draw() method calls toolkit primitives, which generate
        the appropriate vertex data.

        Cross and character markers output to line_dest (if provided).
        All other markers output to dest (triangle vertices).

        Appends triangles to dest.
        Each vertex: x, y, z, nx, ny, nz, r, g, b (9 floats)

        Args:
            dest: List to append triangle vertex data to.
            line_dest: Optional list for line vertex data (cross/character markers).
        """
        markers = self.get_markers()
        if not markers:
            return

        toolkit = ModernGLCellToolkit(
            triangle_dest=dest,
            line_dest=line_dest,
            corners=self._corners,
            normal=self._normal,
            color=self._color,
        )

        for marker in markers:
            marker.draw(toolkit)

    def generate_tracker_indicator_vertices(self, dest: list[float]) -> None:
        """Generate triangle vertices for tracker anchor indicator.

        Creates a small filled circle showing the tracker's assigned color,
        with a black outline for visibility (especially for white on white).
        Only generated for cells that are tracked center slices (even cubes).

        The indicator uses the tracker's assigned color directly (not complementary)
        so the user can see which color "owns" this center piece.

        Appends triangles to dest.
        Each vertex: x, y, z, nx, ny, nz, r, g, b (9 floats)

        Args:
            dest: List to append vertex data to
        """
        tracker_color = self.get_tracker_color()
        if tracker_color is None:
            return

        # Get RGB for the tracker's assigned color (NOT complementary)
        from ._modern_gl_constants import COLOR_TO_RGB
        rgb = COLOR_TO_RGB.get(tracker_color, (1.0, 1.0, 1.0))

        # Calculate cell center and size
        lb, rb, rt, lt = self._corners
        center = (lb + rb + rt + lt) / 4.0

        # Cell size (use minimum of width/height for radius)
        width = float(np.linalg.norm(rb - lb))
        height = float(np.linalg.norm(lt - lb))
        cell_size = min(width, height)

        # Normal vector
        normal = (float(self._normal[0]), float(self._normal[1]), float(self._normal[2]))

        # Calculate indicator size (smaller than markers)
        inner_radius = cell_size * _TRACKER_INDICATOR_RADIUS_FACTOR
        indicator_height = cell_size * _TRACKER_INDICATOR_HEIGHT

        # Calculate outline dimensions
        outline_width = inner_radius * _TRACKER_INDICATOR_OUTLINE_WIDTH
        outer_radius = inner_radius + outline_width

        # First: Draw black outline ring (slightly larger, behind the colored circle)
        self._generate_3d_ring(
            dest,
            center,
            inner_radius=inner_radius,  # Ring starts at inner edge
            outer_radius=outer_radius,  # Ring extends to outer edge
            height=indicator_height,
            normal=normal,
            color=_TRACKER_INDICATOR_OUTLINE_COLOR,
        )

        # Second: Draw colored filled circle (on top of the outline)
        self._generate_3d_ring(
            dest,
            center,
            inner_radius=0.0,  # Filled circle
            outer_radius=inner_radius,  # Same size as outline's inner edge
            height=indicator_height,
            normal=normal,
            color=rgb,
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
