import numpy as np

from collections.abc import Sequence


def in_box(x, y, z, bottom_quad: Sequence[np.ndarray],
           top_quad: Sequence[np.ndarray]):
    """

    Checks if a point is inside a 3D box defined by two quadrilaterals.

    The function uses vector dot products to determine if the point is within the bounds of the box.

    :param x: The x-coordinate of the point to check.
    :param y: The y-coordinate of the point to check.
    :param z: The z-coordinate of the point to check.
    :param bottom_quad: The bottom quadrilateral defining the box. It should be a sequence of four points
    representing [left_bottom, right_bottom, right_top, left_top].
    :param top_quad: The top quadrilateral defining the box. It should be a sequence of four points
    representing [left_bottom, right_bottom, right_top, left_top].
    :return: True if the point is inside the box, False otherwise.

    References:
    - https://stackoverflow.com/questions/2752725/finding-whether-a-point-lies-inside-a-rectangle-or-not
    - https://math.stackexchange.com/questions/1472049/check-if-a-point-is-inside-a-rectangular-shaped-area-3d
    """

    # # Assuming the rectangle is represented by three points A,B,C, with AB and BC perpendicular
    #
    #    p6-------p7
    #   /         /
    #  /         /
    # p5 ------ p8
    #
    #
    #    p2-------p3
    #   /         /
    #  /         /
    # p1 ------ p4
    #
    # Given p1,p2,p4,p5 vertices of your cuboid, and pv the point to test for intersection with the cuboid, compute:
    # i=p2−p1
    # j=p4−p1
    # k=p5−p1
    # v=pv−p1
    # then, if
    # 0<v⋅i<i⋅i
    # 0<v⋅j<j⋅j
    # 0<v⋅k<k⋅k

    p1 = bottom_quad[0]
    p2 = bottom_quad[3]
    p4 = bottom_quad[1]
    p5 = top_quad[0]

    i = p2 - p1
    j = p4 - p1
    k = p5 - p1
    v = np.array([x, y, z]) - p1

    dot = np.dot

    ii = dot(i, i)
    jj = dot(j, j)
    kk = dot(k, k)
    vi = dot(v, i)
    vj = dot(v, j)
    vk = dot(v, k)

    res = 0 <= vi <= ii and 0 <= vj <= jj and 0 <= vk <= kk

    # if res:
    #     print(f"{x} {y} {z}")
    #     print(f"{bottom_quad=}")
    #     print(f"{top_quad=}")
    #
    return res
