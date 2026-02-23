"""Name and position enums for cube parts: edges, corners, and their positions on faces.

These are pure value enums with no domain logic. They identify:
  - EdgeName: the 12 edges (FU, FL, FR, ...)
  - CornerName: the 8 corners (FLU, FRU, ...)
  - EdgePosition: edge slot on a face (TOP, RIGHT, BOTTOM, LEFT)
  - CornerPosition: corner slot on a face (TOP_LEFT, TOP_RIGHT, ...)
"""

from enum import Enum, unique


class EdgeName(Enum):
    FL = "FL"
    FU = "FU"
    FR = "FR"
    FD = "FD"
    BL = "BL"
    BU = "BU"
    BR = "BR"
    BD = "BD"
    UR = "UR"
    RD = "RD"
    DL = "DL"
    LU = "LU"

    def __str__(self) -> str:
        return str(self.value)


@unique
class CornerName(Enum):
    FLU = "FLU"
    FRU = "FRU"
    FRD = "FRD"
    FLD = "FLD"
    BLU = "BLU"
    BRU = "BRU"
    BRD = "BRD"
    BLD = "BLD"

    def __str__(self) -> str:
        return str(self.value)


@unique
class EdgePosition(Enum):
    """Position of an edge relative to a face (when viewing the face from outside the cube).

    Used to get the edge at a specific position on a face via Face.get_edge().
    """
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name


@unique
class CornerPosition(Enum):
    """Position of a corner relative to a face (viewing from outside the cube)."""
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_RIGHT = "bottom_right"
    BOTTOM_LEFT = "bottom_left"

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name
