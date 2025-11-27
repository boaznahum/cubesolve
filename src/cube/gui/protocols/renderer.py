"""
Renderer protocol definitions.

These protocols define the interface for rendering geometric primitives,
managing display lists, and handling view transformations.
"""

from typing import Protocol, Sequence, runtime_checkable

from cube.gui.types import Point3D, Color3, Color4, DisplayList, Matrix4x4


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


@runtime_checkable
class DisplayListManager(Protocol):
    """Protocol for managing compiled display lists.

    Display lists are pre-compiled rendering commands that can be
    executed efficiently. For backends without native display list support
    (e.g., tkinter), this can store callable objects or canvas item IDs.
    """

    def create_list(self) -> DisplayList:
        """Create a new display list and return its handle.

        Returns:
            Opaque handle to the display list
        """
        ...

    def begin_compile(self, list_id: DisplayList) -> None:
        """Begin compiling rendering commands into the list.

        All subsequent rendering calls are recorded until end_compile().

        Args:
            list_id: Handle from create_list()
        """
        ...

    def end_compile(self) -> None:
        """End compilation and finalize the display list."""
        ...

    def call_list(self, list_id: DisplayList) -> None:
        """Execute a single display list.

        Args:
            list_id: Handle to execute
        """
        ...

    def call_lists(self, list_ids: Sequence[DisplayList]) -> None:
        """Execute multiple display lists in order.

        Args:
            list_ids: Sequence of handles to execute
        """
        ...

    def delete_list(self, list_id: DisplayList) -> None:
        """Delete a display list and free resources.

        Args:
            list_id: Handle to delete
        """
        ...

    def delete_lists(self, list_ids: Sequence[DisplayList]) -> None:
        """Delete multiple display lists.

        Args:
            list_ids: Sequence of handles to delete
        """
        ...


@runtime_checkable
class ViewStateManager(Protocol):
    """Protocol for managing view transformations.

    Handles projection setup, model-view matrix stack, and
    coordinate transformations. Based on OpenGL conventions
    but abstracted for other backends.
    """

    def set_projection(
        self, width: int, height: int, fov_y: float = 50.0, near: float = 0.1, far: float = 100.0
    ) -> None:
        """Set up projection matrix for the viewport.

        Args:
            width: Viewport width in pixels
            height: Viewport height in pixels
            fov_y: Vertical field of view in degrees (for 3D backends)
            near: Near clipping plane distance
            far: Far clipping plane distance
        """
        ...

    def push_matrix(self) -> None:
        """Save current model-view matrix to stack."""
        ...

    def pop_matrix(self) -> None:
        """Restore model-view matrix from stack."""
        ...

    def load_identity(self) -> None:
        """Reset model-view matrix to identity."""
        ...

    def translate(self, x: float, y: float, z: float) -> None:
        """Apply translation to current matrix.

        Args:
            x, y, z: Translation amounts
        """
        ...

    def rotate(self, angle_degrees: float, x: float, y: float, z: float) -> None:
        """Apply rotation around axis to current matrix.

        Args:
            angle_degrees: Rotation angle in degrees
            x, y, z: Axis of rotation (will be normalized)
        """
        ...

    def scale(self, x: float, y: float, z: float) -> None:
        """Apply scaling to current matrix.

        Args:
            x, y, z: Scale factors
        """
        ...

    def multiply_matrix(self, matrix: Matrix4x4) -> None:
        """Multiply current matrix by given 4x4 matrix.

        Args:
            matrix: 4x4 transformation matrix (column-major for OpenGL)
        """
        ...

    def look_at(
        self,
        eye_x: float,
        eye_y: float,
        eye_z: float,
        center_x: float,
        center_y: float,
        center_z: float,
        up_x: float,
        up_y: float,
        up_z: float,
    ) -> None:
        """Set up view matrix to look at a point.

        Args:
            eye_x, eye_y, eye_z: Camera position
            center_x, center_y, center_z: Look-at point
            up_x, up_y, up_z: Up vector
        """
        ...


@runtime_checkable
class Renderer(Protocol):
    """Main renderer protocol combining all rendering capabilities.

    This is the primary interface that backends implement. It provides
    access to shape rendering, display lists, and view transformations.
    """

    @property
    def shapes(self) -> ShapeRenderer:
        """Access shape rendering methods."""
        ...

    @property
    def display_lists(self) -> DisplayListManager:
        """Access display list management."""
        ...

    @property
    def view(self) -> ViewStateManager:
        """Access view transformation methods."""
        ...

    def clear(self, color: Color4 = (0, 0, 0, 255)) -> None:
        """Clear the rendering surface.

        Args:
            color: RGBA clear color (default: black)
        """
        ...

    def setup(self) -> None:
        """Initialize renderer (called once at startup).

        Sets up any required rendering state, contexts, etc.
        """
        ...

    def cleanup(self) -> None:
        """Release renderer resources (called at shutdown).

        Frees display lists, textures, and other resources.
        """
        ...

    def begin_frame(self) -> None:
        """Begin a new frame (called before drawing).

        Prepares for rendering a new frame.
        """
        ...

    def end_frame(self) -> None:
        """End frame and present (called after drawing).

        Finalizes rendering and presents the frame.
        """
        ...

    def flush(self) -> None:
        """Flush any pending rendering commands."""
        ...
