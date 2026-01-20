"""Color enumeration."""

from enum import Enum, unique


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
