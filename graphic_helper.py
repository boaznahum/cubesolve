from collections.abc import Sequence
from math import *

import numpy as np
from numpy import ndarray
from pyglet.gl import *  # type: ignore
from pyglet import gl  # type: ignore

projection_matrix = np.matrix([
    [1, 0, 0],
    [0, 1, 0]
])

scale = 1


def vec3to2(point: np.ndarray,
            alpha_x: float, alpha_y: float, alpha_z: float,
            screen0: Sequence[int]) -> Sequence[int, int]:
    a_x = alpha_x
    a_y = alpha_y
    a_z = alpha_z

    rotation_z = np.matrix([
        [cos(a_z), -sin(a_z), 0],
        [sin(a_z), cos(a_z), 0],
        [0, 0, 1],
    ])

    rotation_y = np.matrix([
        [cos(a_y), 0, sin(a_y)],
        [0, 1, 0],
        [-sin(a_y), 0, cos(a_y)],
    ])

    rotation_x = np.matrix([
        [1, 0, 0],
        [0, cos(a_x), -sin(a_x)],
        [0, sin(a_x), cos(a_x)],
    ])

    rotated2d = np.dot(rotation_z, np.matrix(point).reshape((3, 1)))
    rotated2d = np.dot(rotation_y, rotated2d)
    rotated2d = np.dot(rotation_x, rotated2d)

    projected2d = np.dot(projection_matrix, rotated2d)

    x = int(projected2d[0][0] * scale) + screen0[0]
    y = int(projected2d[1][0] * scale) + screen0[1]

    return (x, y)


def print_matrix(name, id: int):
    """

    :param id:  GL_MODELVIEW_MATRIX, GL_PROJECTION_MATRIX, GL_VIEWPORT
    :return:
    """
    v = (gl.GLdouble * 16)()
    gl.glGetDoublev(id, v)

    m: ndarray = np.array( [ *v ]) # because iterator return floats

    m=m.reshape((4,4)).transpose()

    # from column major to row major
    # m = [
    #     [v[0], v[4], v[8], v[12]],
    #     [v[1], v[5], v[9], v[13]],
    #     [v[2], v[6], v[10], v[14]],
    #     [v[3], v[7], v[11], v[15]]
    # ]

    print(name + ":")
    for r in m:
        print(" ", r)
