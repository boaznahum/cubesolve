"""Color enumeration."""

from __future__ import annotations

from enum import Enum, unique

import matplotlib.colors as mplcolors


# https://matplotlib.org/stable/gallery/color/named_colors.html#
# import matplotlibmpl

# list(mpl.colors.BASE_COLORS) -> ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
# list(mpl.colors.CSS4_COLORS) -> 'aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige', 'bisque', 'black', 'blanchedalmond' ...
# list(mpl.colors.TABLEAU_COLORS)
# list(mpl.colors.XKCD_COLORS) --> 949 colors
# all colors
#  mpl.get_named_colors_mapping()

# https://matplotlib.org/stable/users/explain/colors/colors.html
# API https://matplotlib.org/stable/api/colors_api.html#
#
# Getting color - see above:
# mpl.colors.CSS4_COLORS["blue"] -> '#0000FF'
# mpl.colors.to_rgb(mpl.colors.CSS4_COLORS["blue"])

# RGB - float
# mpl.colors.to_rgb(mpl.colors.get_named_colors_mapping()["white"]) -> (1.0, 1.0, 1.0)


@unique
class Color(Enum):
    """Cube face/sticker colors.

    Color names are resolved to RGB via matplotlib (see ``_n2c``).
    Browse available names: https://matplotlib.org/stable/gallery/color/named_colors.html

    **Lighting wash-out:** Pastel/light colors (where ALL RGB channels are high,
    roughly > 0.6) will wash out to white under Phong lighting when a face
    directly faces the light source, because ambient + diffuse pushes every
    channel past 1.0 simultaneously. Prefer saturated colors (at least one
    channel near 0) for distinguishable cube faces.

    When adding a new color, update:
    - ``TEXT_RICH_COLORS`` (Rich console output)
    - ``ConsoleViewer._color_2_str`` (console backend)
    """
    BLUE = "Bl"
    ORANGE = "Or"
    YELLOW = "Yl"
    GREEN = "Gr"
    RED = "Re"
    WHITE = "Wh"
    PURPLE = "Pur"
    PINK = "Pnk"
    PALE_LILAC = "lilac"
    LIGHT_SEAFOAM_GREEN = "lsgrn"
    LIGHTISH_PURPLE = "LPnk"
    ELECTRIC_PINK = "EPnk"

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
    def long(self) -> str:
        """The long-form name of this color (e.g. Color.BLUE → ColorLong.BLUE)."""
        return self.name.capitalize()

# class ColorLong(Enum):
#     BLUE = "Blue"
#     ORANGE = "Orange"
#     YELLOW = "Yellow"
#     GREEN = "Green"
#     RED = "Red"
#     WHITE = "White"
#     PURPLE = "Purple"
#     PINK = "Pink"

# _COLOR_2_LONG: dict[Color, ColorLong] = {
#     Color.BLUE: ColorLong.BLUE,
#     Color.ORANGE: ColorLong.ORANGE,
#     Color.YELLOW: ColorLong.YELLOW,
#     Color.GREEN: ColorLong.GREEN,
#     Color.RED: ColorLong.RED,
#     Color.WHITE: ColorLong.WHITE,
#     Color.PURPLE: ColorLong.PURPLE,
#     Color.PINK: ColorLong.PINK,
# }


# =============================================================================
# Color Mapping
# =============================================================================
# Cube face colors: Color enum -> RGB (0.0-1.0 normalized)
# These colors match the standard Rubik's cube color scheme.

def _i2f(r, g, b):
    return r / 255, g /255, b / 255

def _f2i(rgb: tuple[float, float, float]) -> tuple[int, int, int]:
    return int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] *255)

def _n2c(n: str) -> tuple[float, float, float]:
    """Map a color name to an RGB float tuple via matplotlib.

    Lookup order: CSS4 named colors → XKCD survey colors (prefixed "xkcd:").

    NOTE: matplotlib color names may differ from intuitive expectations.
    For example, "pink" maps to pastel CSS #FFC0CB (1.0, 0.75, 0.80),
    NOT hot-pink #FF69B4 (1.0, 0.41, 0.71). Light/pastel colors can
    wash out to white under Phong lighting at direct angles because
    ambient + diffuse exceeds 1.0 on all channels.
    """
    _n = n.lower().replace("_", " ")
    mapping = mplcolors.get_named_colors_mapping()

    if _n not in mapping:
        _n = "xkcd:" + _n

    return mplcolors.to_rgb(mapping[_n])

_COLOR_TO_RGB_FLOAT: dict[Color, tuple[float, float, float]] = { c : _n2c(c.name) for c in Color }

 #_COLOR_TO_RGB_FLOAT: dict[Color, tuple[float, float, float]] = {
#     Color.BLUE: _n2c("blue"),
#     Color.ORANGE: _n2c("orange"),
#     Color.YELLOW: _n2c("yellow"),
#     Color.GREEN: _n2c("green"),
#     Color.RED: _n2c("red"),
#     Color.WHITE: _n2c("white"),
#     Color.PINK: _n2c("pink"),
#
#     # https://www.rapidtables.com/web/color/purple-color.html
#     Color.PURPLE: _n2c("purple"),
#
# }

_COLOR_TO_RGB_INT: dict[Color, tuple[int, int, int]] = { c : _f2i(_COLOR_TO_RGB_FLOAT[c]) for c in Color }

__COLOR_TO_RGB_FLOAT: dict[Color, tuple[float, float, float]] = { c : _i2f(*_COLOR_TO_RGB_INT[c]) for c in Color }

def color2rgb_int(col: Color) -> tuple[int, int, int]:
    return _COLOR_TO_RGB_INT[col]

def color2rgb_float(col: Color) -> tuple[float, float, float]:
    return _COLOR_TO_RGB_FLOAT[col]


def complementary_color(r: float, g: float, b: float) -> tuple[float, float, float]:
    """Compute the complementary (inverted) color.

    Args:
        r, g, b: RGB values in 0.0-1.0 range.

    Returns:
        (1-r, 1-g, 1-b) — the RGB complement.
    """
    return (1.0 - r, 1.0 - g, 1.0 - b)


def color2complementary_float(col: Color) -> tuple[float, float, float]:
    """Get the complementary color for a Color enum member.

    Args:
        col: A Color enum value.

    Returns:
        RGB complement as floats in 0.0-1.0 range.
    """
    r, g, b = _COLOR_TO_RGB_FLOAT[col]
    return complementary_color(r, g, b)


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
