"""
Common types for the GUI abstraction layer.

This module defines backend-independent types used across all GUI protocols.
"""

from dataclasses import dataclass
from typing import TypeAlias, Tuple, NewType

import numpy as np
from numpy import ndarray

# Geometric types
Point3D: TypeAlias = ndarray  # Shape (3,) - [x, y, z]
Matrix4x4: TypeAlias = ndarray  # Shape (4, 4) column-major for OpenGL compatibility

# Color types (RGB/RGBA with values 0-255)
Color3: TypeAlias = Tuple[int, int, int]
Color4: TypeAlias = Tuple[int, int, int, int]

# Display list handle (opaque type for compiled rendering commands)
DisplayList = NewType("DisplayList", int)


@dataclass(frozen=True)
class KeyEvent:
    """Backend-independent keyboard event."""

    symbol: int  # Key code (use Keys constants)
    modifiers: int  # Modifier flags (use Modifiers constants)
    char: str | None = None  # Character if printable key


@dataclass(frozen=True)
class MouseEvent:
    """Backend-independent mouse event."""

    x: int  # X position in window coordinates
    y: int  # Y position in window coordinates
    dx: int = 0  # Delta X for drag events
    dy: int = 0  # Delta Y for drag events
    button: int = 0  # Mouse button (1=left, 2=middle, 3=right)
    modifiers: int = 0  # Modifier flags


class Keys:
    """Backend-independent key constants.

    These are abstract key codes that each backend maps to/from
    its native key codes.
    """

    # Letters (using ASCII-like values for convenience)
    A, B, C, D, E, F = 65, 66, 67, 68, 69, 70
    G, H, I, J, K, L = 71, 72, 73, 74, 75, 76
    M, N, O, P, Q, R = 77, 78, 79, 80, 81, 82
    S, T, U, V, W, X = 83, 84, 85, 86, 87, 88
    Y, Z = 89, 90

    # Numbers
    _0, _1, _2, _3, _4 = 48, 49, 50, 51, 52
    _5, _6, _7, _8, _9 = 53, 54, 55, 56, 57

    # Special keys
    ESCAPE = 256
    SPACE = 32
    RETURN = 257
    ENTER = 257  # Alias for RETURN
    TAB = 258
    BACKSPACE = 259
    DELETE = 260
    INSERT = 261

    # Arrow keys
    LEFT = 262
    RIGHT = 263
    UP = 264
    DOWN = 265

    # Function keys
    F1, F2, F3, F4 = 290, 291, 292, 293
    F5, F6, F7, F8 = 294, 295, 296, 297
    F9, F10, F11, F12 = 298, 299, 300, 301

    # Other common keys
    HOME = 268
    END = 269
    PAGE_UP = 270
    PAGE_DOWN = 271

    # Punctuation (commonly used in cube notation)
    SLASH = 47  # '/' - often used for solve command
    QUESTION = 47  # Same as slash (shift+/)
    APOSTROPHE = 39  # "'" - prime moves
    MINUS = 45
    PLUS = 43
    EQUAL = 61


class Modifiers:
    """Modifier key flags."""

    NONE = 0
    SHIFT = 1
    CTRL = 2
    ALT = 4
    META = 8  # Command on Mac, Windows key on PC


def make_point3d(x: float, y: float, z: float) -> Point3D:
    """Create a Point3D from coordinates."""
    return np.array([x, y, z], dtype=np.float32)


def make_identity_matrix() -> Matrix4x4:
    """Create a 4x4 identity matrix."""
    return np.eye(4, dtype=np.float32)


def make_translation_matrix(x: float, y: float, z: float) -> Matrix4x4:
    """Create a 4x4 translation matrix."""
    m = np.eye(4, dtype=np.float32)
    m[0, 3] = x
    m[1, 3] = y
    m[2, 3] = z
    return m


def make_rotation_matrix(angle_degrees: float, x: float, y: float, z: float) -> Matrix4x4:
    """Create a 4x4 rotation matrix around an arbitrary axis.

    Args:
        angle_degrees: Rotation angle in degrees
        x, y, z: Axis of rotation (will be normalized)

    Returns:
        4x4 rotation matrix
    """
    angle = np.radians(angle_degrees)
    c = np.cos(angle)
    s = np.sin(angle)

    # Normalize axis
    length = np.sqrt(x * x + y * y + z * z)
    if length == 0:
        return np.eye(4, dtype=np.float32)

    x, y, z = x / length, y / length, z / length

    # Rodrigues' rotation formula
    m = np.eye(4, dtype=np.float32)
    m[0, 0] = c + x * x * (1 - c)
    m[0, 1] = x * y * (1 - c) - z * s
    m[0, 2] = x * z * (1 - c) + y * s
    m[1, 0] = y * x * (1 - c) + z * s
    m[1, 1] = c + y * y * (1 - c)
    m[1, 2] = y * z * (1 - c) - x * s
    m[2, 0] = z * x * (1 - c) - y * s
    m[2, 1] = z * y * (1 - c) + x * s
    m[2, 2] = c + z * z * (1 - c)

    return m
