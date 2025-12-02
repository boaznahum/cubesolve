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

# Per-vertex color shader - position and color per vertex
VERTEX_COLOR_VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aColor;

uniform mat4 uMVP;

out vec3 vColor;

void main() {
    gl_Position = uMVP * vec4(aPos, 1.0);
    vColor = aColor;
}
"""

VERTEX_COLOR_FRAGMENT_SHADER = """
#version 330 core
in vec3 vColor;
out vec4 FragColor;

void main() {
    FragColor = vec4(vColor, 1.0);
}
"""

# Phong lighting shader with per-vertex color and normal
# Vertex data: position (3) + normal (3) + color (3) = 9 floats per vertex
PHONG_VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec3 aColor;

uniform mat4 uMVP;
uniform mat4 uModelView;
uniform mat3 uNormalMatrix;

out vec3 vColor;
out vec3 vNormal;
out vec3 vFragPos;

void main() {
    gl_Position = uMVP * vec4(aPos, 1.0);
    vColor = aColor;
    vNormal = uNormalMatrix * aNormal;
    vFragPos = vec3(uModelView * vec4(aPos, 1.0));
}
"""

PHONG_FRAGMENT_SHADER = """
#version 330 core
in vec3 vColor;
in vec3 vNormal;
in vec3 vFragPos;

uniform vec3 uLightPos;
uniform vec3 uLightColor;
uniform vec3 uAmbientColor;
uniform float uShininess;

out vec4 FragColor;

void main() {
    // Ambient
    vec3 ambient = uAmbientColor * vColor;

    // Diffuse
    vec3 norm = normalize(vNormal);
    vec3 lightDir = normalize(uLightPos - vFragPos);
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = diff * uLightColor * vColor;

    // Specular (Blinn-Phong)
    vec3 viewDir = normalize(-vFragPos);  // Camera at origin in view space
    vec3 halfwayDir = normalize(lightDir + viewDir);
    float spec = pow(max(dot(norm, halfwayDir), 0.0), uShininess);
    vec3 specular = spec * uLightColor * 0.3;  // Reduced specular intensity

    vec3 result = ambient + diffuse + specular;
    FragColor = vec4(result, 1.0);
}
"""


