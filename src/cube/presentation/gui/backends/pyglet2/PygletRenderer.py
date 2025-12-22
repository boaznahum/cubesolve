"""
Pyglet 2.0/OpenGL renderer implementation.

Wraps OpenGL rendering calls to implement the Renderer protocol.
Uses pyglet.gl.gl_compat for legacy OpenGL functions and PyOpenGL for GLU.
"""

from typing import Sequence

import numpy as np

try:
    import pyglet

    # GLU functions are not in pyglet 2.0 - use PyOpenGL instead
    from OpenGL import GLU as glu

    # Pyglet 2.0 uses modern OpenGL by default - use gl_compat for legacy functions
    from pyglet.gl import gl_compat as gl
except ImportError as e:
    raise ImportError(
        "pyglet2 backend requires: pip install 'pyglet>=2.0' PyOpenGL"
    ) from e

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


class PygletShapeRenderer(ShapeRenderer):
    """OpenGL shape renderer implementing ShapeRenderer protocol."""

    def quad(self, vertices: Sequence[Point3D], color: Color3) -> None:
        """Draw a filled quad."""
        gl.glColor3ub(*color)
        gl.glBegin(gl.GL_QUADS)
        for v in vertices:
            gl.glVertex3f(float(v[0]), float(v[1]), float(v[2]))
        gl.glEnd()

    def quad_with_border(
        self,
        vertices: Sequence[Point3D],
        face_color: Color3,
        line_width: float = 1.0,
        line_color: Color3 = (0, 0, 0),
    ) -> None:
        """Draw a quad with border."""
        # Draw filled quad
        self.quad(vertices, face_color)

        # Draw border
        gl.glLineWidth(line_width)
        gl.glColor3ub(*line_color)
        gl.glBegin(gl.GL_LINE_LOOP)
        for v in vertices:
            gl.glVertex3f(float(v[0]), float(v[1]), float(v[2]))
        gl.glEnd()

    def triangle(self, vertices: Sequence[Point3D], color: Color3) -> None:
        """Draw a filled triangle."""
        gl.glColor3ub(*color)
        gl.glBegin(gl.GL_TRIANGLES)
        for v in vertices:
            gl.glVertex3f(float(v[0]), float(v[1]), float(v[2]))
        gl.glEnd()

    def line(
        self,
        p1: Point3D,
        p2: Point3D,
        width: float = 1.0,
        color: Color3 = (255, 255, 255),
    ) -> None:
        """Draw a line."""
        gl.glLineWidth(width)
        gl.glColor3ub(*color)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(float(p1[0]), float(p1[1]), float(p1[2]))
        gl.glVertex3f(float(p2[0]), float(p2[1]), float(p2[2]))
        gl.glEnd()

    def sphere(
        self,
        center: Point3D,
        radius: float,
        color: Color3,
        slices: int = 16,
        stacks: int = 16,
    ) -> None:
        """Draw a sphere using GLU quadric."""
        gl.glColor3ub(*color)
        gl.glPushMatrix()
        gl.glTranslatef(float(center[0]), float(center[1]), float(center[2]))

        quadric = glu.gluNewQuadric()
        glu.gluSphere(quadric, radius, slices, stacks)
        glu.gluDeleteQuadric(quadric)

        gl.glPopMatrix()

    def cylinder(
        self,
        p1: Point3D,
        p2: Point3D,
        radius1: float,
        radius2: float,
        color: Color3,
        slices: int = 16,
    ) -> None:
        """Draw a cylinder between two points."""
        gl.glColor3ub(*color)

        # Calculate cylinder axis
        dx = float(p2[0] - p1[0])
        dy = float(p2[1] - p1[1])
        dz = float(p2[2] - p1[2])
        length = np.sqrt(dx * dx + dy * dy + dz * dz)

        if length < 1e-6:
            return

        gl.glPushMatrix()
        gl.glTranslatef(float(p1[0]), float(p1[1]), float(p1[2]))

        # Calculate rotation to align Z axis with cylinder axis
        if abs(dz) < 1e-6:
            if abs(dy) < 1e-6:
                # Pointing along X
                angle = 90.0 if dx > 0 else -90.0
                gl.glRotatef(angle, 0, 1, 0)
            else:
                # Pointing along Y
                angle = -90.0 if dy > 0 else 90.0
                gl.glRotatef(angle, 1, 0, 0)
        else:
            # General case
            ax = -dy
            ay = dx
            angle = np.degrees(np.arccos(dz / length))
            gl.glRotatef(angle, ax, ay, 0)

        quadric = glu.gluNewQuadric()
        glu.gluCylinder(quadric, radius1, radius2, length, slices, 1)
        glu.gluDeleteQuadric(quadric)

        gl.glPopMatrix()

    def disk(
        self,
        center: Point3D,
        normal: Point3D,
        inner_radius: float,
        outer_radius: float,
        color: Color3,
        slices: int = 25,
    ) -> None:
        """Draw a disk perpendicular to the normal vector."""
        gl.glColor3ub(*color)

        # Normalize the normal vector
        nx, ny, nz = float(normal[0]), float(normal[1]), float(normal[2])
        length = np.sqrt(nx * nx + ny * ny + nz * nz)
        if length < 1e-6:
            return
        nx, ny, nz = nx / length, ny / length, nz / length

        gl.glPushMatrix()
        gl.glTranslatef(float(center[0]), float(center[1]), float(center[2]))

        # Rotate to align Z axis with normal
        # Default disk is in XY plane (normal = Z axis)
        if abs(nz - 1.0) > 1e-6:  # Not already aligned with Z
            if abs(nz + 1.0) < 1e-6:  # Pointing in -Z direction
                gl.glRotatef(180.0, 1, 0, 0)
            else:
                # General rotation
                angle = np.degrees(np.arccos(nz))
                # Rotation axis is cross product of Z and normal: (-ny, nx, 0)
                gl.glRotatef(angle, -ny, nx, 0)

        quadric = glu.gluNewQuadric()
        glu.gluQuadricNormals(quadric, glu.GLU_SMOOTH)
        glu.gluDisk(quadric, inner_radius, outer_radius, slices, 1)
        glu.gluDeleteQuadric(quadric)

        gl.glPopMatrix()

    def lines(
        self,
        points: Sequence[tuple[Point3D, Point3D]],
        width: float,
        color: Color3,
    ) -> None:
        """Draw multiple line segments."""
        gl.glLineWidth(width)
        gl.glColor3ub(*color)
        gl.glBegin(gl.GL_LINES)
        for p1, p2 in points:
            gl.glVertex3f(float(p1[0]), float(p1[1]), float(p1[2]))
            gl.glVertex3f(float(p2[0]), float(p2[1]), float(p2[2]))
        gl.glEnd()

    def quad_with_texture(
        self,
        vertices: Sequence[Point3D],
        color: Color3,
        texture: TextureHandle | None,
        texture_map: TextureMap | None,
    ) -> None:
        """Draw a textured quad."""
        # Enable texturing if we have a texture
        if texture is not None and texture_map is not None:
            gl.glEnable(gl.GL_TEXTURE_2D)
            gl.glBindTexture(gl.GL_TEXTURE_2D, int(texture))

        gl.glColor3ub(*color)
        gl.glBegin(gl.GL_QUADS)
        for i, v in enumerate(vertices):
            if texture_map is not None and i < len(texture_map):
                gl.glTexCoord2i(texture_map[i].u, texture_map[i].v)
            gl.glVertex3f(float(v[0]), float(v[1]), float(v[2]))
        gl.glEnd()

        if texture is not None:
            gl.glDisable(gl.GL_TEXTURE_2D)

    def cross(
        self,
        vertices: Sequence[Point3D],
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Draw a cross (X) inside a quadrilateral."""
        # vertices: [left_bottom, right_bottom, right_top, left_top]
        gl.glLineWidth(line_width)
        gl.glColor3ub(*line_color)
        gl.glBegin(gl.GL_LINES)
        # Diagonal from left_bottom to right_top
        gl.glVertex3f(float(vertices[0][0]), float(vertices[0][1]), float(vertices[0][2]))
        gl.glVertex3f(float(vertices[2][0]), float(vertices[2][1]), float(vertices[2][2]))
        # Diagonal from right_bottom to left_top
        gl.glVertex3f(float(vertices[1][0]), float(vertices[1][1]), float(vertices[1][2]))
        gl.glVertex3f(float(vertices[3][0]), float(vertices[3][1]), float(vertices[3][2]))
        gl.glEnd()

    def lines_in_quad(
        self,
        vertices: Sequence[Point3D],
        n: int,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Draw n evenly-spaced vertical lines inside a quadrilateral."""
        if n <= 0:
            return

        # vertices: [left_bottom, right_bottom, right_top, left_top]
        lb = np.array(vertices[0], dtype=float)
        rb = np.array(vertices[1], dtype=float)
        lt = np.array(vertices[3], dtype=float)
        rt = np.array(vertices[2], dtype=float)

        # Calculate step vectors
        dx_bottom = (rb - lb) / (n + 1)
        dx_top = (rt - lt) / (n + 1)

        gl.glLineWidth(line_width)
        gl.glColor3ub(*line_color)
        gl.glBegin(gl.GL_LINES)

        for i in range(n):
            # Position along bottom and top edges
            p_bottom = lb + dx_bottom * (i + 1)
            p_top = lt + dx_top * (i + 1)
            gl.glVertex3f(float(p_bottom[0]), float(p_bottom[1]), float(p_bottom[2]))
            gl.glVertex3f(float(p_top[0]), float(p_top[1]), float(p_top[2]))

        gl.glEnd()

    def box_with_lines(
        self,
        bottom_quad: Sequence[Point3D],
        top_quad: Sequence[Point3D],
        face_color: Color3,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Draw a 3D box with filled faces and line borders."""
        # Indices for quad vertices: [left_bottom, right_bottom, right_top, left_top]
        lb, rb, rt, lt = 0, 1, 2, 3

        # Draw six faces
        # Bottom face
        self.quad_with_border(list(bottom_quad), face_color, line_width, line_color)
        # Top face
        self.quad_with_border(list(top_quad), face_color, line_width, line_color)
        # Front face
        self.quad_with_border(
            [bottom_quad[lb], bottom_quad[rb], top_quad[rb], top_quad[lb]],
            face_color, line_width, line_color
        )
        # Back face
        self.quad_with_border(
            [bottom_quad[rb], bottom_quad[rt], top_quad[rt], top_quad[rb]],
            face_color, line_width, line_color
        )
        # Right face
        self.quad_with_border(
            [bottom_quad[lt], bottom_quad[rt], top_quad[rt], top_quad[lt]],
            face_color, line_width, line_color
        )
        # Left face
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
        slices: int = 25,
        stacks: int = 25,
    ) -> None:
        """Draw a hollow cylinder with capped ends."""
        from math import acos, pi, sqrt

        # Convert to numpy arrays for easier math
        _p1 = np.array([float(p1[0]), float(p1[1]), float(p1[2])])
        _p2 = np.array([float(p2[0]), float(p2[1]), float(p2[2])])

        # Swap if needed (from original shapes.py logic)
        if (_p1[0] == _p2[0]) and (_p1[2] == _p2[2]) and (_p1[1] < _p2[1]):
            _p1, _p2 = _p2, _p1

        # Calculate height
        d = _p1 - _p2
        height = sqrt(float(d.dot(d)))
        if height < 1e-6:
            return

        r2d = 180.0 / pi

        gl.glColor3ub(*color)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glTranslatef(_p1[0], _p1[1], _p1[2])

        # Calculate rotation to align Z with cylinder axis
        _v = _p2 - _p1
        v = float(np.linalg.norm(_v))
        vx, vy, vz = _v[0], _v[1], _v[2]

        rx = -vy * vz
        ry = vx * vz

        if vz == 0:
            ax = r2d * acos(vx / v)
            if vx <= 0:
                ax = -ax
            gl.glRotated(90.0, 0, 1, 0.0)
            gl.glRotated(ax, -1.0, 0.0, 0.0)
        else:
            ax = r2d * acos(vz / v)
            if vz <= 0:
                ax = -ax
            gl.glRotated(ax, rx, ry, 0)

        # Ensure inner < outer
        r_inner = min(inner_radius, outer_radius)
        r_outer = max(inner_radius, outer_radius)

        quadric = glu.gluNewQuadric()
        glu.gluQuadricNormals(quadric, glu.GLU_SMOOTH)

        # Draw outer and inner cylinders
        glu.gluCylinder(quadric, r_inner, r_inner, height, slices, stacks)
        glu.gluCylinder(quadric, r_outer, r_outer, height, slices, stacks)

        # Draw bottom disk (at origin after transformation)
        glu.gluDisk(quadric, r_inner, r_outer, slices, stacks)

        # Draw top disk
        gl.glTranslatef(0, 0, height)
        glu.gluDisk(quadric, r_inner, r_outer, slices, stacks)

        glu.gluDeleteQuadric(quadric)
        gl.glPopMatrix()


class PygletDisplayListManager(DisplayListManager):
    """OpenGL display list manager implementing DisplayListManager protocol."""

    def __init__(self) -> None:
        self._next_id = 1
        self._lists: dict[int, int] = {}  # our_id -> gl_list_id
        self._compiling: int | None = None

    def create_list(self) -> DisplayList:
        """Create a new display list."""
        gl_list = gl.glGenLists(1)
        list_id = self._next_id
        self._next_id += 1
        self._lists[list_id] = gl_list
        return DisplayList(list_id)

    def begin_compile(self, list_id: DisplayList) -> None:
        """Begin compiling commands into a display list."""
        if list_id in self._lists:
            gl.glNewList(self._lists[list_id], gl.GL_COMPILE)
            self._compiling = list_id

    def end_compile(self) -> None:
        """End display list compilation."""
        if self._compiling is not None:
            gl.glEndList()
            self._compiling = None

    def call_list(self, list_id: DisplayList) -> None:
        """Execute a display list."""
        if list_id in self._lists:
            gl.glCallList(self._lists[list_id])

    def call_lists(self, list_ids: Sequence[DisplayList]) -> None:
        """Execute multiple display lists."""
        for list_id in list_ids:
            self.call_list(list_id)

    def delete_list(self, list_id: DisplayList) -> None:
        """Delete a display list."""
        if list_id in self._lists:
            gl.glDeleteLists(self._lists[list_id], 1)
            del self._lists[list_id]

    def delete_lists(self, list_ids: Sequence[DisplayList]) -> None:
        """Delete multiple display lists."""
        for list_id in list_ids:
            self.delete_list(list_id)


class PygletViewStateManager(ViewStateManager):
    """OpenGL view state manager implementing ViewStateManager protocol."""

    def set_projection(
        self,
        width: int,
        height: int,
        fov_y: float = 45.0,
        near: float = 0.1,
        far: float = 100.0,
    ) -> None:
        """Set up perspective projection."""
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

        aspect = width / height if height > 0 else 1.0
        glu.gluPerspective(fov_y, aspect, near, far)

        gl.glMatrixMode(gl.GL_MODELVIEW)

    def push_matrix(self) -> None:
        """Push current matrix onto stack."""
        gl.glPushMatrix()

    def pop_matrix(self) -> None:
        """Pop matrix from stack."""
        gl.glPopMatrix()

    def load_identity(self) -> None:
        """Load identity matrix."""
        gl.glLoadIdentity()

    def translate(self, x: float, y: float, z: float) -> None:
        """Apply translation."""
        gl.glTranslatef(x, y, z)

    def rotate(self, angle_degrees: float, x: float, y: float, z: float) -> None:
        """Apply rotation (angle in degrees)."""
        gl.glRotatef(angle_degrees, x, y, z)

    def scale(self, x: float, y: float, z: float) -> None:
        """Apply scaling."""
        gl.glScalef(x, y, z)

    def multiply_matrix(self, matrix: Matrix4x4) -> None:
        """Multiply current matrix by given 4x4 matrix."""
        # Convert to column-major order for OpenGL
        m = (gl.GLfloat * 16)()
        m[:] = matrix.flatten(order='F').tolist()
        gl.glMultMatrixf(m)

    def look_at(
        self,
        eye_x: float, eye_y: float, eye_z: float,
        center_x: float, center_y: float, center_z: float,
        up_x: float, up_y: float, up_z: float,
    ) -> None:
        """Set up view matrix using look-at parameters."""
        glu.gluLookAt(
            eye_x, eye_y, eye_z,
            center_x, center_y, center_z,
            up_x, up_y, up_z,
        )

    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float, float]:
        """Convert screen coordinates to world coordinates.

        Uses gluUnProject with current matrices and depth buffer.

        Note: screen_y is expected in OpenGL/pyglet convention (origin at bottom-left).
        """
        # Get current matrices and viewport
        pmat = (gl.GLdouble * 16)()
        mvmat = (gl.GLdouble * 16)()
        viewport = (gl.GLint * 4)()

        gl.glGetIntegerv(gl.GL_VIEWPORT, viewport)
        gl.glGetDoublev(gl.GL_PROJECTION_MATRIX, pmat)
        gl.glGetDoublev(gl.GL_MODELVIEW_MATRIX, mvmat)

        # screen_y is already in OpenGL convention (bottom-left origin)
        # No conversion needed for pyglet backend

        # Read depth at the pixel
        depth = (gl.GLfloat * 1)()
        gl.glReadPixels(int(screen_x), int(screen_y), 1, 1, gl.GL_DEPTH_COMPONENT, gl.GL_FLOAT, depth)

        # Unproject to world coordinates
        result = glu.gluUnProject(screen_x, screen_y, depth[0], mvmat, pmat, viewport)

        return (result[0], result[1], result[2])


class PygletRenderer(Renderer):
    """Pyglet/OpenGL renderer implementing Renderer protocol."""

    def __init__(self) -> None:
        self._shapes = PygletShapeRenderer()
        self._display_lists = PygletDisplayListManager()
        self._view = PygletViewStateManager()
        self._initialized = False

    @property
    def shapes(self) -> PygletShapeRenderer:
        """Access shape rendering methods."""
        return self._shapes

    @property
    def display_lists(self) -> PygletDisplayListManager:
        """Access display list management."""
        return self._display_lists

    @property
    def view(self) -> PygletViewStateManager:
        """Access view state management."""
        return self._view

    def setup(self) -> None:
        """Initialize OpenGL state."""
        if self._initialized:
            return

        gl.glClearColor(0, 0, 0, 1)
        # Note: GL_DEPTH_TEST is enabled by Window.py after setup()
        # Do NOT enable GL_CULL_FACE - it breaks cube rendering

        self._initialized = True

    def cleanup(self) -> None:
        """Clean up OpenGL resources."""
        self._initialized = False

    def begin_frame(self) -> None:
        """Begin a new frame."""
        pass  # OpenGL doesn't need explicit frame begin

    def end_frame(self) -> None:
        """End the current frame."""
        gl.glFlush()

    def clear(self, color: Color4 | None = None) -> None:
        """Clear the screen."""
        if color is not None:
            gl.glClearColor(
                color[0] / 255.0,
                color[1] / 255.0,
                color[2] / 255.0,
                color[3] / 255.0,
            )
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    def flush(self) -> None:
        """Flush rendering commands."""
        gl.glFlush()

    def load_texture(self, file_path: str) -> TextureHandle | None:
        """Load a texture from a file."""
        try:
            image = pyglet.image.load(file_path)
            data = image.get_image_data()
            texture_data = data.get_data(fmt="RGBA")

            ids = (gl.GLuint * 1)()
            gl.glGenTextures(1, ids)
            tex_id = ids[0]

            gl.glBindTexture(gl.GL_TEXTURE_2D, tex_id)
            glu.gluBuild2DMipmaps(
                gl.GL_TEXTURE_2D, 4,
                image.width, image.height,
                gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, texture_data
            )

            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR_MIPMAP_LINEAR)

            return TextureHandle(tex_id)
        except Exception:
            return None

    def bind_texture(self, texture: TextureHandle | None) -> None:
        """Bind a texture for rendering."""
        if texture is not None:
            gl.glEnable(gl.GL_TEXTURE_2D)
            gl.glBindTexture(gl.GL_TEXTURE_2D, int(texture))
        else:
            gl.glDisable(gl.GL_TEXTURE_2D)

    def delete_texture(self, texture: TextureHandle) -> None:
        """Delete a texture."""
        p = (gl.GLuint * 1)()
        p[0] = int(texture)
        gl.glDeleteTextures(1, p)
