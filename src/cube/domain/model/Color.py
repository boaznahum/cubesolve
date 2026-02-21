"""Color enumeration."""

from __future__ import annotations

from enum import Enum, unique

from cube.domain.model.ColorLong import ColorLong


@unique
class Color(Enum):
    BLUE = "Bl"
    ORANGE = "Or"
    YELLOW = "Yl"
    GREEN = "Gr"
    RED = "Re"
    WHITE = "Wh"

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


#claude: why we need this enum ?
_COLOR_2_LONG: dict[Color, ColorLong] = {
    Color.BLUE: ColorLong.BLUE,
    Color.ORANGE: ColorLong.ORANGE,
    Color.YELLOW: ColorLong.YELLOW,
    Color.GREEN: ColorLong.GREEN,
    Color.RED: ColorLong.RED,
    Color.WHITE: ColorLong.WHITE,
}


def color2long(c: Color) -> ColorLong:
    """Convert a Color enum to its ColorLong equivalent."""
    return _COLOR_2_LONG[c]
