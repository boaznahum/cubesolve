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
from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName

def boy_scheme() -> CubeColorScheme:
    """Standard Western BOY (Blue-Orange-Yellow on the Front-Left-Up corner).

    Face colors:
        Front=Blue, Right=Red, Up=Yellow, Left=Orange, Down=White, Back=Green
    """
    return CubeColorScheme({
        FaceName.F: Color.BLUE,
        FaceName.R: Color.RED,
        FaceName.U: Color.YELLOW,
        FaceName.L: Color.ORANGE,
        FaceName.D: Color.WHITE,
        FaceName.B: Color.GREEN,
    }, read_only=True)

def purple_pink() -> CubeColorScheme:
    """Standard Western BOY (Blue-Orange-Yellow on the Front-Left-Up corner).

    Face colors:
        Front=Blue, Right=Red, Up=Yellow, Left=Orange, Down=White, Back=Green
    """
    return CubeColorScheme({
        FaceName.F: Color.PURPLE,
        FaceName.R: Color.PINK,
        FaceName.U: Color.YELLOW,
        FaceName.L: Color.ORANGE,
        FaceName.D: Color.WHITE,
        FaceName.B: Color.GREEN,
    }, read_only=True)


def random_scheme() -> CubeColorScheme:
    """Random color scheme — pick 6 random colors from Color enum onto 6 faces."""
    colors = _random.sample(list(Color), k=len(FaceName))
    faces = dict(zip(list(FaceName), colors))
    return CubeColorScheme(faces, read_only=True)

