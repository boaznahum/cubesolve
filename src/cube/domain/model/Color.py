"""Color enumeration."""

from __future__ import annotations

from enum import Enum, unique



@unique
class Color(Enum):
    """"
    When you add color, need also to add in:
    cube.domain.model.Color.ColorLong
    cube.presentation.gui.backends.console.ConsoleViewer._color_2_str # not all available !!!
    In this file  COLOR_TO_RGB , notbelong to model

    #claude why COLOR_TO_HOME_FACE is never used, or a tleas doesnt fails , no such color
    src/cube/presentation/gui/backends/pyglet2/_modern_gl_constants.py:95 COLOR_TO_HOME_FACENEED TOGET RID, USE CUBE SCHEMA


    cube.presentation.viewer._cell._color_2_v_color # claude: what is this, why it never fails ?
    src/cube/presentation/viewer/_cell.py:44 _COMPLEMENTARY_MAP_FLOAT WHAT THE FUCK IS IT ? why it never fails
    src/cube/utils/text_cube_viewer.py:49  _RICH_COLORS WHY WE NEED THIS
    """
    BLUE = "Bl"
    ORANGE = "Or"
    YELLOW = "Yl"
    GREEN = "Gr"
    RED = "Re"
    WHITE = "Wh"
    PURPLE = "Pur"
    PINK = "Pnk"

    def __str__(self) -> str:
        return self.name ## see below

    def __repr__(self) -> str:
        """Return just the enum name (e.g., 'GREEN' not '<Color.GREEN: Gr>').

        This is needed because containers (list, set, frozenset, dict) use __repr__
        for their elements, not __str__. Without this, printing a frozenset of colors
        would show: frozenset({<Color.GREEN: 'Gr'>, <Color.RED: 'Re'>})
        With this, it shows: frozenset({GREEN, RED})
        """
        return self.name

    @property
    def long(self) -> ColorLong:
        """The long-form name of this color (e.g. Color.BLUE → ColorLong.BLUE)."""
        return _COLOR_2_LONG[self]

class ColorLong(Enum):
    BLUE = "Blue"
    ORANGE = "Orange"
    YELLOW = "Yellow"
    GREEN = "Green"
    RED = "Red"
    WHITE = "White"
    PURPLE = "Purple"
    PINK = "Pink"

#claude: why we need this enum ?
_COLOR_2_LONG: dict[Color, ColorLong] = {
    Color.BLUE: ColorLong.BLUE,
    Color.ORANGE: ColorLong.ORANGE,
    Color.YELLOW: ColorLong.YELLOW,
    Color.GREEN: ColorLong.GREEN,
    Color.RED: ColorLong.RED,
    Color.WHITE: ColorLong.WHITE,
    Color.PURPLE: ColorLong.PURPLE,
    Color.PINK: ColorLong.PINK,
}


#Claude: not belong to model !!!
# =============================================================================
# Color Mapping
# =============================================================================
# Cube face colors: Color enum -> RGB (0.0-1.0 normalized)
# These colors match the standard Rubik's cube color scheme.

def _i2f(r, g, b):
    return r / 255, g /255, b / 255


_COLOR_TO_RGB_INT: dict[Color, tuple[int, int, int]] = {
    Color.BLUE: (0, 0, 255),
    Color.ORANGE: (255, 69, 0),  # (255,127,80) # (255, 165, 0)
    Color.YELLOW: (255, 255, 0),
    Color.GREEN: (0, 255, 0),
    Color.RED: (255, 0, 0),
    Color.WHITE: (255, 255, 255),
    Color.PINK: (255, 105, 180),

    # https://www.rapidtables.com/web/color/purple-color.html
    Color.PURPLE: (138, 43, 226),

}

_COLOR_TO_RGB_FLOAT: dict[Color, tuple[float, float, float]] = { c : _i2f(*_COLOR_TO_RGB_INT[c]) for c in Color }

def color2rgb_int(col: Color) -> tuple[int, int, int]:
    return _COLOR_TO_RGB_INT[col]

def color2rgb_float(col: Color) -> tuple[float, float, float]:
    return _COLOR_TO_RGB_FLOAT[col]


# Rich color mappings for text viewer
TEXT_RICH_COLORS: dict[Color, str] = {
    Color.WHITE: "white",
    Color.YELLOW: "yellow",
    Color.GREEN: "green",
    Color.BLUE: "blue",
    Color.RED: "red",
    Color.ORANGE: "bright_magenta",  # Rich has no orange, use magenta
    Color.PINK: "pink", # not supported
    Color.PURPLE: "purple",  # not supported
}
