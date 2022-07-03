from collections.abc import Sequence
from contextlib import contextmanager
from math import pi, sqrt, acos
from typing import Tuple

import numpy as np
from numpy import ndarray
from pyglet import gl  # type: ignore
import pyglet.gl.glu as glu  # type: ignore
from pyglet.gl import *  # type: ignore


def quad_with_line(vertexes: Sequence[np.ndarray], face_color: Tuple[int, int, int],
                   line_width: float,
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


def cross(vertexes: Sequence[np.ndarray],
          line_width: int,
          line_color: Tuple[int, int, int]):
    """

    :param line_width:
    :param vertexes:  # [left_bottom, right_bottom, right_top, left_top]
    :param line_color:
    :return:
    """

    gl.glLineWidth(line_width)

    gl.glColor3ub(*line_color)
    gl.glBegin(gl.GL_LINES)
    gl.glVertex3f(*vertexes[0])
    gl.glVertex3f(*vertexes[2])
    gl.glVertex3f(*vertexes[1])
    gl.glVertex3f(*vertexes[3])

    gl.glEnd()


def lines_in_quad(vertexes: Sequence[np.ndarray],
                  n: int,
                  line_width: int,
                  line_color: Tuple[int, int, int]):
    """

    :param n:
    :param line_width:
    :param vertexes:  # [left_bottom, right_bottom, right_top, left_top]
    :param line_color:
    :return:
    """

    if n == 0:
        return

    lb = vertexes[0]
    rb = vertexes[1]
    rt = vertexes[2]
    lt = vertexes[3]

    # lb = lb.copy()
    # lt = lt.copy()

    dx1 = (rb - lb) / (n + 1)
    dx2 = (rt - lt) / (n + 1)

    gl.glLineWidth(line_width)
    gl.glColor3ub(*line_color)
    gl.glBegin(gl.GL_LINES)

    for i in range(n):
        lb = lb + dx1  # don't use +=
        lt = lt + dx2

        gl.glVertex3f(*lb)
        gl.glVertex3f(*lt)

    gl.glEnd()


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


def sphere(center: np.ndarray, radius: float, color: Tuple[int, int, int]):
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    gl.glTranslatef(center[0], center[1], center[2])
    _sphere = glu.gluNewQuadric()
    gl.glColor3ub(*color)
    glu.gluSphere(_sphere, radius, 25, 25)
    glu.gluDeleteQuadric(_sphere)
    gl.glPopMatrix()


def cylinder(p1: np.ndarray, p2: np.ndarray, r1: float, r2: float, color: Tuple[int, int, int]):
    """
     Draw a cylinder which is around the vector p1 p2 i.e. a cylinder on plane that is orthogonal to p1-p2
     and pass through p1
     bottom of disk is on p1 and top on p2
     """

    # https://community.khronos.org/t/glucylinder-between-two-points/34447/3

    if (p1[0] == p2[0]) and (p1[2] == p2[2]) and (p1[1] < p2[1]):
        p1, p2 = p2, p1

    r2d = 180 / pi
    # length of cylinder
    d: ndarray = p1 - p2
    height = sqrt(d.dot(d))

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    gl.glTranslatef(p1[0], p1[1], p1[2])

    # orientation vectors
    _v = p2 - p1
    v = np.linalg.norm(_v)  # // cylinder length

    vx = _v[0]
    vy = _v[1]
    vz = _v[2]

    # rotation vector, z x r
    rx = -vy * vz
    ry = +vx * vz
    ax: float
    if vz == 0:
        ax = r2d * acos(vx / v)  # rotation angle in x-y plane
        if vx <= 0:
            ax = -ax

    else:
        ax = r2d * acos(vz / v)  # rotation angle
        if vz <= 0:
            ax = -ax

    if vz == 0:

        gl.glRotated(90.0, 0, 1, 0.0)  # Rotate & align with x-axis
        gl.glRotated(ax, -1.0, 0.0, 0.0)  # Rotate to point 2 in x-y plane

    else:
        gl.glRotated(ax, rx, ry, 0)  # Rotate about rotation vector

    # Specifies the number of subdivisions around the z axis.
    slices = 25
    # Specifies the number of subdivisions along the z axis.
    stacks = 25

    # create a pointer to the quadratic object
    quadratic = glu.gluNewQuadric()

    # https://www.khronos.org/registry/OpenGL-Refpages/gl2.1/xhtml/gluQuadricDrawStyle.xml
    # glu.gluQuadricDrawStyle(quadratic, glu.GLU_FILL)

    # glu.gluQuadricTexture(quadratic, glu.GLU_TRUE)

    # tell it to smooth normals
    glu.gluQuadricNormals(quadratic, glu.GLU_SMOOTH)
    gl.glColor3ub(*color)
    # draw the cylinder
    glu.gluCylinder(quadratic, r1, r2, height, slices, stacks)  # Draw A cylinder
    gl.glPopMatrix()
    # delete the pointer
    glu.gluDeleteQuadric(quadratic)


@contextmanager
def _prepare_z_plane(p1: np.ndarray, p2: np.ndarray):
    """
     Move axis origin into p1, and put z on vector p1-p2
     yield p1, p2, |p1-p2|
     """

    # https://community.khronos.org/t/glucylinder-between-two-points/34447/3

    # todo: why ?
    if (p1[0] == p2[0]) and (p1[2] == p2[2]) and (p1[1] < p2[1]):
        p1, p2 = p2, p1

    r2d = 180 / pi
    # length of cylinder
    d: ndarray = p1 - p2
    height = sqrt(d.dot(d))

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    gl.glTranslatef(p1[0], p1[1], p1[2])

    # orientation vectors
    _v = p2 - p1
    v = np.linalg.norm(_v)  # // cylinder length

    vx = _v[0]
    vy = _v[1]
    vz = _v[2]

    # rotation vector, z x r
    rx = -vy * vz
    ry = +vx * vz
    ax: float
    if vz == 0:
        ax = r2d * acos(vx / v)  # rotation angle in x-y plane
        if vx <= 0:
            ax = -ax

    else:
        ax = r2d * acos(vz / v)  # rotation angle
        if vz <= 0:
            ax = -ax

    if vz == 0:

        gl.glRotated(90.0, 0, 1, 0.0)  # Rotate & align with x-axis
        gl.glRotated(ax, -1.0, 0.0, 0.0)  # Rotate to point 2 in x-y plane

    else:
        gl.glRotated(ax, rx, ry, 0)  # Rotate about rotation vector

    try:
        yield p1, p2, height
    finally:
        gl.glPopMatrix()


def full_cylinder(p1: np.ndarray, p2: np.ndarray, r1: float, r2: float, color: Tuple[int, int, int]):
    """
     Draw a cylinder which is around the vector p1 p2 i.e. a cylinder on plane that is orthogonal to p1-p2
     and pass through p1
     bottom of disk is on p1 and top on p2
     """

    with _prepare_z_plane(p1, p2) as (p1, p2, height):
        # Specifies the number of subdivisions around the z axis.
        slices = 25
        # Specifies the number of subdivisions along the z axis.
        stacks = 25

        # create a pointer to the quadratic object
        quadratic = glu.gluNewQuadric()

        # https://www.khronos.org/registry/OpenGL-Refpages/gl2.1/xhtml/gluQuadricDrawStyle.xml
        # glu.gluQuadricDrawStyle(quadratic, glu.GLU_FILL)

        # glu.gluQuadricTexture(quadratic, glu.GLU_TRUE)

        # tell it to smooth normals
        glu.gluQuadricNormals(quadratic, glu.GLU_SMOOTH)
        gl.glColor3ub(*color)
        # draw the cylinder

        if r1 > r2:
            r1, r2 = r2, r1

        glu.gluCylinder(quadratic, r1, r1, height, slices, stacks)  # Draw A cylinder
        glu.gluCylinder(quadratic, r2, r2, height, slices, stacks)  # Draw A cylinder

        glu.gluDisk(quadratic, r1, r2, slices, stacks)  # Draw A cylinder

        gl.glTranslatef(0, 0, height)
        glu.gluDisk(quadratic, r1, r2, slices, stacks)  # Draw A cylinder

        # delete the pointer
        glu.gluDeleteQuadric(quadratic)


def disk(p1: np.ndarray, p2: np.ndarray, r_outer: float, r_inner: float, color: Tuple[int, int, int]):
    """
    Draw a disk which is around the vector p1 p2 i.e. a disk on plane that is orthogonal to p1-p2 and pass through p1
    :param p1:
    :param p2:
    :param r_outer:
    :param r_inner: can be zero
    :param color:
    :return:
    """

    # https://community.khronos.org/t/glucylinder-between-two-points/34447/3

    if (p1[0] == p2[0]) and (p1[2] == p2[2]) and (p1[1] < p2[1]):
        p1, p2 = p2, p1

    r2d = 180 / pi
    # length of cylinder
    d: ndarray = p1 - p2

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    gl.glTranslatef(p1[0], p1[1], p1[2])

    # orientation vectors
    _v = p2 - p1
    v = np.linalg.norm(_v)  # // cylinder length

    vx = _v[0]
    vy = _v[1]
    vz = _v[2]

    # rotation vector, z x r
    rx = -vy * vz
    ry = +vx * vz
    ax: float
    if vz == 0:
        ax = r2d * acos(vx / v)  # rotation angle in x-y plane
        if vx <= 0:
            ax = -ax

    else:
        ax = r2d * acos(vz / v)  # rotation angle
        if vz <= 0:
            ax = -ax

    if vz == 0:

        gl.glRotated(90.0, 0, 1, 0.0)  # Rotate & align with x-axis
        gl.glRotated(ax, -1.0, 0.0, 0.0)  # Rotate to point 2 in x-y plane

    else:
        gl.glRotated(ax, rx, ry, 0)  # Rotate about rotation vector

    # Specifies the number of subdivisions around the z axis.
    slices = 25
    # Specifies the number of subdivisions along the z axis.
    stacks = 25

    # create a pointer to the quadratic object
    quadratic = glu.gluNewQuadric()

    # https://www.khronos.org/registry/OpenGL-Refpages/gl2.1/xhtml/gluQuadricDrawStyle.xml
    # glu.gluQuadricDrawStyle(quadratic, glu.GLU_FILL)

    # glu.gluQuadricTexture(quadratic, glu.GLU_TRUE)

    # tell it to smooth normals
    glu.gluQuadricNormals(quadratic, glu.GLU_SMOOTH)
    gl.glColor3ub(*color)
    # draw the cylinder
    glu.gluDisk(quadratic, r_inner, r_outer, slices, stacks)  # Draw A cylinder
    gl.glPopMatrix()
    # delete the pointer
    glu.gluDeleteQuadric(quadratic)
