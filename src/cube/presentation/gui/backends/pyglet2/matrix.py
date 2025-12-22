"""
Matrix math utilities for modern OpenGL in pyglet2 backend.

Provides functions to create projection, view, and model matrices
for use with shaders. All matrices are 4x4 column-major (OpenGL convention).
"""
from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray

# Type alias for 4x4 matrix
Mat4 = NDArray[np.float32]


def identity() -> Mat4:
    """Create a 4x4 identity matrix."""
    return np.eye(4, dtype=np.float32)


def perspective(fov_y: float, aspect: float, near: float, far: float) -> Mat4:
    """Create a perspective projection matrix.

    Args:
        fov_y: Field of view in Y direction (degrees)
        aspect: Aspect ratio (width / height)
        near: Near clipping plane distance
        far: Far clipping plane distance

    Returns:
        4x4 perspective projection matrix
    """
    fov_rad = math.radians(fov_y)
    f = 1.0 / math.tan(fov_rad / 2.0)

    mat = np.zeros((4, 4), dtype=np.float32)
    mat[0, 0] = f / aspect
    mat[1, 1] = f
    mat[2, 2] = (far + near) / (near - far)
    mat[2, 3] = (2.0 * far * near) / (near - far)
    mat[3, 2] = -1.0

    return mat


def orthographic(
    left: float, right: float,
    bottom: float, top: float,
    near: float, far: float
) -> Mat4:
    """Create an orthographic projection matrix.

    Args:
        left, right: Left and right clipping planes
        bottom, top: Bottom and top clipping planes
        near, far: Near and far clipping planes

    Returns:
        4x4 orthographic projection matrix
    """
    mat = np.zeros((4, 4), dtype=np.float32)
    mat[0, 0] = 2.0 / (right - left)
    mat[1, 1] = 2.0 / (top - bottom)
    mat[2, 2] = -2.0 / (far - near)
    mat[0, 3] = -(right + left) / (right - left)
    mat[1, 3] = -(top + bottom) / (top - bottom)
    mat[2, 3] = -(far + near) / (far - near)
    mat[3, 3] = 1.0

    return mat


def translate(x: float, y: float, z: float) -> Mat4:
    """Create a translation matrix.

    Args:
        x, y, z: Translation amounts

    Returns:
        4x4 translation matrix
    """
    mat = np.eye(4, dtype=np.float32)
    mat[0, 3] = x
    mat[1, 3] = y
    mat[2, 3] = z
    return mat


def scale(x: float, y: float, z: float) -> Mat4:
    """Create a scale matrix.

    Args:
        x, y, z: Scale factors

    Returns:
        4x4 scale matrix
    """
    mat = np.eye(4, dtype=np.float32)
    mat[0, 0] = x
    mat[1, 1] = y
    mat[2, 2] = z
    return mat


def rotate_x(angle_deg: float) -> Mat4:
    """Create a rotation matrix around the X axis.

    Args:
        angle_deg: Rotation angle in degrees

    Returns:
        4x4 rotation matrix
    """
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)

    mat = np.eye(4, dtype=np.float32)
    mat[1, 1] = c
    mat[1, 2] = -s
    mat[2, 1] = s
    mat[2, 2] = c
    return mat


def rotate_y(angle_deg: float) -> Mat4:
    """Create a rotation matrix around the Y axis.

    Args:
        angle_deg: Rotation angle in degrees

    Returns:
        4x4 rotation matrix
    """
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)

    mat = np.eye(4, dtype=np.float32)
    mat[0, 0] = c
    mat[0, 2] = s
    mat[2, 0] = -s
    mat[2, 2] = c
    return mat


def rotate_z(angle_deg: float) -> Mat4:
    """Create a rotation matrix around the Z axis.

    Args:
        angle_deg: Rotation angle in degrees

    Returns:
        4x4 rotation matrix
    """
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)

    mat = np.eye(4, dtype=np.float32)
    mat[0, 0] = c
    mat[0, 1] = -s
    mat[1, 0] = s
    mat[1, 1] = c
    return mat


def look_at(
    eye: tuple[float, float, float],
    center: tuple[float, float, float],
    up: tuple[float, float, float]
) -> Mat4:
    """Create a look-at view matrix.

    Args:
        eye: Camera position
        center: Point to look at
        up: Up direction vector

    Returns:
        4x4 view matrix
    """
    eye_arr = np.array(eye, dtype=np.float32)
    center_arr = np.array(center, dtype=np.float32)
    up_arr = np.array(up, dtype=np.float32)

    # Calculate forward, right, and up vectors
    f = center_arr - eye_arr
    f = f / np.linalg.norm(f)

    s = np.cross(f, up_arr)
    s = s / np.linalg.norm(s)

    u = np.cross(s, f)

    mat = np.eye(4, dtype=np.float32)
    mat[0, 0:3] = s
    mat[1, 0:3] = u
    mat[2, 0:3] = -f
    mat[0, 3] = -np.dot(s, eye_arr)
    mat[1, 3] = -np.dot(u, eye_arr)
    mat[2, 3] = np.dot(f, eye_arr)

    return mat


def multiply(*matrices: Mat4) -> Mat4:
    """Multiply multiple matrices together.

    Args:
        *matrices: Matrices to multiply (left to right)

    Returns:
        Product of all matrices
    """
    result = matrices[0]
    for mat in matrices[1:]:
        result = np.matmul(result, mat)
    return result.astype(np.float32)


class MatrixStack:
    """Stack of 4x4 matrices for emulating legacy OpenGL push/pop.

    In legacy GL, you could push/pop matrices to save/restore state.
    This class provides similar functionality for modern GL.
    """

    def __init__(self) -> None:
        """Initialize with identity matrix."""
        self._stack: list[Mat4] = [identity()]

    @property
    def current(self) -> Mat4:
        """Get the current (top) matrix."""
        return self._stack[-1]

    def push(self) -> None:
        """Push a copy of the current matrix onto the stack."""
        self._stack.append(self._stack[-1].copy())

    def pop(self) -> None:
        """Pop the top matrix from the stack."""
        if len(self._stack) > 1:
            self._stack.pop()

    def load_identity(self) -> None:
        """Replace current matrix with identity."""
        self._stack[-1] = identity()

    def load(self, mat: Mat4) -> None:
        """Replace current matrix with given matrix."""
        self._stack[-1] = mat.copy()

    def mult(self, mat: Mat4) -> None:
        """Multiply current matrix by given matrix."""
        self._stack[-1] = multiply(self._stack[-1], mat)

    def translate(self, x: float, y: float, z: float) -> None:
        """Apply translation to current matrix."""
        self.mult(translate(x, y, z))

    def scale(self, x: float, y: float, z: float) -> None:
        """Apply scale to current matrix."""
        self.mult(scale(x, y, z))

    def rotate_x(self, angle_deg: float) -> None:
        """Apply rotation around X axis."""
        self.mult(rotate_x(angle_deg))

    def rotate_y(self, angle_deg: float) -> None:
        """Apply rotation around Y axis."""
        self.mult(rotate_y(angle_deg))

    def rotate_z(self, angle_deg: float) -> None:
        """Apply rotation around Z axis."""
        self.mult(rotate_z(angle_deg))
