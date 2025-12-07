"""
Modern OpenGL buffer utilities for pyglet2 backend.

Provides helper classes for managing VBOs (Vertex Buffer Objects) and
VAOs (Vertex Array Objects) in OpenGL 3.3+ core profile.
"""
from __future__ import annotations

import ctypes
from typing import Sequence

import numpy as np
from pyglet import gl


class VertexBuffer:
    """Wrapper for OpenGL Vertex Buffer Object (VBO).

    Stores vertex data (positions, colors, etc.) on the GPU.
    """

    def __init__(self) -> None:
        """Create a new VBO."""
        self._vbo = ctypes.c_uint()
        gl.glGenBuffers(1, ctypes.byref(self._vbo))

    @property
    def handle(self) -> int:
        """Get the OpenGL buffer handle."""
        return self._vbo.value

    def bind(self) -> None:
        """Bind this buffer for use."""
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)

    def unbind(self) -> None:
        """Unbind this buffer."""
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    def set_data(self, data: np.ndarray, usage: int = gl.GL_STATIC_DRAW) -> None:
        """Upload data to the buffer.

        Args:
            data: Numpy array of vertex data (float32)
            usage: GL_STATIC_DRAW, GL_DYNAMIC_DRAW, or GL_STREAM_DRAW
        """
        self.bind()
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            gl.GLsizeiptr(data.nbytes),
            data.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            usage
        )

    def delete(self) -> None:
        """Delete the buffer."""
        if self._vbo.value:
            gl.glDeleteBuffers(1, ctypes.byref(self._vbo))
            self._vbo.value = 0


class VertexArray:
    """Wrapper for OpenGL Vertex Array Object (VAO).

    Stores the vertex attribute configuration (how to interpret VBO data).
    """

    def __init__(self) -> None:
        """Create a new VAO."""
        self._vao = ctypes.c_uint()
        gl.glGenVertexArrays(1, ctypes.byref(self._vao))

    @property
    def handle(self) -> int:
        """Get the OpenGL VAO handle."""
        return self._vao.value

    def bind(self) -> None:
        """Bind this VAO for use."""
        gl.glBindVertexArray(self._vao)

    def unbind(self) -> None:
        """Unbind this VAO."""
        gl.glBindVertexArray(0)

    def set_attribute(
        self,
        index: int,
        size: int,
        stride: int,
        offset: int,
        gl_type: int = gl.GL_FLOAT,
        normalized: bool = False
    ) -> None:
        """Configure a vertex attribute.

        Args:
            index: Attribute location (matches shader layout)
            size: Number of components (1-4)
            stride: Bytes between consecutive vertices
            offset: Byte offset of this attribute within vertex
            gl_type: Data type (GL_FLOAT, GL_INT, etc.)
            normalized: Whether to normalize integer values
        """
        gl.glVertexAttribPointer(
            index, size, gl_type,
            gl.GL_TRUE if normalized else gl.GL_FALSE,
            stride,
            ctypes.c_void_p(offset)
        )
        gl.glEnableVertexAttribArray(index)

    def delete(self) -> None:
        """Delete the VAO."""
        if self._vao.value:
            gl.glDeleteVertexArrays(1, ctypes.byref(self._vao))
            self._vao.value = 0


class Mesh:
    """Combines a VBO and VAO for easy rendering.

    A mesh stores vertex data and knows how to draw itself.
    """

    def __init__(self) -> None:
        """Create a new mesh."""
        self._vbo = VertexBuffer()
        self._vao = VertexArray()
        self._vertex_count = 0

    @property
    def vertex_count(self) -> int:
        """Number of vertices in the mesh."""
        return self._vertex_count

    def setup_position_only(self, positions: Sequence[tuple[float, float, float]]) -> None:
        """Set up mesh with position data only.

        Args:
            positions: List of (x, y, z) vertex positions
        """
        # Convert to numpy array
        data = np.array(positions, dtype=np.float32).flatten()

        # Upload to VBO
        self._vbo.set_data(data)
        self._vertex_count = len(positions)

        # Configure VAO
        self._vao.bind()
        self._vbo.bind()
        # Position attribute at location 0, 3 floats, stride=12 bytes, offset=0
        self._vao.set_attribute(0, 3, 3 * 4, 0)
        self._vao.unbind()

    def setup_position_color(
        self,
        data: Sequence[tuple[float, float, float, float, float, float]]
    ) -> None:
        """Set up mesh with interleaved position and color data.

        Args:
            data: List of (x, y, z, r, g, b) per vertex
        """
        # Convert to numpy array
        arr = np.array(data, dtype=np.float32).flatten()

        # Upload to VBO
        self._vbo.set_data(arr)
        self._vertex_count = len(data)

        # Configure VAO
        self._vao.bind()
        self._vbo.bind()
        # Position attribute at location 0, 3 floats, stride=24 bytes, offset=0
        self._vao.set_attribute(0, 3, 6 * 4, 0)
        # Color attribute at location 1, 3 floats, stride=24 bytes, offset=12
        self._vao.set_attribute(1, 3, 6 * 4, 3 * 4)
        self._vao.unbind()

    def bind(self) -> None:
        """Bind the mesh's VAO for drawing."""
        self._vao.bind()

    def unbind(self) -> None:
        """Unbind the mesh's VAO."""
        self._vao.unbind()

    def draw(self, mode: int = gl.GL_TRIANGLES) -> None:
        """Draw the mesh.

        Args:
            mode: GL_TRIANGLES, GL_LINES, GL_POINTS, etc.
        """
        self._vao.bind()
        gl.glDrawArrays(mode, 0, self._vertex_count)

    def delete(self) -> None:
        """Delete the mesh and its buffers."""
        self._vao.delete()
        self._vbo.delete()


def create_line_mesh(
    start: tuple[float, float, float],
    end: tuple[float, float, float]
) -> Mesh:
    """Create a mesh for a single line.

    Args:
        start: Starting point (x, y, z)
        end: Ending point (x, y, z)

    Returns:
        Mesh configured for GL_LINES drawing
    """
    mesh = Mesh()
    mesh.setup_position_only([start, end])
    return mesh


def create_quad_mesh(
    vertices: Sequence[tuple[float, float, float]]
) -> Mesh:
    """Create a mesh for a quad (4 vertices -> 2 triangles).

    Args:
        vertices: Four vertices in order (v0, v1, v2, v3)
                  Will create triangles: (v0,v1,v2) and (v0,v2,v3)

    Returns:
        Mesh configured for GL_TRIANGLES drawing
    """
    if len(vertices) != 4:
        raise ValueError("Quad requires exactly 4 vertices")

    # Convert quad to two triangles
    v0, v1, v2, v3 = vertices
    triangle_vertices = [v0, v1, v2, v0, v2, v3]

    mesh = Mesh()
    mesh.setup_position_only(triangle_vertices)
    return mesh


def create_triangle_mesh(
    v0: tuple[float, float, float],
    v1: tuple[float, float, float],
    v2: tuple[float, float, float]
) -> Mesh:
    """Create a mesh for a single triangle.

    Args:
        v0, v1, v2: Triangle vertices

    Returns:
        Mesh configured for GL_TRIANGLES drawing
    """
    mesh = Mesh()
    mesh.setup_position_only([v0, v1, v2])
    return mesh
