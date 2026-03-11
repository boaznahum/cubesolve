"""
AbstractShapeRenderer - base class with no-op defaults for ShapeRenderer protocol.

Use this for partial implementations that only need a subset of ShapeRenderer methods.
"""
from __future__ import annotations

from typing import Sequence

from cube.presentation.gui.protocols.ShapeRenderer import ShapeRenderer
from cube.presentation.gui.types import Color3, Point3D, TextureHandle, TextureMap


class AbstractShapeRenderer(ShapeRenderer):
    """Abstract base class providing default no-op implementations for ShapeRenderer.

    Inherit from this class when you only need to implement a subset of
    ShapeRenderer methods. All methods have no-op defaults that do nothing.
    """

    def quad(self, vertices: Sequence[Point3D], color: Color3) -> None:
        """Render a filled quadrilateral. No-op default."""
        pass

    def quad_with_border(
        self,
        vertices: Sequence[Point3D],
        face_color: Color3,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Render a quadrilateral with colored border. No-op default."""
        pass

    def triangle(self, vertices: Sequence[Point3D], color: Color3) -> None:
        """Render a filled triangle. No-op default."""
        pass

    def line(self, p1: Point3D, p2: Point3D, width: float, color: Color3) -> None:
        """Render a line segment. No-op default."""
        pass

    def sphere(self, center: Point3D, radius: float, color: Color3) -> None:
        """Render a sphere. No-op default."""
        pass

    def cylinder(
        self,
        p1: Point3D,
        p2: Point3D,
        radius1: float,
        radius2: float,
        color: Color3,
    ) -> None:
        """Render a cylinder/cone. No-op default."""
        pass

    def disk(
        self,
        center: Point3D,
        normal: Point3D,
        inner_radius: float,
        outer_radius: float,
        color: Color3,
    ) -> None:
        """Render a disk. No-op default."""
        pass

    def lines(
        self,
        points: Sequence[tuple[Point3D, Point3D]],
        width: float,
        color: Color3,
    ) -> None:
        """Render multiple line segments. No-op default."""
        pass

    def quad_with_texture(
        self,
        vertices: Sequence[Point3D],
        color: Color3,
        texture: TextureHandle | None,
        texture_map: TextureMap | None,
    ) -> None:
        """Render a quadrilateral with optional texture. No-op default."""
        pass

    def cross(
        self,
        vertices: Sequence[Point3D],
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Render a cross (X) inside a quadrilateral. No-op default."""
        pass

    def lines_in_quad(
        self,
        vertices: Sequence[Point3D],
        n: int,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Render n evenly-spaced vertical lines inside a quadrilateral. No-op default."""
        pass

    def box_with_lines(
        self,
        bottom_quad: Sequence[Point3D],
        top_quad: Sequence[Point3D],
        face_color: Color3,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Render a 3D box with filled faces and line borders. No-op default."""
        pass

    def full_cylinder(
        self,
        p1: Point3D,
        p2: Point3D,
        outer_radius: float,
        inner_radius: float,
        color: Color3,
    ) -> None:
        """Render a hollow cylinder with capped ends. No-op default."""
        pass

    def set_sticker_context(self, face: str, row: int, col: int,
                            slice_index: int = -1,
                            sx: int = -1, sy: int = -1) -> None:
        """Set sticker metadata context. No-op default."""
        pass

    def clear_sticker_context(self) -> None:
        """Clear sticker metadata context. No-op default."""
        pass
