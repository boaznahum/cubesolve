"""
Modern GL Constants - Named constants for cube geometry and rendering.

This module centralizes all magic numbers with clear documentation.

Coordinate System (OpenGL right-handed):
    +Y (Up)
    |
    |   +Z (Front, toward viewer)
    |  /
    | /
    +------ +X (Right)

The cube is centered at the origin with faces at distance HALF_CUBE_SIZE.
"""
from __future__ import annotations

from cube.domain.model.cube_boy import Color, FaceName

# =============================================================================
# Cube Geometry Constants
# =============================================================================

# The cube is centered at origin, spanning [-HALF_CUBE_SIZE, +HALF_CUBE_SIZE]
# on each axis. Each face center is at distance HALF_CUBE_SIZE from origin.
HALF_CUBE_SIZE = 50.0

# Full size of one face (edge to edge)
FACE_SIZE = HALF_CUBE_SIZE * 2  # 100.0

# =============================================================================
# Cell Rendering Constants
# =============================================================================

# Gap between cells as a ratio of cell size (creates the grid line effect)
# 0.02 = 2% gap, so cells are 96% filled with 4% total gap
CELL_GAP_RATIO = 0.02

# Black border line width around each cell (in pixels/units)
BORDER_LINE_WIDTH = 4.0

# =============================================================================
# Shadow Face Offsets
# =============================================================================
# When shadow mode is enabled (F10/F11/F12), we render duplicate faces
# at offset positions so they're visible in the default isometric view.
#
# Offsets are in face-size units (multiply by FACE_SIZE to get world coords):
#   L (Left):  -0.75 = 75% of face width to the left
#   D (Down):  -0.50 = 50% of face height below
#   B (Back):  -2.00 = 2 face depths behind

SHADOW_OFFSET_L = -0.75  # Left face shadow: offset in -X direction
SHADOW_OFFSET_D = -0.50  # Down face shadow: offset in -Y direction
SHADOW_OFFSET_B = -2.00  # Back face shadow: offset in -Z direction

# Pre-computed shadow offsets in world coordinates
SHADOW_OFFSETS: dict[FaceName, tuple[float, float, float]] = {
    FaceName.L: (SHADOW_OFFSET_L * FACE_SIZE, 0, 0),
    FaceName.D: (0, SHADOW_OFFSET_D * FACE_SIZE, 0),
    FaceName.B: (0, 0, SHADOW_OFFSET_B * FACE_SIZE),
}

# =============================================================================
# Color Mapping
# =============================================================================
# Cube face colors: Color enum -> RGB (0.0-1.0 normalized)
# These colors match the standard Rubik's cube color scheme.

COLOR_TO_RGB: dict[Color, tuple[float, float, float]] = {
    Color.WHITE:  (1.0, 1.0, 1.0),      # Up face
    Color.YELLOW: (1.0, 0.84, 0.0),     # Down face (golden yellow)
    Color.GREEN:  (0.0, 0.61, 0.28),    # Front face (dark green)
    Color.BLUE:   (0.0, 0.27, 0.68),    # Back face (dark blue)
    Color.RED:    (0.72, 0.07, 0.20),   # Right face (dark red)
    Color.ORANGE: (1.0, 0.35, 0.0),     # Left face
}

# Reverse mapping for texture grouping
RGB_TO_COLOR: dict[tuple[float, float, float], Color] = {
    v: k for k, v in COLOR_TO_RGB.items()
}

# =============================================================================
# Color to Home Face Mapping (for textures)
# =============================================================================
# Each color belongs to a "home" face. When textures are enabled,
# cells are grouped by their COLOR (not current face) so the texture
# "sticks" to the piece as it moves around the cube.

COLOR_TO_HOME_FACE: dict[Color, FaceName] = {
    Color.GREEN:  FaceName.F,   # Green = Front
    Color.BLUE:   FaceName.B,   # Blue = Back
    Color.RED:    FaceName.R,   # Red = Right
    Color.ORANGE: FaceName.L,   # Orange = Left
    Color.WHITE:  FaceName.U,   # White = Up
    Color.YELLOW: FaceName.D,   # Yellow = Down
}

# =============================================================================
# Face Transforms
# =============================================================================
# Each face is defined by:
#   - center: Position of face center in world space
#   - right: Direction vector for "right" on this face
#   - up: Direction vector for "up" on this face
#
# The normal (outward direction) is computed as cross(right, up).
#
# Face Layout (looking at the cube from default view):
#
#        +-------+
#        |   U   |
#        |  +Y   |
#    +---+---+---+---+
#    | L | F | R | B |
#    |-X |+Z |+X |-Z |
#    +---+---+---+---+
#        |   D   |
#        |  -Y   |
#        +-------+

FACE_TRANSFORMS: dict[FaceName, tuple[
    tuple[float, float, float],  # center
    tuple[float, float, float],  # right direction
    tuple[float, float, float],  # up direction
]] = {
    # Front face: at +Z, normal points toward viewer
    #   Right = +X, Up = +Y
    FaceName.F: (
        (0, 0, HALF_CUBE_SIZE),   # center at z=+50
        (1, 0, 0),                # right is +X
        (0, 1, 0),                # up is +Y
    ),

    # Back face: at -Z, normal points away from viewer
    #   Right = -X (mirrored), Up = +Y
    FaceName.B: (
        (0, 0, -HALF_CUBE_SIZE),  # center at z=-50
        (-1, 0, 0),               # right is -X (mirrored)
        (0, 1, 0),                # up is +Y
    ),

    # Right face: at +X, normal points right
    #   Right = -Z (into screen), Up = +Y
    FaceName.R: (
        (HALF_CUBE_SIZE, 0, 0),   # center at x=+50
        (0, 0, -1),               # right is -Z
        (0, 1, 0),                # up is +Y
    ),

    # Left face: at -X, normal points left
    #   Right = +Z (out of screen), Up = +Y
    FaceName.L: (
        (-HALF_CUBE_SIZE, 0, 0),  # center at x=-50
        (0, 0, 1),                # right is +Z
        (0, 1, 0),                # up is +Y
    ),

    # Up face: at +Y, normal points up
    #   Right = +X, Up = -Z (away from viewer)
    FaceName.U: (
        (0, HALF_CUBE_SIZE, 0),   # center at y=+50
        (1, 0, 0),                # right is +X
        (0, 0, -1),               # up is -Z
    ),

    # Down face: at -Y, normal points down
    #   Right = +X, Up = +Z (toward viewer)
    FaceName.D: (
        (0, -HALF_CUBE_SIZE, 0),  # center at y=-50
        (1, 0, 0),                # right is +X
        (0, 0, 1),                # up is +Z
    ),
}
