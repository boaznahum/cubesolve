"""
Modern GL Arrow - 3D arrows for solver annotations.

This module generates 3D arrow geometry to visualize source-to-destination
movement during solver animations. Arrows consist of:
- Shaft: Cylinder connecting source to destination
- Head: 3D cone at the destination end

The arrows float above the cube surface and animate (grow) as the solver
progresses through each step.

Vertex Format: 9 floats per vertex (x, y, z, nx, ny, nz, r, g, b)
Same format as face triangles, compatible with Phong shader.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy import ndarray

from ._modern_gl_constants import (
    ARROW_COLOR,
    ARROW_HEAD_LENGTH,
    ARROW_HEAD_RADIUS,
    ARROW_HEIGHT_OFFSET,
    ARROW_SEGMENTS,
    ARROW_SHAFT_RADIUS,
)

if TYPE_CHECKING:
    from ._modern_gl_cell import ModernGLCell


@dataclass
class ArrowEndpoint:
    """Position data for arrow source or destination.

    Attributes:
        position: 3D world position of the cell center
        normal: Surface normal (for height offset direction)
        color: Face color (for complementary arrow color)
    """
    position: ndarray
    normal: ndarray
    color: tuple[float, float, float]


@dataclass
class Arrow3D:
    """A 3D arrow from source to destination.

    The arrow consists of a cylindrical shaft and a cone head.
    Animation progress controls the grow animation.

    Attributes:
        source: Starting point (piece being moved)
        destination: Target position
        color: Arrow color (from config, bright gold by default)
        animation_progress: 0.0 (invisible) to 1.0 (fully drawn)
        source_is_animated: True if source cell is being rotated
    """
    source: ArrowEndpoint
    destination: ArrowEndpoint
    color: tuple[float, float, float]
    animation_progress: float = 0.0
    source_is_animated: bool = False

    def generate_vertices(
        self,
        dest: list[float],
        source_transform: ndarray | None = None,
    ) -> None:
        """Generate arrow geometry vertices (shaft + head).

        Uses grow animation: shaft extends from source toward destination,
        cone head appears when animation is near complete.

        Args:
            dest: List to append vertex data to (9 floats per vertex)
            source_transform: Optional 4x4 transform matrix to apply to source position
                            (used when source piece is being animated/rotated)
        """
        if self.animation_progress < 0.01:
            return  # Not visible yet

        # Calculate offset positions (float above surface)
        src_base = self.source.position + self.source.normal * ARROW_HEIGHT_OFFSET

        # Apply transform to source if animated
        if source_transform is not None and self.source_is_animated:
            # Convert to homogeneous coordinates
            src_h = np.array([src_base[0], src_base[1], src_base[2], 1.0])
            src_transformed = source_transform @ src_h
            src_pos = src_transformed[:3]
        else:
            src_pos = src_base

        dst_pos = self.destination.position + self.destination.normal * ARROW_HEIGHT_OFFSET

        # Direction and length
        direction = dst_pos - src_pos
        length = float(np.linalg.norm(direction))
        if length < 0.001:
            return

        direction = direction / length

        # Animated length (grow from source)
        animated_length = length * self.animation_progress

        # Reserve space for cone head at the end
        shaft_length = max(0, animated_length - ARROW_HEAD_LENGTH * self.animation_progress)
        shaft_end = src_pos + direction * shaft_length

        # Generate shaft cylinder (if long enough)
        if shaft_length > 0.5:
            self._generate_cylinder(
                dest,
                src_pos,
                shaft_end,
                direction,
                ARROW_SHAFT_RADIUS,
            )

        # Generate cone head (fade in during last 20% of animation)
        head_alpha = min(1.0, (self.animation_progress - 0.8) / 0.2) if self.animation_progress > 0.8 else 0.0
        if head_alpha > 0.01:
            cone_base = shaft_end
            cone_tip = src_pos + direction * animated_length
            self._generate_cone(
                dest,
                cone_base,
                cone_tip,
                direction,
            )

    def _generate_cylinder(
        self,
        dest: list[float],
        start: ndarray,
        end: ndarray,
        direction: ndarray,
        radius: float,
    ) -> None:
        """Generate a cylinder from start to end.

        Args:
            dest: List to append vertex data to
            start: Start position (center)
            end: End position (center)
            direction: Unit direction vector along cylinder axis
            radius: Cylinder radius
        """
        r, g, b = self.color

        # Create perpendicular vectors for the circular cross-section
        if abs(direction[0]) < 0.9:
            up = np.array([1.0, 0.0, 0.0])
        else:
            up = np.array([0.0, 1.0, 0.0])

        tangent1 = np.cross(direction, up)
        tangent1 = tangent1 / np.linalg.norm(tangent1)
        tangent2 = np.cross(direction, tangent1)

        # Generate cylinder segments
        for i in range(ARROW_SEGMENTS):
            angle1 = 2 * math.pi * i / ARROW_SEGMENTS
            angle2 = 2 * math.pi * (i + 1) / ARROW_SEGMENTS

            cos1, sin1 = math.cos(angle1), math.sin(angle1)
            cos2, sin2 = math.cos(angle2), math.sin(angle2)

            # Direction vectors for this segment
            dir1 = cos1 * tangent1 + sin1 * tangent2
            dir2 = cos2 * tangent1 + sin2 * tangent2

            # Points on circle at start and end
            start1 = start + radius * dir1
            start2 = start + radius * dir2
            end1 = end + radius * dir1
            end2 = end + radius * dir2

            # Normal is outward from axis (averaged between two edge normals)
            norm_avg = (dir1 + dir2) / 2
            norm_avg = norm_avg / np.linalg.norm(norm_avg)
            nx, ny, nz = float(norm_avg[0]), float(norm_avg[1]), float(norm_avg[2])

            # Two triangles for this quad segment
            # Triangle 1: start1, end1, start2
            for p in [start1, end1, start2]:
                dest.extend([float(p[0]), float(p[1]), float(p[2]), nx, ny, nz, r, g, b])

            # Triangle 2: start2, end1, end2
            for p in [start2, end1, end2]:
                dest.extend([float(p[0]), float(p[1]), float(p[2]), nx, ny, nz, r, g, b])

    def _generate_cone(
        self,
        dest: list[float],
        base_center: ndarray,
        tip: ndarray,
        direction: ndarray,
    ) -> None:
        """Generate a cone from base_center to tip.

        Args:
            dest: List to append vertex data to
            base_center: Center of cone base
            tip: Tip of cone
            direction: Unit direction from base to tip
        """
        r, g, b = self.color

        # Create perpendicular vectors for the circular base
        if abs(direction[0]) < 0.9:
            up = np.array([1.0, 0.0, 0.0])
        else:
            up = np.array([0.0, 1.0, 0.0])

        tangent1 = np.cross(direction, up)
        tangent1 = tangent1 / np.linalg.norm(tangent1)
        tangent2 = np.cross(direction, tangent1)

        # Generate cone segments
        for i in range(ARROW_SEGMENTS):
            angle1 = 2 * math.pi * i / ARROW_SEGMENTS
            angle2 = 2 * math.pi * (i + 1) / ARROW_SEGMENTS

            cos1, sin1 = math.cos(angle1), math.sin(angle1)
            cos2, sin2 = math.cos(angle2), math.sin(angle2)

            # Points on base circle
            dir1 = cos1 * tangent1 + sin1 * tangent2
            dir2 = cos2 * tangent1 + sin2 * tangent2
            base1 = base_center + ARROW_HEAD_RADIUS * dir1
            base2 = base_center + ARROW_HEAD_RADIUS * dir2

            # Calculate cone surface normals
            # The normal points outward from the cone surface
            cone_height = float(np.linalg.norm(tip - base_center))
            if cone_height < 0.001:
                continue

            # Slant height for normal calculation
            slant_outward = dir1  # Outward component
            slant_along = direction * (ARROW_HEAD_RADIUS / cone_height)  # Along-axis component
            norm1 = slant_outward + slant_along
            norm1 = norm1 / np.linalg.norm(norm1)

            slant_outward2 = dir2
            norm2 = slant_outward2 + slant_along
            norm2 = norm2 / np.linalg.norm(norm2)

            # Average normal for the triangle
            norm_avg = (norm1 + norm2) / 2
            norm_avg = norm_avg / np.linalg.norm(norm_avg)
            nx, ny, nz = float(norm_avg[0]), float(norm_avg[1]), float(norm_avg[2])

            # Cone side triangle: base1, base2, tip
            for p in [base1, base2, tip]:
                dest.extend([float(p[0]), float(p[1]), float(p[2]), nx, ny, nz, r, g, b])

            # Base cap triangle (optional, for solid look)
            # Normal points backward (opposite to direction)
            bnx, bny, bnz = -float(direction[0]), -float(direction[1]), -float(direction[2])
            for p in [base_center, base2, base1]:
                dest.extend([float(p[0]), float(p[1]), float(p[2]), bnx, bny, bnz, r, g, b])


def create_arrows_from_markers(
    source_cells: list["ModernGLCell"],
    dest_cells: list["ModernGLCell"],
    animated_part_slices: "set | None" = None,
    arrow_color: tuple[float, float, float] | None = None,
) -> list[Arrow3D]:
    """Create Arrow3D objects from source and destination cells.

    Pairs up source cells (c_attributes markers) with destination cells
    (f_attributes markers) to create arrows.

    Note: The caller should check if arrows are enabled via ConfigProtocol
    before calling this function.

    Args:
        source_cells: Cells with c_attributes markers (moving pieces)
        dest_cells: Cells with f_attributes markers (target positions)
        animated_part_slices: Set of PartSlice objects currently being animated
        arrow_color: Optional arrow color from config (defaults to ARROW_COLOR constant)

    Returns:
        List of Arrow3D objects
    """
    color = arrow_color if arrow_color is not None else ARROW_COLOR

    arrows: list[Arrow3D] = []

    # Simple pairing: match source[i] with dest[i]
    # More sophisticated matching could use part_slice identity
    for i, src_cell in enumerate(source_cells):
        if i < len(dest_cells):
            dst_cell = dest_cells[i]

            # Check if source cell is part of animated geometry
            source_is_animated = (
                animated_part_slices is not None
                and src_cell.part_slice is not None
                and src_cell.part_slice in animated_part_slices
            )

            source_ep = ArrowEndpoint(
                position=src_cell.get_center_position(),
                normal=src_cell.get_normal(),
                color=src_cell.get_color(),
            )
            dest_ep = ArrowEndpoint(
                position=dst_cell.get_center_position(),
                normal=dst_cell.get_normal(),
                color=dst_cell.get_color(),
            )

            arrows.append(Arrow3D(
                source=source_ep,
                destination=dest_ep,
                color=color,  # Use color from config or default
                animation_progress=0.0,
                source_is_animated=source_is_animated,
            ))

    return arrows
