# Re-exports for backward compatibility
from .FaceName import FaceName
from .Color import Color
from .ColorLong import ColorLong
from .CubeLayout import CubeLayout

# Helper function and mapping
_color2long = {
    Color.BLUE: ColorLong.BLUE,
    Color.ORANGE: ColorLong.ORANGE,
    Color.YELLOW: ColorLong.YELLOW,
    Color.GREEN: ColorLong.GREEN,
    Color.RED: ColorLong.RED,
    Color.WHITE: ColorLong.WHITE,
}


def color2long(c: Color) -> ColorLong:
    return _color2long[c]


__all__ = [
    'FaceName',
    'Color',
    'ColorLong',
    'CubeLayout',
    'color2long',
]
