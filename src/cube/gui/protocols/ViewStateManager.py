"""
ViewStateManager protocol definition.

This protocol defines the interface for managing view transformations.
"""

from typing import Protocol, runtime_checkable

from cube.gui.types import Matrix4x4


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

    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float, float]:
        """Convert screen coordinates to world coordinates.

        Uses the current projection and modelview matrices along with
        depth buffer to unproject screen coordinates to 3D world space.

        Args:
            screen_x: X coordinate in screen/window space
            screen_y: Y coordinate in screen/window space (origin at bottom-left, OpenGL convention)

        Returns:
            Tuple of (world_x, world_y, world_z) coordinates
        """
        ...
