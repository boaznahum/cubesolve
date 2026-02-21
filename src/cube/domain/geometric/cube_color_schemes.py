"""Color Scheme Bank — factory functions for standard cube color schemes.

Each function returns a **new read-only** ``CubeColorScheme``.
No global singletons — callers own the instance.

Usage:
    from cube.domain.geometric.cube_color_schemes import boy_scheme
    scheme = boy_scheme()
"""

from __future__ import annotations

import random as _random

from cube.domain.geometric.cube_color_scheme import CubeColorScheme
from cube.domain.geometric.schematic_cube import SchematicCube
from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName

_BOY_FACES: dict[FaceName, Color] = {
    FaceName.F: Color.BLUE,
    FaceName.R: Color.RED,
    FaceName.U: Color.YELLOW,
    FaceName.L: Color.ORANGE,
    FaceName.D: Color.WHITE,
    FaceName.B: Color.GREEN,
}


def boy_scheme() -> CubeColorScheme:
    """Standard Western BOY (Blue-Orange-Yellow on the Front-Left-Up corner).

    Face colors:
        Front=Blue, Right=Red, Up=Yellow, Left=Orange, Down=White, Back=Green
    """
    return CubeColorScheme(_BOY_FACES, read_only=True)


def random_scheme() -> CubeColorScheme:
    """Random valid color scheme — a random whole-cube rotation of BOY.

    There are exactly 24 orientations of a cube (one per element of the
    rotation group).  This picks one uniformly at random by:

    1. Choosing a random face to become Front (6 choices).
    2. Choosing a random neighbor of that face to become Up (4 choices).
    3. Rotating a copy of BOY accordingly.

    The result is always a valid color scheme (same opposite-pair structure
    as BOY, just viewed from a different orientation).
    """
    scheme = SchematicCube.inst()
    boy = CubeColorScheme(_BOY_FACES)  # mutable copy for rotation

    # Pick which original face's color will become Front
    new_front: FaceName = _random.choice(list(FaceName))

    # Pick which neighbor of new_front will become Up
    neighbors: list[FaceName] = scheme.get_face_neighbors_cw_names(new_front)
    new_up: FaceName = _random.choice(neighbors)

    # The colors we want at Front and Up
    front_color: Color = _BOY_FACES[new_front]
    up_color: Color = _BOY_FACES[new_up]

    # Rotate: bring front_color to the F position
    boy._bring_face_to_front(boy._find_face(front_color))

    # Rotate: bring up_color to the U position, keeping F fixed
    # (it may have moved during the first rotation)
    boy._bring_face_up_preserve_front(boy._find_face(up_color))

    return CubeColorScheme(boy.faces, read_only=True)

