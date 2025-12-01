"""
Modern OpenGL renderer for pyglet2 backend.

This renderer uses OpenGL 3.3+ core profile with shaders and VBOs,
replacing the legacy immediate mode rendering.
"""
from __future__ import annotations

import ctypes
from typing import Sequence

import numpy as np
from pyglet import gl

from cube.presentation.gui.backends.pyglet2.shaders import ShaderProgram
from cube.presentation.gui.backends.pyglet2.matrix import (
    Mat4, identity, perspective, multiply, MatrixStack
)


# Solid color shader - position only, color from uniform
SOLID_VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec3 aPos;

uniform mat4 uMVP;

void main() {
    gl_Position = uMVP * vec4(aPos, 1.0);
}
"""

SOLID_FRAGMENT_SHADER = """
#version 330 core
uniform vec3 uColor;
out vec4 FragColor;

void main() {
    FragColor = vec4(uColor, 1.0);
}
"""


class ModernGLRenderer:
    """Modern OpenGL renderer using shaders and VBOs.

    This replaces the legacy PygletShapeRenderer for pyglet 2.0.
    """

    def __init__(self) -> None:
        self._shader: ShaderProgram | None = None
        self._initialized = False

        # Matrix stacks (emulate legacy GL)
        self._projection = MatrixStack()
        self._modelview = MatrixStack()

        # Current color (RGB, 0-255)
        self._color: tuple[int, int, int] = (255, 255, 255)

        # Reusable VBO/VAO for immediate-style drawing
        self._vao = ctypes.c_uint()
        self._vbo = ctypes.c_uint()

    def setup(self) -> None:
        """Initialize the renderer. Must be called after GL context exists."""
        if self._initialized:
            return

        # Create shader
        self._shader = ShaderProgram(SOLID_VERTEX_SHADER, SOLID_FRAGMENT_SHADER)

        # Create reusable VAO/VBO
        gl.glGenVertexArrays(1, ctypes.byref(self._vao))
        gl.glGenBuffers(1, ctypes.byref(self._vbo))

        # Set up VAO with position attribute
        gl.glBindVertexArray(self._vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)
        # Position at location 0, 3 floats
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 3 * 4, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glBindVertexArray(0)

        self._initialized = True

    def cleanup(self) -> None:
        """Clean up GL resources."""
        if self._shader:
            self._shader.delete()
            self._shader = None
        if self._vao.value:
            gl.glDeleteVertexArrays(1, ctypes.byref(self._vao))
        if self._vbo.value:
            gl.glDeleteBuffers(1, ctypes.byref(self._vbo))
        self._initialized = False

    # === Projection Setup ===

    def set_perspective(
        self,
        width: int,
        height: int,
        fov_y: float = 45.0,
        near: float = 0.1,
        far: float = 100.0
    ) -> None:
        """Set up perspective projection."""
        aspect = width / height if height > 0 else 1.0
        self._projection.load(perspective(fov_y, aspect, near, far))

    # === Matrix Stack Operations (emulate legacy GL) ===

    def push_matrix(self) -> None:
        """Push current modelview matrix onto stack."""
        self._modelview.push()

    def pop_matrix(self) -> None:
        """Pop modelview matrix from stack."""
        self._modelview.pop()

    def load_identity(self) -> None:
        """Load identity into modelview matrix."""
        self._modelview.load_identity()

    def translate(self, x: float, y: float, z: float) -> None:
        """Apply translation to modelview matrix."""
        self._modelview.translate(x, y, z)

    def rotate(self, angle: float, x: float, y: float, z: float) -> None:
        """Apply rotation around arbitrary axis.

        Note: For simplicity, only supports rotation around principal axes.
        """
        if x > 0.5:
            self._modelview.rotate_x(angle)
        elif y > 0.5:
            self._modelview.rotate_y(angle)
        elif z > 0.5:
            self._modelview.rotate_z(angle)

    def scale(self, x: float, y: float, z: float) -> None:
        """Apply scale to modelview matrix."""
        self._modelview.scale(x, y, z)

    # === Color ===

    def set_color(self, r: int, g: int, b: int) -> None:
        """Set current drawing color (0-255 RGB)."""
        self._color = (r, g, b)

    # === Drawing Methods ===

    def _get_mvp(self) -> Mat4:
        """Get combined Model-View-Projection matrix."""
        return multiply(self._projection.current, self._modelview.current)

    def _upload_and_draw(self, vertices: np.ndarray, mode: int) -> None:
        """Upload vertex data and draw.

        Args:
            vertices: Numpy array of float32 vertex data
            mode: GL draw mode (GL_LINES, GL_TRIANGLES, etc.)
        """
        if self._shader is None:
            return

        self._shader.use()

        # Set MVP matrix
        mvp = self._get_mvp()
        self._shader.set_uniform_matrix4('uMVP', mvp)

        # Set color (normalized to 0-1)
        r, g, b = self._color
        self._shader.set_uniform_3f('uColor', r / 255.0, g / 255.0, b / 255.0)

        # Upload vertex data
        gl.glBindVertexArray(self._vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            vertices.nbytes,
            vertices.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            gl.GL_DYNAMIC_DRAW
        )

        # Draw
        vertex_count = len(vertices) // 3
        gl.glDrawArrays(mode, 0, vertex_count)

        gl.glBindVertexArray(0)

    def line(
        self,
        start: tuple[float, float, float],
        end: tuple[float, float, float],
        width: float = 1.0
    ) -> None:
        """Draw a line.

        Args:
            start: Starting point (x, y, z)
            end: Ending point (x, y, z)
            width: Line width (may not be supported on all hardware)
        """
        gl.glLineWidth(width)
        vertices = np.array([*start, *end], dtype=np.float32)
        self._upload_and_draw(vertices, gl.GL_LINES)

    def triangle(
        self,
        v0: tuple[float, float, float],
        v1: tuple[float, float, float],
        v2: tuple[float, float, float]
    ) -> None:
        """Draw a filled triangle."""
        vertices = np.array([*v0, *v1, *v2], dtype=np.float32)
        self._upload_and_draw(vertices, gl.GL_TRIANGLES)

    def quad(
        self,
        vertices: Sequence[tuple[float, float, float]]
    ) -> None:
        """Draw a filled quad (4 vertices).

        Args:
            vertices: Four vertices in order (converted to 2 triangles)
        """
        if len(vertices) != 4:
            return
        v0, v1, v2, v3 = vertices
        # Convert to 2 triangles: (v0,v1,v2) and (v0,v2,v3)
        tri_verts = np.array([
            *v0, *v1, *v2,
            *v0, *v2, *v3
        ], dtype=np.float32)
        self._upload_and_draw(tri_verts, gl.GL_TRIANGLES)

    def draw_axis(self, length: float = 5.0) -> None:
        """Draw XYZ axis lines for debugging.

        X = Red, Y = Green, Z = Blue
        """
        origin = (0.0, 0.0, 0.0)

        # X axis - Red
        self.set_color(255, 0, 0)
        self.line(origin, (length, 0, 0), 2.0)

        # Y axis - Green
        self.set_color(0, 255, 0)
        self.line(origin, (0, length, 0), 2.0)

        # Z axis - Blue
        self.set_color(0, 0, 255)
        self.line(origin, (0, 0, length), 2.0)

        # Reset color
        self.set_color(255, 255, 255)

    def draw_cube(self, size: float = 50.0) -> None:
        """Draw a simple colored cube for testing.

        Standard Rubik's cube colors:
        - White on top (U)
        - Yellow on bottom (D)
        - Green on front (F)
        - Blue on back (B)
        - Red on right (R)
        - Orange on left (L)
        """
        s = size / 2  # half size

        # Define the 8 vertices of the cube
        # Front face vertices (z = +s)
        ftl = (-s, +s, +s)  # front top left
        ftr = (+s, +s, +s)  # front top right
        fbr = (+s, -s, +s)  # front bottom right
        fbl = (-s, -s, +s)  # front bottom left

        # Back face vertices (z = -s)
        btl = (-s, +s, -s)  # back top left
        btr = (+s, +s, -s)  # back top right
        bbr = (+s, -s, -s)  # back bottom right
        bbl = (-s, -s, -s)  # back bottom left

        # Front face - Green
        self.set_color(0, 155, 72)
        self.quad([fbl, fbr, ftr, ftl])

        # Back face - Blue
        self.set_color(0, 70, 173)
        self.quad([bbr, bbl, btl, btr])

        # Top face - White
        self.set_color(255, 255, 255)
        self.quad([ftl, ftr, btr, btl])

        # Bottom face - Yellow
        self.set_color(255, 213, 0)
        self.quad([bbl, bbr, fbr, fbl])

        # Right face - Red
        self.set_color(183, 18, 52)
        self.quad([fbr, bbr, btr, ftr])

        # Left face - Orange
        self.set_color(255, 88, 0)
        self.quad([bbl, fbl, ftl, btl])
