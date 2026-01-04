"""
Tkinter renderer implementation.

Provides 2D canvas-based rendering using isometric projection.
"""

from math import cos, radians, sin
from typing import Callable, Sequence

import numpy as np

from cube.presentation.gui.protocols import (
    DisplayListManager,
    Renderer,
    ShapeRenderer,
    ViewStateManager,
)
from cube.presentation.gui.types import (
    Color3,
    Color4,
    DisplayList,
    Matrix4x4,
    Point3D,
    TextureHandle,
    TextureMap,
)


class TkinterShapeRenderer(ShapeRenderer):
    """Tkinter Canvas implementation of ShapeRenderer protocol.

    Uses isometric projection to render 3D shapes on a 2D canvas.
    """

    def __init__(self, get_canvas: Callable, view_manager: "TkinterViewStateManager"):
        """Initialize shape renderer.

        Args:
            get_canvas: Callable that returns the tk.Canvas (deferred to avoid import issues)
            view_manager: View state manager for coordinate transformations
        """
        self._get_canvas = get_canvas
        self._view = view_manager
        self._items: list[int] = []  # Track canvas item IDs for clearing
        self._display_list_manager: "TkinterDisplayListManager | None" = None

    def set_display_list_manager(self, dlm: "TkinterDisplayListManager") -> None:
        """Set the display list manager for command capture."""
        self._display_list_manager = dlm

    def _project(self, point_3d: Point3D) -> tuple[float, float]:
        """Project 3D point to 2D canvas coordinates using current transformation."""
        return self._project_with_matrix(point_3d, self._view._current_matrix)

    def _project_with_matrix(self, point_3d: Point3D, matrix: np.ndarray) -> tuple[float, float]:
        """Project 3D point to 2D using given transformation matrix."""
        # Center the cube geometry first (spans 0-90, so center at 45)
        cube_center = 45.0
        centered = np.array([
            point_3d[0] - cube_center,
            point_3d[1] - cube_center,
            point_3d[2] - cube_center,
            1.0
        ])

        # Apply transformation matrix (rotation only - we extract just the rotation part)
        # The matrix may contain translations (like Z=-400 for perspective) that we ignore
        rotation_matrix = matrix.copy()
        rotation_matrix[0, 3] = 0  # Clear translation X
        rotation_matrix[1, 3] = 0  # Clear translation Y
        rotation_matrix[2, 3] = 0  # Clear translation Z

        transformed = rotation_matrix @ centered
        x, y, z = transformed[0], transformed[1], transformed[2]

        # Isometric formula: rotate 45° around Y, then ~35.264° around X
        # Simplified: x' = (x - z) * scale, y' = y - (x + z) * 0.5 * scale
        scale = self._view.scale_factor
        offset_x = self._view.offset_x
        offset_y = self._view.offset_y

        x_2d = (x - z) * 0.866 * scale + offset_x  # cos(30°) ≈ 0.866
        y_2d = offset_y - (y * scale - (x + z) * 0.5 * scale)  # Flip Y for screen coords

        return x_2d, y_2d

    def _project_points(self, vertices: Sequence[Point3D]) -> list[tuple[float, float]]:
        """Project list of 3D vertices to 2D."""
        return [self._project(v) for v in vertices]

    def _project_points_with_matrix(self, vertices: Sequence[Point3D], matrix: np.ndarray) -> list[tuple[float, float]]:
        """Project list of 3D vertices to 2D with given matrix."""
        return [self._project_with_matrix(v, matrix) for v in vertices]

    def _flatten_points(self, points_2d: list[tuple[float, float]]) -> list[float]:
        """Flatten [(x1,y1), (x2,y2), ...] to [x1, y1, x2, y2, ...]"""
        return [coord for point in points_2d for coord in point]

    def _rgb_to_hex(self, color: Color3) -> str:
        """Convert RGB tuple (0-255) to hex string."""
        r, g, b = color
        return f"#{r:02x}{g:02x}{b:02x}"

    def _add_item(self, item_id: int) -> None:
        """Track canvas item for later clearing."""
        self._items.append(item_id)

    def clear_items(self) -> None:
        """Clear all tracked canvas items."""
        canvas = self._get_canvas()
        if canvas:
            for item_id in self._items:
                canvas.delete(item_id)
        self._items.clear()

    def quad(self, vertices: Sequence[Point3D], color: Color3) -> None:
        """Render filled quadrilateral."""
        dlm = self._display_list_manager
        if dlm is not None and dlm.is_compiling():
            # Store vertices and color; matrix will be applied at call time
            dlm.add_command(
                lambda v=list(vertices), c=color: self._draw_quad(v, c, self._view._current_matrix)
            )
            return

        self._draw_quad(list(vertices), color, self._view._current_matrix)

    def _draw_quad(self, vertices: list[Point3D], color: Color3, matrix: np.ndarray) -> None:
        """Actually draw the quad with the given transformation matrix."""
        canvas = self._get_canvas()
        if not canvas:
            return

        points_2d = self._project_points_with_matrix(vertices, matrix)
        flat_coords = self._flatten_points(points_2d)
        hex_color = self._rgb_to_hex(color)

        item_id = canvas.create_polygon(*flat_coords, fill=hex_color, outline="")
        self._add_item(item_id)

    def quad_with_border(
        self,
        vertices: Sequence[Point3D],
        face_color: Color3,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Render quad with colored border."""
        dlm = self._display_list_manager
        if dlm is not None and dlm.is_compiling():
            # Store vertices and colors; matrix will be applied at call time
            dlm.add_command(
                lambda v=list(vertices), fc=face_color, lw=line_width, lc=line_color:
                    self._draw_quad_with_border(v, fc, lw, lc, self._view._current_matrix)
            )
            return

        self._draw_quad_with_border(list(vertices), face_color, line_width, line_color, self._view._current_matrix)

    def _draw_quad_with_border(
        self, vertices: list[Point3D], face_color: Color3, line_width: float, line_color: Color3, matrix: np.ndarray
    ) -> None:
        """Actually draw the quad with border."""
        canvas = self._get_canvas()
        if not canvas:
            return

        points_2d = self._project_points_with_matrix(vertices, matrix)
        flat_coords = self._flatten_points(points_2d)
        hex_face = self._rgb_to_hex(face_color)
        hex_line = self._rgb_to_hex(line_color)

        item_id = canvas.create_polygon(
            *flat_coords,
            fill=hex_face,
            outline=hex_line,
            width=max(1, int(line_width))
        )
        self._add_item(item_id)

    def triangle(self, vertices: Sequence[Point3D], color: Color3) -> None:
        """Render filled triangle."""
        dlm = self._display_list_manager
        if dlm is not None and dlm.is_compiling():
            dlm.add_command(
                lambda v=list(vertices), c=color: self._draw_triangle(v, c, self._view._current_matrix)
            )
            return

        self._draw_triangle(list(vertices), color, self._view._current_matrix)

    def _draw_triangle(self, vertices: list[Point3D], color: Color3, matrix: np.ndarray) -> None:
        """Actually draw the triangle."""
        canvas = self._get_canvas()
        if not canvas:
            return

        points_2d = self._project_points_with_matrix(vertices, matrix)
        flat_coords = self._flatten_points(points_2d)
        hex_color = self._rgb_to_hex(color)

        item_id = canvas.create_polygon(*flat_coords, fill=hex_color, outline="")
        self._add_item(item_id)

    def line(self, p1: Point3D, p2: Point3D, width: float, color: Color3) -> None:
        """Render a line segment."""
        dlm = self._display_list_manager
        if dlm is not None and dlm.is_compiling():
            dlm.add_command(
                lambda pt1=p1, pt2=p2, w=width, c=color: self._draw_line(pt1, pt2, w, c, self._view._current_matrix)
            )
            return

        self._draw_line(p1, p2, width, color, self._view._current_matrix)

    def _draw_line(self, p1: Point3D, p2: Point3D, width: float, color: Color3, matrix: np.ndarray) -> None:
        """Actually draw the line."""
        canvas = self._get_canvas()
        if not canvas:
            return

        x1, y1 = self._project_with_matrix(p1, matrix)
        x2, y2 = self._project_with_matrix(p2, matrix)
        hex_color = self._rgb_to_hex(color)

        item_id = canvas.create_line(x1, y1, x2, y2, fill=hex_color, width=max(1, int(width)))
        self._add_item(item_id)

    def sphere(self, center: Point3D, radius: float, color: Color3) -> None:
        """Render a sphere as a circle."""
        dlm = self._display_list_manager
        current_scale = self._view.scale_factor
        if dlm is not None and dlm.is_compiling():
            dlm.add_command(
                lambda c=center, r=radius, col=color, s=current_scale: self._draw_sphere(c, r, col, self._view._current_matrix, s)
            )
            return

        self._draw_sphere(center, radius, color, self._view._current_matrix, current_scale)

    def _draw_sphere(self, center: Point3D, radius: float, color: Color3, matrix: np.ndarray, scale: float) -> None:
        """Actually draw the sphere."""
        canvas = self._get_canvas()
        if not canvas:
            return

        cx, cy = self._project_with_matrix(center, matrix)
        r = radius * scale * 0.7
        hex_color = self._rgb_to_hex(color)

        item_id = canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=hex_color, outline="black")
        self._add_item(item_id)

    def cylinder(
        self,
        p1: Point3D,
        p2: Point3D,
        radius1: float,
        radius2: float,
        color: Color3,
    ) -> None:
        """Render cylinder as a thick line (simplified 2D representation)."""
        dlm = self._display_list_manager
        current_scale = self._view.scale_factor
        if dlm is not None and dlm.is_compiling():
            dlm.add_command(
                lambda pt1=p1, pt2=p2, r1=radius1, r2=radius2, c=color, s=current_scale:
                    self._draw_cylinder(pt1, pt2, r1, r2, c, self._view._current_matrix, s)
            )
            return

        self._draw_cylinder(p1, p2, radius1, radius2, color, self._view._current_matrix, current_scale)

    def _draw_cylinder(
        self, p1: Point3D, p2: Point3D, radius1: float, radius2: float, color: Color3, matrix: np.ndarray, scale: float
    ) -> None:
        """Actually draw the cylinder."""
        canvas = self._get_canvas()
        if not canvas:
            return

        x1, y1 = self._project_with_matrix(p1, matrix)
        x2, y2 = self._project_with_matrix(p2, matrix)
        hex_color = self._rgb_to_hex(color)

        avg_radius = (radius1 + radius2) / 2
        width = max(2, int(avg_radius * scale * 0.5))

        item_id = canvas.create_line(x1, y1, x2, y2, fill=hex_color, width=width)
        self._add_item(item_id)

    def disk(
        self,
        center: Point3D,
        normal: Point3D,
        inner_radius: float,
        outer_radius: float,
        color: Color3,
    ) -> None:
        """Render disk as an ellipse (simplified)."""
        dlm = self._display_list_manager
        current_scale = self._view.scale_factor
        if dlm is not None and dlm.is_compiling():
            dlm.add_command(
                lambda c=center, n=normal, ri=inner_radius, ro=outer_radius, col=color, s=current_scale:
                    self._draw_disk(c, n, ri, ro, col, self._view._current_matrix, s)
            )
            return

        self._draw_disk(center, normal, inner_radius, outer_radius, color, self._view._current_matrix, current_scale)

    def _draw_disk(
        self, center: Point3D, normal: Point3D, inner_radius: float, outer_radius: float,
        color: Color3, matrix: np.ndarray, scale: float
    ) -> None:
        """Actually draw the disk."""
        canvas = self._get_canvas()
        if not canvas:
            return

        cx, cy = self._project_with_matrix(center, matrix)
        r_outer = outer_radius * scale * 0.7
        r_inner = inner_radius * scale * 0.7
        hex_color = self._rgb_to_hex(color)

        item_id = canvas.create_oval(
            cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer,
            fill=hex_color, outline="black"
        )
        self._add_item(item_id)

        if r_inner > 0:
            item_id = canvas.create_oval(
                cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner,
                fill="#d9d9d9", outline=""
            )
            self._add_item(item_id)

    def lines(
        self,
        points: Sequence[tuple[Point3D, Point3D]],
        width: float,
        color: Color3,
    ) -> None:
        """Render multiple line segments."""
        dlm = self._display_list_manager
        if dlm is not None and dlm.is_compiling():
            dlm.add_command(
                lambda pts=list(points), w=width, c=color: self._draw_lines(pts, w, c, self._view._current_matrix)
            )
            return

        self._draw_lines(list(points), width, color, self._view._current_matrix)

    def _draw_lines(
        self, points: list[tuple[Point3D, Point3D]], width: float, color: Color3, matrix: np.ndarray
    ) -> None:
        """Actually draw the lines."""
        canvas = self._get_canvas()
        if not canvas:
            return

        hex_color = self._rgb_to_hex(color)
        line_width = max(1, int(width))

        for p1, p2 in points:
            x1, y1 = self._project_with_matrix(p1, matrix)
            x2, y2 = self._project_with_matrix(p2, matrix)
            item_id = canvas.create_line(x1, y1, x2, y2, fill=hex_color, width=line_width)
            self._add_item(item_id)

    def quad_with_texture(
        self,
        vertices: Sequence[Point3D],
        color: Color3,
        texture: TextureHandle | None,
        texture_map: TextureMap | None,
    ) -> None:
        """Render quad with texture (falls back to solid color in Tkinter)."""
        # Tkinter doesn't support textures easily, just draw solid color
        self.quad(vertices, color)

    def cross(
        self,
        vertices: Sequence[Point3D],
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Render a cross (X) inside a quadrilateral."""
        dlm = self._display_list_manager
        if dlm is not None and dlm.is_compiling():
            dlm.add_command(
                lambda v=list(vertices), lw=line_width, lc=line_color: self._draw_cross(v, lw, lc, self._view._current_matrix)
            )
            return

        self._draw_cross(list(vertices), line_width, line_color, self._view._current_matrix)

    def _draw_cross(self, vertices: list[Point3D], line_width: float, line_color: Color3, matrix: np.ndarray) -> None:
        """Actually draw the cross."""
        canvas = self._get_canvas()
        if not canvas:
            return

        points_2d = self._project_points_with_matrix(vertices, matrix)
        hex_color = self._rgb_to_hex(line_color)
        width = max(1, int(line_width))

        item_id = canvas.create_line(
            points_2d[0][0], points_2d[0][1],
            points_2d[2][0], points_2d[2][1],
            fill=hex_color, width=width
        )
        self._add_item(item_id)

        item_id = canvas.create_line(
            points_2d[1][0], points_2d[1][1],
            points_2d[3][0], points_2d[3][1],
            fill=hex_color, width=width
        )
        self._add_item(item_id)

    def lines_in_quad(
        self,
        vertices: Sequence[Point3D],
        n: int,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Render n evenly-spaced vertical lines inside a quadrilateral."""
        if n <= 0:
            return

        dlm = self._display_list_manager
        if dlm is not None and dlm.is_compiling():
            dlm.add_command(
                lambda v=list(vertices), num=n, lw=line_width, lc=line_color:
                    self._draw_lines_in_quad(v, num, lw, lc, self._view._current_matrix)
            )
            return

        self._draw_lines_in_quad(list(vertices), n, line_width, line_color, self._view._current_matrix)

    def _draw_lines_in_quad(
        self, vertices: list[Point3D], n: int, line_width: float, line_color: Color3, matrix: np.ndarray
    ) -> None:
        """Actually draw lines in quad."""
        canvas = self._get_canvas()
        if not canvas:
            return

        lb = np.array(vertices[0], dtype=float)
        rb = np.array(vertices[1], dtype=float)
        lt = np.array(vertices[3], dtype=float)
        rt = np.array(vertices[2], dtype=float)

        dx_bottom = (rb - lb) / (n + 1)
        dx_top = (rt - lt) / (n + 1)

        hex_color = self._rgb_to_hex(line_color)
        width = max(1, int(line_width))

        for i in range(n):
            p_bottom = lb + dx_bottom * (i + 1)
            p_top = lt + dx_top * (i + 1)

            x1, y1 = self._project_with_matrix(p_bottom, matrix)
            x2, y2 = self._project_with_matrix(p_top, matrix)

            item_id = canvas.create_line(x1, y1, x2, y2, fill=hex_color, width=width)
            self._add_item(item_id)

    def box_with_lines(
        self,
        bottom_quad: Sequence[Point3D],
        top_quad: Sequence[Point3D],
        face_color: Color3,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Render a 3D box with filled faces and line borders."""
        # This method delegates to quad_with_border which handles compile mode
        lb, rb, rt, lt = 0, 1, 2, 3

        # Back face
        self.quad_with_border(
            [bottom_quad[rb], bottom_quad[rt], top_quad[rt], top_quad[rb]],
            face_color, line_width, line_color
        )
        # Left face
        self.quad_with_border(
            [bottom_quad[lt], bottom_quad[rt], top_quad[rt], top_quad[lt]],
            face_color, line_width, line_color
        )
        # Bottom face
        self.quad_with_border(list(bottom_quad), face_color, line_width, line_color)
        # Top face
        self.quad_with_border(list(top_quad), face_color, line_width, line_color)
        # Front face
        self.quad_with_border(
            [bottom_quad[lb], bottom_quad[rb], top_quad[rb], top_quad[lb]],
            face_color, line_width, line_color
        )
        # Right face
        self.quad_with_border(
            [bottom_quad[lb], bottom_quad[lt], top_quad[lt], top_quad[lb]],
            face_color, line_width, line_color
        )

    def full_cylinder(
        self,
        p1: Point3D,
        p2: Point3D,
        outer_radius: float,
        inner_radius: float,
        color: Color3,
    ) -> None:
        """Render hollow cylinder (simplified as thick line)."""
        # Delegates to cylinder which handles compile mode
        self.cylinder(p1, p2, outer_radius, outer_radius, color)


class TkinterDisplayListManager(DisplayListManager):
    """Display list manager that stores rendering commands for replay.

    Since Tkinter Canvas doesn't have native display lists, we store
    callable commands that can be replayed.
    """

    def __init__(self, shape_renderer: TkinterShapeRenderer):
        self._shapes = shape_renderer
        self._next_id = 1
        self._lists: dict[int, list[Callable]] = {}
        self._compiling: int | None = None
        self._current_commands: list[Callable] = []

    def create_list(self) -> DisplayList:
        """Create a new display list."""
        list_id = DisplayList(self._next_id)
        self._next_id += 1
        self._lists[list_id] = []
        return list_id

    def begin_compile(self, list_id: DisplayList) -> None:
        """Begin compiling commands into display list."""
        self._compiling = list_id
        self._current_commands = []

    def end_compile(self) -> None:
        """End compilation and store commands."""
        if self._compiling is not None:
            self._lists[self._compiling] = self._current_commands
            self._compiling = None
            self._current_commands = []

    def call_list(self, list_id: DisplayList) -> None:
        """Execute a display list by replaying stored commands."""
        if list_id in self._lists:
            for cmd in self._lists[list_id]:
                cmd()

    def call_lists(self, list_ids: Sequence[DisplayList]) -> None:
        """Execute multiple display lists."""
        for list_id in list_ids:
            self.call_list(list_id)

    def delete_list(self, list_id: DisplayList) -> None:
        """Delete a display list."""
        if list_id in self._lists:
            del self._lists[list_id]

    def delete_lists(self, list_ids: Sequence[DisplayList]) -> None:
        """Delete multiple display lists."""
        for list_id in list_ids:
            self.delete_list(list_id)

    def is_compiling(self) -> bool:
        """Check if currently compiling a display list."""
        return self._compiling is not None

    def add_command(self, cmd: Callable) -> None:
        """Add a command during compilation."""
        if self._compiling is not None:
            self._current_commands.append(cmd)


class TkinterViewStateManager(ViewStateManager):
    """View state manager with matrix stack for transformations.

    Handles 3D transformations and provides isometric projection parameters.
    """

    def __init__(self) -> None:
        self._matrix_stack: list[np.ndarray] = []
        self._current_matrix = np.eye(4)
        self._width = 720
        self._height = 720
        self._scale_factor = 25.0  # Scale factor for isometric projection
        self.offset_x = 360.0  # Center X offset
        self.offset_y = 360.0  # Center Y offset

    @property
    def scale_factor(self) -> float:
        """Get the scale factor for isometric projection."""
        return self._scale_factor

    @scale_factor.setter
    def scale_factor(self, value: float) -> None:
        """Set the scale factor for isometric projection."""
        self._scale_factor = value

    def set_projection(
        self,
        width: int,
        height: int,
        fov_y: float = 50.0,
        near: float = 0.1,
        far: float = 100.0,
    ) -> None:
        """Set up projection (store dimensions for centering)."""
        self._width = width
        self._height = height
        self.offset_x = width / 2
        self.offset_y = height / 2
        # Scale to fit cube (90 units) in window with margin
        # For isometric: max extent is roughly cube_size * 1.5 (diagonal)
        # We want this to fit in min(width, height) with some margin
        cube_size = 90  # The cube geometry spans 0-90
        self._scale_factor = min(width, height) * 0.4 / cube_size  # ~3.2 for 720px

    def push_matrix(self) -> None:
        """Save current matrix to stack."""
        self._matrix_stack.append(self._current_matrix.copy())

    def pop_matrix(self) -> None:
        """Restore matrix from stack."""
        if self._matrix_stack:
            self._current_matrix = self._matrix_stack.pop()

    def load_identity(self) -> None:
        """Reset to identity matrix."""
        self._current_matrix = np.eye(4)

    def translate(self, x: float, y: float, z: float) -> None:
        """Apply translation."""
        translation = np.eye(4)
        translation[0, 3] = x
        translation[1, 3] = y
        translation[2, 3] = z
        self._current_matrix = self._current_matrix @ translation

    def rotate(self, angle_degrees: float, x: float, y: float, z: float) -> None:
        """Apply rotation around axis."""
        angle = radians(angle_degrees)
        c = cos(angle)
        s = sin(angle)

        # Normalize axis
        length = (x * x + y * y + z * z) ** 0.5
        if length < 1e-6:
            return
        x, y, z = x / length, y / length, z / length

        # Rodrigues' rotation formula
        rotation = np.eye(4)
        rotation[0, 0] = c + x * x * (1 - c)
        rotation[0, 1] = x * y * (1 - c) - z * s
        rotation[0, 2] = x * z * (1 - c) + y * s
        rotation[1, 0] = y * x * (1 - c) + z * s
        rotation[1, 1] = c + y * y * (1 - c)
        rotation[1, 2] = y * z * (1 - c) - x * s
        rotation[2, 0] = z * x * (1 - c) - y * s
        rotation[2, 1] = z * y * (1 - c) + x * s
        rotation[2, 2] = c + z * z * (1 - c)

        self._current_matrix = self._current_matrix @ rotation

    def scale(self, x: float, y: float, z: float) -> None:
        """Apply scaling."""
        scale_matrix = np.eye(4)
        scale_matrix[0, 0] = x
        scale_matrix[1, 1] = y
        scale_matrix[2, 2] = z
        self._current_matrix = self._current_matrix @ scale_matrix

    def multiply_matrix(self, matrix: Matrix4x4) -> None:
        """Multiply current matrix by given 4x4 matrix."""
        self._current_matrix = self._current_matrix @ matrix

    def look_at(
        self,
        eye_x: float, eye_y: float, eye_z: float,
        center_x: float, center_y: float, center_z: float,
        up_x: float, up_y: float, up_z: float,
    ) -> None:
        """Set up view matrix (simplified for isometric)."""
        # For isometric projection, we don't need full look_at
        # Just store as reference if needed
        pass

    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float, float]:
        """Convert screen coordinates to world coordinates (approximate)."""
        # Inverse isometric projection (approximate, assumes z=0 plane)
        x_2d = screen_x - self.offset_x
        y_2d = self.offset_y - screen_y

        # Simplified inverse (assumes z ≈ x for isometric)
        # This is an approximation - proper unprojection would need depth info
        x = x_2d / (0.866 * self._scale_factor)
        y = y_2d / self._scale_factor
        z = 0.0

        return (x, y, z)

    def transform_point(self, point: Point3D) -> np.ndarray:
        """Transform a 3D point by current matrix."""
        p = np.array([point[0], point[1], point[2], 1.0])
        transformed = self._current_matrix @ p
        return transformed[:3]


class TkinterRenderer(Renderer):
    """Tkinter renderer using Canvas for 2D isometric display.

    This renderer provides a 2D representation of the 3D cube using
    isometric projection onto a Tkinter Canvas widget.
    """

    def __init__(self):
        self._canvas = None
        self._view = TkinterViewStateManager()
        self._shapes = TkinterShapeRenderer(lambda: self._canvas, self._view)
        self._display_lists = TkinterDisplayListManager(self._shapes)
        # Connect shape renderer to display list manager for compile-mode awareness
        self._shapes.set_display_list_manager(self._display_lists)
        self._initialized = False
        self._bg_color = "#d9d9d9"

    def set_canvas(self, canvas) -> None:
        """Set the canvas to render to (called by TkinterWindow)."""
        self._canvas = canvas

    @property
    def shapes(self) -> TkinterShapeRenderer:
        """Access shape rendering methods."""
        return self._shapes

    @property
    def display_lists(self) -> TkinterDisplayListManager:
        """Access display list management."""
        return self._display_lists

    @property
    def view(self) -> TkinterViewStateManager:
        """Access view state management."""
        return self._view

    def clear(self, color: Color4 = (0, 0, 0, 255)) -> None:
        """Clear the canvas."""
        if self._canvas:
            self._canvas.delete("all")
            # Set background color
            r, g, b, a = color
            self._bg_color = f"#{r:02x}{g:02x}{b:02x}"
            self._canvas.configure(bg=self._bg_color)

    def setup(self) -> None:
        """Initialize renderer."""
        self._initialized = True

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._canvas:
            self._canvas.delete("all")
        self._initialized = False

    def begin_frame(self) -> None:
        """Begin a new frame - clear previous items."""
        self._shapes.clear_items()

    def end_frame(self) -> None:
        """End frame - update canvas."""
        if self._canvas:
            self._canvas.update_idletasks()

    def flush(self) -> None:
        """Flush rendering commands."""
        if self._canvas:
            self._canvas.update_idletasks()

    def load_texture(self, file_path: str) -> TextureHandle | None:
        """Load texture (not supported in Tkinter backend)."""
        return None

    def bind_texture(self, texture: TextureHandle | None) -> None:
        """Bind texture (no-op in Tkinter backend)."""
        pass

    def delete_texture(self, texture: TextureHandle) -> None:
        """Delete texture (no-op in Tkinter backend)."""
        pass
