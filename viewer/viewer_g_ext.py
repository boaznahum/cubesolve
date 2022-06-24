import math
from collections.abc import Sequence
from typing import Tuple

from pyglet import gl  # type: ignore

import config
from app_state import ApplicationAndViewState


class GViewerExt:
    """
    Some extensions to graphic viewer
    """

    @staticmethod
    def draw_axis(vs: ApplicationAndViewState):

        axis_length = config.AXIS_LENGTH

        gl.glPushAttrib(gl.GL_MATRIX_MODE)
        gl.glMatrixMode(gl.GL_MODELVIEW)

        gl.glPushMatrix()

        gl.glLoadIdentity()

        offset: Sequence[int] = vs.offset

        gl.glTranslatef(offset[0], offset[1], offset[2])

        # print_matrix("GL_MODELVIEW_MATRIX", gl.GL_MODELVIEW_MATRIX)
        # print_matrix("GL_PROJECTION_MATRIX", gl.GL_PROJECTION_MATRIX)
        # print_matrix("GL_VIEWPORT", gl.GL_VIEWPORT)

        # ideally we want the axis to be fixed, but in this case we won't see the Z,
        #  so we rotate the Axes, or we should change the perspective
        gl.glRotatef(math.degrees(vs.alpha_x_0), 1, 0, 0)
        gl.glRotatef(math.degrees(vs.alpha_y_0), 0, 1, 0)
        gl.glRotatef(math.degrees(vs.alpha_z_0), 0, 0, 1)

        gl.glPushAttrib(gl.GL_LINE_WIDTH)
        gl.glLineWidth(3)

        gl.glBegin(gl.GL_LINES)

        gl.glColor3ub(255, 255, 255)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(axis_length, 0, 0)
        gl.glEnd()

        gl.glBegin(gl.GL_LINES)
        gl.glColor3ub(255, 0, 0)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(0, axis_length, 0)
        gl.glEnd()

        gl.glBegin(gl.GL_LINES)
        gl.glColor3ub(0, 255, 0)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(0, 0, axis_length)

        gl.glEnd()

        gl.glPopAttrib()  # line width

        # Pop Matrix off stack
        gl.glPopMatrix()
        gl.glPopAttrib()  # GL_MATRIX_MODE
