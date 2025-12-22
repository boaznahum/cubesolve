"""Color enumeration."""

from enum import Enum, unique


@unique
class Color(Enum):
    BLUE = "B"
    ORANGE = "O"
    YELLOW = "Y"
    GREEN = "G"
    RED = "R"
    WHITE = "W"
