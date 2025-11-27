"""
Pyglet/OpenGL renderer implementation.

Wraps OpenGL rendering calls to implement the Renderer protocol.
"""

from typing import Sequence
import numpy as np

try:
    import pyglet
    from pyglet import gl
except ImportError as e:
    raise ImportError("pyglet is required for PygletRenderer: pip install pyglet") from e

from cube.gui.types import Point3D, Color3, Color4, DisplayList, Matrix4x4


class PygletShapeRenderer:
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

        quadric = gl.gluNewQuadric()
        gl.gluSphere(quadric, radius, slices, stacks)
        gl.gluDeleteQuadric(quadric)

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

        quadric = gl.gluNewQuadric()
        gl.gluCylinder(quadric, radius1, radius2, length, slices, 1)
        gl.gluDeleteQuadric(quadric)

        gl.glPopMatrix()


class PygletDisplayListManager:
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


class PygletViewStateManager:
    """OpenGL view state manager implementing ViewStateManager protocol."""

    def set_projection(
        self,
        width: int,
        height: int,
        fov_y: float = 45.0,
        z_near: float = 0.1,
        z_far: float = 100.0,
    ) -> None:
        """Set up perspective projection."""
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

        aspect = width / height if height > 0 else 1.0
        gl.gluPerspective(fov_y, aspect, z_near, z_far)

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

    def rotate(self, angle: float, x: float, y: float, z: float) -> None:
        """Apply rotation (angle in degrees)."""
        gl.glRotatef(angle, x, y, z)

    def scale(self, x: float, y: float, z: float) -> None:
        """Apply scaling."""
        gl.glScalef(x, y, z)

    def multiply_matrix(self, matrix: Matrix4x4) -> None:
        """Multiply current matrix by given 4x4 matrix."""
        # Convert to column-major order for OpenGL
        m = (gl.GLfloat * 16)()
        m[:] = matrix.flatten(order='F')
        gl.glMultMatrixf(m)

    def look_at(
        self,
        eye_x: float, eye_y: float, eye_z: float,
        center_x: float, center_y: float, center_z: float,
        up_x: float, up_y: float, up_z: float,
    ) -> None:
        """Set up view matrix using look-at parameters."""
        gl.gluLookAt(
            eye_x, eye_y, eye_z,
            center_x, center_y, center_z,
            up_x, up_y, up_z,
        )


class PygletRenderer:
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
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glCullFace(gl.GL_BACK)

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
