"""Face name enumeration."""

from enum import Enum, unique


@unique
class FaceName(Enum):
    U = "U"
    D = "D"
    F = "F"
    B = "B"
    L = "L"
    R = "R"

    def __str__(self):
        return self.value
