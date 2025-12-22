"""
ShapeRenderer protocol definition.

This protocol defines the interface for rendering geometric primitives.
"""

from typing import Protocol, Sequence, runtime_checkable

from cube.presentation.gui.types import Color3, Point3D, TextureHandle, TextureMap


@runtime_checkable
class ShapeRenderer(Protocol):
    """Protocol for rendering geometric primitives.

    Backends implement this to provide shape drawing capabilities.
    For 2D backends (like tkinter), 3D coordinates are projected to 2D.
    """

    def quad(self, vertices: Sequence[Point3D], color: Color3) -> None:
        """Render a filled quadrilateral.

        Args:
            vertices: 4 points in counter-clockwise order
            color: RGB fill color (0-255 per channel)
        """
        ...

    def quad_with_border(
        self,
        vertices: Sequence[Point3D],
        face_color: Color3,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Render a quadrilateral with colored border.

        Args:
            vertices: 4 points in counter-clockwise order
            face_color: RGB fill color
            line_width: Border line width in pixels
            line_color: RGB border color
        """
        ...

    def triangle(self, vertices: Sequence[Point3D], color: Color3) -> None:
        """Render a filled triangle.

        Args:
            vertices: 3 points in counter-clockwise order
            color: RGB fill color
        """
        ...

    def line(self, p1: Point3D, p2: Point3D, width: float, color: Color3) -> None:
        """Render a line segment.

        Args:
            p1: Start point
            p2: End point
            width: Line width in pixels
            color: RGB line color
        """
        ...

    def sphere(self, center: Point3D, radius: float, color: Color3) -> None:
        """Render a sphere (or circle in 2D backends).

        Args:
            center: Center point
            radius: Sphere radius
            color: RGB color
        """
        ...

    def cylinder(
        self,
        p1: Point3D,
        p2: Point3D,
        radius1: float,
        radius2: float,
        color: Color3,
    ) -> None:
        """Render a cylinder/cone between two points (or thick line in 2D).

        Args:
            p1: First end center point
            p2: Second end center point
            radius1: Radius at first end
            radius2: Radius at second end
            color: RGB color
        """
        ...

    def disk(
        self,
        center: Point3D,
        normal: Point3D,
        inner_radius: float,
        outer_radius: float,
        color: Color3,
    ) -> None:
        """Render a disk (annulus) perpendicular to a direction.

        Args:
            center: Center point of the disk
            normal: Normal vector (disk is perpendicular to this)
            inner_radius: Inner radius (0 for solid disk)
            outer_radius: Outer radius
            color: RGB color
        """
        ...

    def lines(
        self,
        points: Sequence[tuple[Point3D, Point3D]],
        width: float,
        color: Color3,
    ) -> None:
        """Render multiple line segments.

        Args:
            points: Sequence of (start, end) point pairs
            width: Line width in pixels
            color: RGB line color
        """
        ...

    def quad_with_texture(
        self,
        vertices: Sequence[Point3D],
        color: Color3,
        texture: TextureHandle | None,
        texture_map: TextureMap | None,
    ) -> None:
        """Render a quadrilateral with optional texture.

        Args:
            vertices: 4 points in counter-clockwise order
            color: RGB base color (modulates texture)
            texture: Texture handle from load_texture, or None for solid color
            texture_map: UV coordinates for each vertex, or None
        """
        ...

    def cross(
        self,
        vertices: Sequence[Point3D],
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Render a cross (X) inside a quadrilateral.

        Draws two diagonal lines from corner to corner.

        Args:
            vertices: 4 points [left_bottom, right_bottom, right_top, left_top]
            line_width: Line width in pixels
            line_color: RGB line color
        """
        ...

    def lines_in_quad(
        self,
        vertices: Sequence[Point3D],
        n: int,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Render n evenly-spaced vertical lines inside a quadrilateral.

        Args:
            vertices: 4 points [left_bottom, right_bottom, right_top, left_top]
            n: Number of lines to draw (0 for none)
            line_width: Line width in pixels
            line_color: RGB line color
        """
        ...

    def box_with_lines(
        self,
        bottom_quad: Sequence[Point3D],
        top_quad: Sequence[Point3D],
        face_color: Color3,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Render a 3D box with filled faces and line borders.

        Args:
            bottom_quad: 4 points [left_bottom, right_bottom, right_top, left_top] of bottom face
            top_quad: 4 points [left_bottom, right_bottom, right_top, left_top] of top face
            face_color: RGB fill color for faces
            line_width: Border line width in pixels
            line_color: RGB border color
        """
        ...

    def full_cylinder(
        self,
        p1: Point3D,
        p2: Point3D,
        outer_radius: float,
        inner_radius: float,
        color: Color3,
    ) -> None:
        """Render a hollow cylinder with capped ends (an annular prism).

        The cylinder is oriented along the p1-p2 axis.
        If inner_radius is 0, renders a solid cylinder with caps.

        Args:
            p1: First end center point
            p2: Second end center point
            outer_radius: Outer radius of the cylinder
            inner_radius: Inner radius (0 for solid cylinder)
            color: RGB color
        """
        ...
