from collections.abc import Sequence
from typing import Tuple

import numpy as np
from numpy import ndarray
from pyglet import gl  # type: ignore
from pyglet.gl import *  # type: ignore


def quad_with_line(vertexes: Sequence[np.ndarray], face_color: Tuple[int, int, int],
                   line_width: int,
                   line_color: Tuple[int, int, int]):
    """

    :param line_width:
    :param vertexes:  # [left_bottom, right_bottom, right_top, left_top]
    :param face_color:
    :param line_color:
    :return:
    """

    gl.glLineWidth(line_width)

    def _q(is_line: bool):
        if is_line:
            gl.glColor3ub(*line_color)
            gl.glBegin(gl.GL_LINE_LOOP)
        else:
            gl.glColor3ub(*face_color)
            gl.glBegin(gl.GL_QUADS)

        for v in vertexes:
            gl.glVertex3f(*v)

        gl.glEnd()

    _q(False)
    _q(True)


def box_with_lines(bottom_quad: Sequence[np.ndarray],
                   top_quad: Sequence[np.ndarray],
                   face_color: Tuple[int, int, int],
                   line_width: int,
                   line_color: Tuple[int, int, int]):
    """

    :param bottom_quad:  [left_bottom, right_bottom, right_top, left_top]
    :param top_quad:  [left_bottom, right_bottom, right_top, left_top]
    :param face_color:
    :param line_width:
    :param line_color:
    :return:
    """

    # [left_bottom, right_bottom, right_top, left_top]
    lb = 0
    rb = 1
    rt = 2
    lt = 3

    bottom = bottom_quad
    top = top_quad

    def _q(*vertexes: ndarray):
        quad_with_line([*vertexes], face_color, line_width, line_color)

    # create six quads to form a box

    # gl.glColor3ub(255, 51, 255)
    _q(*bottom)
    # gl.glColor3ub(51, 255, 51)
    _q(*top)

    # gl.glColor3ub(255, 255, 51)
    _q(bottom[lb], bottom[rb], top[rb], top[lb])

    # gl.glColor3ub(255, 0, 51)
    _q(bottom[rb], bottom[rt], top[rt], top[rb])

    # gl.glColor3ub(0, 255, 255)
    _q(bottom[lt], bottom[rt], top[rt], top[lt])

    # gl.glColor3ub(51, 102, 0)
    _q(bottom[lb], bottom[lt], top[lt], top[lb])
