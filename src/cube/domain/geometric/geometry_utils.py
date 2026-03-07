from collections.abc import Sequence
from typing import Tuple, TypeVar

import numpy as np

from cube.domain.geometric.geometry_types import Point


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

def inv(n_slices:int, x: int) -> int:
    return n_slices - x -1


def rotate_point_clockwise(rc: Tuple[int, int] | Point, n_slices: int, n_rotations: int = 1) -> Point:
    """
    Rotate a point clockwise on the face by n * 90 degrees.

    Args:
        rc: Point (row, col) - accepts both tuple and Point
        n_rotations: Number of 90-degree rotations (supports negative for counterclockwise)

    Returns:
        Rotated point as Point
    """

    r, c = rc[0], rc[1]
    nm1 = n_slices - 1
    rot = n_rotations % 4
    if rot == 0:
        return Point(r, c)
    if rot == 1:
        return Point(nm1 - c, r)
    if rot == 2:
        return Point(nm1 - r, nm1 - c)
    # rot == 3
    return Point(c, nm1 - r)


_T = TypeVar("_T")


def same_cycle(a: Sequence[_T], b: Sequence[_T]) -> bool:
    """Check if two sequences are cyclic rotations of each other.

    ``b`` is a rotation of ``a`` iff ``len(a) == len(b)`` and ``b``
    appears at some offset in ``a + a``.  We find the first element
    of ``b`` in ``a``, then verify the full match from each candidate
    position.  O(n) on average for sequences with distinct elements.

    >>> same_cycle([1, 2, 3, 4], [3, 4, 1, 2])
    True
    >>> same_cycle([1, 2, 3], [1, 3, 2])
    False
    >>> same_cycle([], [])
    True
    """
    n = len(a)
    if n != len(b):
        return False
    if n == 0:
        return True
    # Find candidate start positions (where a[start] == b[0])
    # then verify the full match.  For sequences with mostly-distinct
    # elements (typical in cube faces) this is O(n).
    b0 = b[0]
    for start in range(n):
        if a[start] != b0:
            continue
        if all(a[(start + i) % n] == b[i] for i in range(1, n)):
            return True
    return False
