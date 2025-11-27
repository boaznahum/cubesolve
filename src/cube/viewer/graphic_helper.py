import numpy as np
from numpy import ndarray
from pyglet import gl  # type: ignore
from pyglet.gl import *  # type: ignore

projection_matrix = np.matrix([
    [1, 0, 0],
    [0, 1, 0]
])

scale = 1


def print_matrix(name, id: int):
    """

    :param name
    :param id:  GL_MODELVIEW_MATRIX, GL_PROJECTION_MATRIX, GL_VIEWPORT
    :return:
    """
    v = (gl.GLdouble * 16)()
    gl.glGetDoublev(id, v)

    m: ndarray = np.array([*v])  # because iterator return floats

    m = m.reshape((4, 4)).transpose()

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



def hilo(a, b, c):
    if c < b: b, c = c, b
    if b < a: a, b = b, a
    if c < b: b, c = c, b
    return a + c

def complement(r, g, b):
    #k = hilo(r, g, b)
    #return tuple(k - u for u in (r, g, b))

    return tuple(255 - u for u in (r, g, b))