class ModernGLRenderer:
    """Modern OpenGL renderer using shaders and VBOs.

    This replaces the legacy PygletShapeRenderer for pyglet 2.0.
    """

    def __init__(self) -> None:
        self._shader: ShaderProgram | None = None
        self._vertex_color_shader: ShaderProgram | None = None
        self._phong_shader: ShaderProgram | None = None
        self._initialized = False

        # Matrix stacks (emulate legacy GL)
        self._projection = MatrixStack()
        self._modelview = MatrixStack()

        # Current color (RGB, 0-255)
        self._color: tuple[int, int, int] = (255, 255, 255)

        # Reusable VBO/VAO for immediate-style drawing (position only)
        self._vao = ctypes.c_uint()
        self._vbo = ctypes.c_uint()

        # VAO/VBO for vertex-colored drawing (position + color interleaved)
        self._vc_vao = ctypes.c_uint()
        self._vc_vbo = ctypes.c_uint()

        # VAO/VBO for lit drawing (position + normal + color interleaved)
        self._lit_vao: ctypes.c_uint = ctypes.c_uint()
        self._lit_vbo: ctypes.c_uint = ctypes.c_uint()

        # Lighting parameters - tuned to match legacy OpenGL appearance
        # TODO: G3 - Add keyboard controls to adjust these (brightness up/down)
        self._light_pos: tuple[float, float, float] = (150.0, 150.0, 300.0)
        self._light_color: tuple[float, float, float] = (1.0, 1.0, 1.0)
        self._ambient_color: tuple[float, float, float] = (0.65, 0.65, 0.65)
        self._shininess: float = 12.0

        # Cached line width range (queried once on first use)
        self._line_width_range: tuple[float, float] | None = None

    def _clamp_line_width(self, width: float) -> float:
        """Clamp line width to the range supported by the GPU.

        OpenGL 4.x core profile only supports line_width=1.0, while
        compatibility profiles may support wider lines.

        Args:
            width: Requested line width

        Returns:
            Clamped line width within supported range
        """
        if self._line_width_range is None:
            # Query supported range once
            range_buf = (ctypes.c_float * 2)()
            gl.glGetFloatv(gl.GL_ALIASED_LINE_WIDTH_RANGE, range_buf)
            self._line_width_range = (range_buf[0], range_buf[1])

        min_width, max_width = self._line_width_range
        return max(min_width, min(max_width, width))

    def setup(self) -> None:
        """Initialize the renderer. Must be called after GL context exists."""
        if self._initialized:
            return

        # Create shaders
        self._shader = ShaderProgram(SOLID_VERTEX_SHADER, SOLID_FRAGMENT_SHADER)
        self._vertex_color_shader = ShaderProgram(
            VERTEX_COLOR_VERTEX_SHADER, VERTEX_COLOR_FRAGMENT_SHADER
        )
        self._phong_shader = ShaderProgram(PHONG_VERTEX_SHADER, PHONG_FRAGMENT_SHADER)

        # Create reusable VAO/VBO for solid color
        gl.glGenVertexArrays(1, ctypes.byref(self._vao))
        gl.glGenBuffers(1, ctypes.byref(self._vbo))

        # Set up VAO with position attribute only
        gl.glBindVertexArray(self._vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)
        # Position at location 0, 3 floats
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 3 * 4, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glBindVertexArray(0)

        # Create VAO/VBO for vertex-colored drawing
        gl.glGenVertexArrays(1, ctypes.byref(self._vc_vao))
        gl.glGenBuffers(1, ctypes.byref(self._vc_vbo))

        # Set up VAO with position + color (interleaved: 3 pos + 3 color = 6 floats)
        gl.glBindVertexArray(self._vc_vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vc_vbo)
        stride = 6 * 4  # 6 floats * 4 bytes
        # Position at location 0
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        # Color at location 1
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(3 * 4))
        gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)

        # Create VAO/VBO for lit drawing (position + normal + color)
        gl.glGenVertexArrays(1, ctypes.byref(self._lit_vao))
        gl.glGenBuffers(1, ctypes.byref(self._lit_vbo))

        # Set up VAO with position + normal + color (9 floats per vertex)
        gl.glBindVertexArray(self._lit_vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._lit_vbo)
        lit_stride = 9 * 4  # 9 floats * 4 bytes
        # Position at location 0
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, lit_stride, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        # Normal at location 1
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, lit_stride, ctypes.c_void_p(3 * 4))
        gl.glEnableVertexAttribArray(1)
        # Color at location 2
        gl.glVertexAttribPointer(2, 3, gl.GL_FLOAT, gl.GL_FALSE, lit_stride, ctypes.c_void_p(6 * 4))
        gl.glEnableVertexAttribArray(2)
        gl.glBindVertexArray(0)

        self._initialized = True

    def cleanup(self) -> None:
        """Clean up GL resources."""
        if self._shader:
            self._shader.delete()
            self._shader = None
        if self._vertex_color_shader:
            self._vertex_color_shader.delete()
            self._vertex_color_shader = None
        if self._phong_shader:
            self._phong_shader.delete()
            self._phong_shader = None
        if self._vao.value:
            gl.glDeleteVertexArrays(1, ctypes.byref(self._vao))
        if self._vbo.value:
            gl.glDeleteBuffers(1, ctypes.byref(self._vbo))
        if self._vc_vao.value:
            gl.glDeleteVertexArrays(1, ctypes.byref(self._vc_vao))
        if self._vc_vbo.value:
            gl.glDeleteBuffers(1, ctypes.byref(self._vc_vbo))
        if self._lit_vao.value:
            gl.glDeleteVertexArrays(1, ctypes.byref(self._lit_vao))
        if self._lit_vbo.value:
            gl.glDeleteBuffers(1, ctypes.byref(self._lit_vbo))
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

    def multiply_matrix(self, matrix: np.ndarray) -> None:
        """Multiply current modelview matrix by the given matrix.

        Used by animation system to apply rotation transforms.

        Args:
            matrix: 4x4 matrix to multiply
        """
        self._modelview.mult(matrix.astype(np.float32))

    # === Color ===

    def set_color(self, r: int, g: int, b: int) -> None:
        """Set current drawing color (0-255 RGB)."""
        self._color = (r, g, b)

    # === Drawing Methods ===

    def _get_mvp(self) -> Mat4:
        """Get combined Model-View-Projection matrix."""
        return multiply(self._projection.current, self._modelview.current)

    def get_inverse_mvp(self) -> np.ndarray:
        """Get the inverse of the combined MVP matrix.

        Used for unprojecting screen coordinates to world space (ray casting).

        Returns:
            4x4 numpy array representing the inverse MVP matrix.
        """
        mvp = self._get_mvp()
        try:
            return np.linalg.inv(mvp)
        except np.linalg.LinAlgError:
            # Matrix not invertible - return identity
            return np.eye(4, dtype=np.float32)

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
            width: Line width (clamped to GPU-supported range)
        """
        gl.glLineWidth(self._clamp_line_width(width))
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

    def quad_with_border(
        self,
        vertices: Sequence[tuple[float, float, float]],
        face_color: tuple[int, int, int],
        line_width: float = 1.0,
        line_color: tuple[int, int, int] = (0, 0, 0),
    ) -> None:
        """Draw a filled quad with a border outline.

        Args:
            vertices: Four vertices in order [bottom-left, bottom-right, top-right, top-left]
            face_color: RGB color (0-255) for the face fill
            line_width: Width of the border lines
            line_color: RGB color (0-255) for the border
        """
        # Draw filled quad
        self.set_color(*face_color)
        self.quad(vertices)

        # Draw border as line loop
        self.set_color(*line_color)
        gl.glLineWidth(self._clamp_line_width(line_width))

        if len(vertices) != 4:
            return
        v0, v1, v2, v3 = vertices
        # Draw 4 lines: v0->v1, v1->v2, v2->v3, v3->v0
        lines = np.array([
            *v0, *v1,
            *v1, *v2,
            *v2, *v3,
            *v3, *v0
        ], dtype=np.float32)
        self._upload_and_draw(lines, gl.GL_LINES)

    def draw_colored_triangles(
        self,
        data: np.ndarray
    ) -> None:
        """Draw multiple triangles with per-vertex colors.

        Args:
            data: Numpy array of float32 with interleaved position and color:
                  [x, y, z, r, g, b, x, y, z, r, g, b, ...]
                  Colors are normalized (0.0-1.0)
        """
        if self._vertex_color_shader is None:
            return

        self._vertex_color_shader.use()

        # Set MVP matrix
        mvp = self._get_mvp()
        self._vertex_color_shader.set_uniform_matrix4('uMVP', mvp)

        # Upload vertex data and draw
        gl.glBindVertexArray(self._vc_vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vc_vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            data.nbytes,
            data.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            gl.GL_DYNAMIC_DRAW
        )

        # Each vertex has 6 floats (3 pos + 3 color)
        vertex_count = len(data) // 6
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, vertex_count)

        gl.glBindVertexArray(0)

    def draw_colored_lines(
        self,
        data: np.ndarray,
        line_width: float = 1.0
    ) -> None:
        """Draw multiple lines with per-vertex colors.

        Args:
            data: Numpy array of float32 with interleaved position and color
            line_width: Line width
        """
        if self._vertex_color_shader is None:
            return

        # Enable line anti-aliasing for smoother lines
        gl.glEnable(gl.GL_LINE_SMOOTH)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_NICEST)

        # Clamp line width to supported range (OpenGL 4.x core only supports 1.0)
        gl.glLineWidth(self._clamp_line_width(line_width))
        self._vertex_color_shader.use()

        # Set MVP matrix
        mvp = self._get_mvp()
        self._vertex_color_shader.set_uniform_matrix4('uMVP', mvp)

        # Upload vertex data and draw
        gl.glBindVertexArray(self._vc_vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vc_vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            data.nbytes,
            data.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            gl.GL_DYNAMIC_DRAW
        )

        vertex_count = len(data) // 6
        gl.glDrawArrays(gl.GL_LINES, 0, vertex_count)

        gl.glBindVertexArray(0)

        # Disable line anti-aliasing after drawing
        gl.glDisable(gl.GL_LINE_SMOOTH)

    def draw_lit_triangles(self, data: np.ndarray) -> None:
        """Draw triangles with Phong lighting.

        Args:
            data: Numpy array of float32 with interleaved position, normal, and color:
                  [x, y, z, nx, ny, nz, r, g, b, ...]
                  Colors are normalized (0.0-1.0), 9 floats per vertex
        """
        if self._phong_shader is None or len(data) == 0:
            return

        self._phong_shader.use()

        # Set matrices
        mvp = self._get_mvp()
        modelview = self._modelview.current

        # Normal matrix is inverse transpose of upper-left 3x3 of modelview
        normal_matrix = np.linalg.inv(modelview[:3, :3]).T.astype(np.float32)

        self._phong_shader.set_uniform_matrix4('uMVP', mvp)
        self._phong_shader.set_uniform_matrix4('uModelView', modelview)

        # Set normal matrix (3x3)
        loc = self._phong_shader.get_uniform('uNormalMatrix')
        if loc >= 0:
            gl.glUniformMatrix3fv(
                loc, 1, gl.GL_TRUE,
                normal_matrix.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            )

        # Set lighting uniforms
        self._phong_shader.set_uniform_3f('uLightPos', *self._light_pos)
        self._phong_shader.set_uniform_3f('uLightColor', *self._light_color)
        self._phong_shader.set_uniform_3f('uAmbientColor', *self._ambient_color)
        self._phong_shader.set_uniform_1f('uShininess', self._shininess)

        # Upload vertex data and draw
        gl.glBindVertexArray(self._lit_vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._lit_vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            data.nbytes,
            data.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            gl.GL_DYNAMIC_DRAW
        )

        # Each vertex has 9 floats (3 pos + 3 normal + 3 color)
        vertex_count = len(data) // 9
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, vertex_count)

        gl.glBindVertexArray(0)

    def set_light_position(self, x: float, y: float, z: float) -> None:
        """Set the light position in world space."""
        self._light_pos = (x, y, z)

    def set_light_color(self, r: float, g: float, b: float) -> None:
        """Set the light color (0.0-1.0)."""
        self._light_color = (r, g, b)

    def set_ambient_color(self, r: float, g: float, b: float) -> None:
        """Set the ambient light color (0.0-1.0)."""
        self._ambient_color = (r, g, b)

    def get_ambient_level(self) -> float:
        """Get the current ambient light level (average of RGB)."""
        return self._ambient_color[0]

    def adjust_ambient(self, delta: float) -> float:
        """Adjust the ambient light level.

        Args:
            delta: Amount to add (positive = brighter, negative = darker)

        Returns:
            New ambient level after clamping to [0.1, 1.5]
            Values > 1.0 create overbright lighting for better visibility.
        """
        new_level = max(0.1, min(1.5, self._ambient_color[0] + delta))
        self._ambient_color = (new_level, new_level, new_level)
        return new_level

    def get_shininess(self) -> float:
        """Get the current shininess value."""
        return self._shininess

    def set_shininess(self, value: float) -> None:
        """Set the shininess value (clamped to [1.0, 128.0])."""
        self._shininess = max(1.0, min(128.0, value))

    def adjust_shininess(self, delta: float) -> float:
        """Adjust the shininess value.

        Args:
            delta: Amount to add

        Returns:
            New shininess value after clamping to [1.0, 128.0]
        """
        self._shininess = max(1.0, min(128.0, self._shininess + delta))
        return self._shininess

    # === Picking / Unprojection ===

    def screen_to_world(
        self,
        screen_x: float,
        screen_y: float,
        window_width: int,
        window_height: int,
    ) -> tuple[float, float, float]:
        """Convert screen coordinates to world coordinates.

        Uses current projection and modelview matrices to unproject
        screen coordinates to 3D world space.

        Args:
            screen_x: Screen X coordinate (0 = left)
            screen_y: Screen Y coordinate (0 = bottom, OpenGL convention)
            window_width: Window width in pixels
            window_height: Window height in pixels

        Returns:
            Tuple of (world_x, world_y, world_z)
        """
        # Read depth at the pixel
        depth_buffer = (gl.GLfloat * 1)()
        gl.glReadPixels(
            int(screen_x), int(screen_y), 1, 1,
            gl.GL_DEPTH_COMPONENT, gl.GL_FLOAT, depth_buffer
        )
        depth = depth_buffer[0]

        # Convert screen coords to normalized device coordinates (NDC)
        # NDC range is [-1, 1] for x, y, z
        ndc_x = (2.0 * screen_x / window_width) - 1.0
        ndc_y = (2.0 * screen_y / window_height) - 1.0
        ndc_z = 2.0 * depth - 1.0

        # Get combined MVP matrix and its inverse
        mvp = self._get_mvp()
        try:
            inv_mvp = np.linalg.inv(mvp)
        except np.linalg.LinAlgError:
            # Matrix not invertible - return origin
            return (0.0, 0.0, 0.0)

        # Unproject: multiply NDC coords by inverse MVP
        clip_coords = np.array([ndc_x, ndc_y, ndc_z, 1.0], dtype=np.float32)
        world_coords = np.matmul(inv_mvp, clip_coords)

        # Perspective divide
        if abs(world_coords[3]) < 1e-10:
            return (0.0, 0.0, 0.0)

        world_coords /= world_coords[3]

        return (float(world_coords[0]), float(world_coords[1]), float(world_coords[2]))


class ModernGLViewStateManager:
    """ViewStateManager adapter that wraps ModernGLRenderer.

    This adapter implements the ViewStateManager protocol by delegating to
    ModernGLRenderer methods. Used by pyglet2 backend to provide modern GL
    compatible view state management (avoiding legacy gluPerspective etc.).

    Part of B4 fix: Zoom crash in pyglet2 backend.
    """

    def __init__(self, renderer: ModernGLRenderer, window_width: int = 800, window_height: int = 600):
        """Initialize the adapter.

        Args:
            renderer: The ModernGLRenderer to wrap
            window_width: Window width for screen_to_world
            window_height: Window height for screen_to_world
        """
        self._renderer = renderer
        self._window_width = window_width
        self._window_height = window_height

    def update_window_size(self, width: int, height: int) -> None:
        """Update window size (called on resize)."""
        self._window_width = width
        self._window_height = height

    def set_projection(
        self, width: int, height: int, fov_y: float = 50.0, near: float = 0.1, far: float = 100.0
    ) -> None:
        """Set up projection matrix for the viewport."""
        self._window_width = width
        self._window_height = height
        self._renderer.set_perspective(width, height, fov_y, near, far)

    def push_matrix(self) -> None:
        """Save current model-view matrix to stack."""
        self._renderer.push_matrix()

    def pop_matrix(self) -> None:
        """Restore model-view matrix from stack."""
        self._renderer.pop_matrix()

    def load_identity(self) -> None:
        """Reset model-view matrix to identity."""
        self._renderer.load_identity()

    def translate(self, x: float, y: float, z: float) -> None:
        """Apply translation to current matrix."""
        self._renderer.translate(x, y, z)

    def rotate(self, angle_degrees: float, x: float, y: float, z: float) -> None:
        """Apply rotation around axis to current matrix."""
        self._renderer.rotate(angle_degrees, x, y, z)

    def scale(self, x: float, y: float, z: float) -> None:
        """Apply scaling to current matrix."""
        self._renderer.scale(x, y, z)

    def multiply_matrix(self, matrix: np.ndarray) -> None:
        """Multiply current matrix by given 4x4 matrix."""
        self._renderer.multiply_matrix(matrix)

    def look_at(
        self,
        eye_x: float, eye_y: float, eye_z: float,
        center_x: float, center_y: float, center_z: float,
        up_x: float, up_y: float, up_z: float,
    ) -> None:
        """Set up view matrix to look at a point.

        Note: ModernGLRenderer uses direct matrix operations for camera.
        This method computes the look-at matrix and applies it.
        """
        # Compute look-at matrix
        from cube.presentation.gui.backends.pyglet2.matrix import look_at as compute_look_at
        look_at_matrix = compute_look_at(
            (eye_x, eye_y, eye_z),
            (center_x, center_y, center_z),
            (up_x, up_y, up_z)
        )
        self._renderer.multiply_matrix(look_at_matrix)

    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float, float]:
        """Convert screen coordinates to world coordinates."""
        return self._renderer.screen_to_world(
            screen_x, screen_y, self._window_width, self._window_height
        )


class ModernGLShapeAdapter:
    """Shape renderer adapter for ModernGLRenderer.

    Provides ShapeRenderer-like interface for effects that need simple shape drawing.
    """

    def __init__(self, modern_renderer: "ModernGLRenderer"):
        self._renderer = modern_renderer

    def quad(self, vertices, color: tuple[int, int, int]) -> None:
        """Draw a filled quad with color."""
        self._renderer.set_color(*color)
        self._renderer.quad(vertices)

    def triangle(self, vertices, color: tuple[int, int, int]) -> None:
        """Draw a filled triangle with color."""
        self._renderer.set_color(*color)
        self._renderer.triangle(vertices)

    def line(self, p1, p2, width: float = 1.0, color: tuple[int, int, int] = (255, 255, 255)) -> None:
        """Draw a line with color."""
        self._renderer.set_color(*color)
        self._renderer.line(p1, p2, width)


class ModernGLRendererAdapter:
    """Renderer protocol adapter for pyglet2's ModernGLRenderer.

    This adapter makes ModernGLRenderer compatible with code that expects
    the legacy Renderer protocol (specifically renderer.view for zoom commands).

    Part of B4 fix: Zoom crash in pyglet2 backend.
    """

    def __init__(self, modern_renderer: ModernGLRenderer, window_width: int = 800, window_height: int = 600):
        """Initialize the adapter.

        Args:
            modern_renderer: The ModernGLRenderer to wrap
            window_width: Initial window width
            window_height: Initial window height
        """
        self._modern_renderer = modern_renderer
        self._view = ModernGLViewStateManager(modern_renderer, window_width, window_height)
        self._shapes = ModernGLShapeAdapter(modern_renderer)

    @property
    def view(self) -> ModernGLViewStateManager:
        """Access view transformation methods (ViewStateManager protocol)."""
        return self._view

    @property
    def shapes(self) -> ModernGLShapeAdapter:
        """Access shape rendering methods."""
        return self._shapes

    @property
    def display_lists(self):
        """Display lists not supported in modern GL - use VBOs instead."""
        raise NotImplementedError("display_lists not supported in modern GL - use VBOs instead")

    def update_window_size(self, width: int, height: int) -> None:
        """Update window size for view state manager."""
        self._view.update_window_size(width, height)
