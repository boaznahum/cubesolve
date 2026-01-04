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
        return self.value
