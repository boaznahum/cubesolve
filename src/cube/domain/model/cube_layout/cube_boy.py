"""
BOY (Blue-Orange-Yellow) Color Scheme - Single Source of Truth.

This module defines the GLOBAL REFERENCE for the standard Rubik's cube color scheme.
All code that needs to know "what colors go where on a solved cube" MUST use this module.

BOY Color Scheme (standard Western color scheme):
    - Front (F): Blue
    - Right (R): Red
    - Up (U): Yellow
    - Left (L): Orange
    - Down (D): White
    - Back (B): Green

The name "BOY" comes from: Blue-Orange-Yellow on the Front-Left-Up corner.

Usage:
    from cube.domain.model import cube_boy

    # Get the global BOY layout instance
    boy = cube_boy.get_boy_layout(sp)

    # Access colors via indexing
    front_color = boy[FaceName.F]  # Color.BLUE

    # Check if a layout matches BOY (preferred method)
    is_boy = some_layout.is_boy()

    # Get opposite faces (via CubeLayout)
    opposite = CubeLayout.opposite(FaceName.F)  # FaceName.B

Important:
    - get_boy_layout() returns a CACHED SINGLETON - same instance every time
    - The layout is READ-ONLY (cannot be modified)
    - To change the color scheme, modify ONLY this file
    - All other code should use get_boy_layout(), never hardcode colors

Consumers:
    - Cube._reset(): Uses boy layout to set initial face colors
    - Cube.is_boy: Compares current layout against boy layout
    - Cube3x3Colors.is_boy(): Compares extracted colors against boy layout
    - CageNxNSolver: Asserts shadow cube maintains BOY layout
"""

from cube.utils.config_protocol import IServiceProvider

from cube.domain.model.Color import Color
from cube.domain.model.ColorLong import ColorLong
from cube.domain.model.cube_layout.CubeLayout import CubeLayout
from cube.domain.model.FaceName import FaceName

# ============================================================================
# BOY Layout - Global Cached Singleton
# ============================================================================

_boy_layout: CubeLayout | None = None


def get_boy_layout(sp: IServiceProvider) -> CubeLayout:
    """Get the global BOY layout instance (cached singleton).

    This is the SINGLE SOURCE OF TRUTH for the standard cube color scheme.
    BOY = Blue-Orange-Yellow (the Front-Left-Up corner colors).

    UNFOLDED CUBE LAYOUT:
    ====================
                ┌───────┐
                │   Y   │
                │   U   │  Yellow (Up)
                │       │
        ┌───────┼───────┼───────┬───────┐
        │   O   │   B   │   R   │   G   │
        │   L   │   F   │   R   │   B   │
        │       │       │       │       │
        └───────┼───────┼───────┴───────┘
                │   W   │
                │   D   │  White (Down)
                │       │
                └───────┘

    FACE COLORS:
        Front=Blue, Right=Red, Up=Yellow, Left=Orange, Down=White, Back=Green

    OPPOSITE FACES:
        F (Blue)   <-> B (Green)
        U (Yellow) <-> D (White)
        L (Orange) <-> R (Red)

    ADJACENT COLORS (clockwise around Up face):
        Front=Blue -> Right=Red -> Back=Green -> Left=Orange

    Args:
        sp: Service provider for configuration access.

    Returns:
        The global BOY CubeLayout instance (same instance on every call).

    Example:
        boy = get_boy_layout(sp)
        front_color = boy[FaceName.F]  # Color.BLUE
        is_match = some_layout.is_boy()  # Preferred way to check BOY
    """
    global _boy_layout
    if _boy_layout is None:
        _boy_layout = CubeLayout(True, {
            FaceName.F: Color.BLUE,
            FaceName.R: Color.RED,
            FaceName.U: Color.YELLOW,
            FaceName.L: Color.ORANGE,
            FaceName.D: Color.WHITE,
            FaceName.B: Color.GREEN,
        }, sp)
    return _boy_layout


# ============================================================================
# Color Conversion Utilities
# ============================================================================

_color2long: dict[Color, ColorLong] = {
    Color.BLUE: ColorLong.BLUE,
    Color.ORANGE: ColorLong.ORANGE,
    Color.YELLOW: ColorLong.YELLOW,
    Color.GREEN: ColorLong.GREEN,
    Color.RED: ColorLong.RED,
    Color.WHITE: ColorLong.WHITE,
}


def color2long(c: Color) -> ColorLong:
    """Convert a Color enum to its ColorLong equivalent."""
    return _color2long[c]


# ============================================================================
# Re-exports for backward compatibility
# ============================================================================

__all__ = [
    'FaceName',
    'Color',
    'ColorLong',
    'CubeLayout',
    'get_boy_layout',
    'color2long',
]
