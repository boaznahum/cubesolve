"""
Common types for the GUI abstraction layer.

This module defines backend-independent types used across all GUI protocols.
"""

from typing import NewType, Tuple, TypeAlias

import numpy as np
from numpy import ndarray

# Re-export classes from split files
from .KeyEvent import KeyEvent
from .Keys import Keys
from .Modifiers import Modifiers
from .MouseButton import MouseButton
from .MouseEvent import MouseEvent
from .TextureCoord import TextureCoord

# Geometric types
Point3D: TypeAlias = ndarray  # Shape (3,) - [x, y, z]
Matrix4x4: TypeAlias = ndarray  # Shape (4, 4) column-major for OpenGL compatibility

# Color types (RGB/RGBA with values 0-255)
Color3: TypeAlias = Tuple[int, int, int]
Color4: TypeAlias = Tuple[int, int, int, int]

# Display list handle (opaque type for compiled rendering commands)
DisplayList = NewType("DisplayList", int)

# Texture handle (opaque type for loaded textures)
TextureHandle = NewType("TextureHandle", int)

# Texture map is a sequence of UV coordinates for each vertex
TextureMap: TypeAlias = Tuple[TextureCoord, TextureCoord, TextureCoord, TextureCoord]


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


# Key sequence helpers for testing

def make_key_event(symbol: int, modifiers: int = 0, char: str | None = None) -> KeyEvent:
    """Create a KeyEvent with the given parameters.

    Args:
        symbol: Key code from Keys class
        modifiers: Modifier flags from Modifiers class (default: no modifiers)
        char: Character if printable key

    Returns:
        KeyEvent instance
    """
    return KeyEvent(symbol=symbol, modifiers=modifiers, char=char)


def make_key_sequence(*keys: int | tuple[int, int]) -> list[KeyEvent]:
    """Create a sequence of KeyEvents from key symbols.

    Each argument can be:
    - A single key code (int): Creates event with no modifiers
    - A tuple (key_code, modifiers): Creates event with specified modifiers

    Args:
        *keys: Variable number of key codes or (key_code, modifiers) tuples

    Returns:
        List of KeyEvent objects

    Example:
        # Simple sequence: R, L, U
        seq = make_key_sequence(Keys.R, Keys.L, Keys.U)

        # With modifiers: R, Shift+L, Ctrl+U
        seq = make_key_sequence(
            Keys.R,
            (Keys.L, Modifiers.SHIFT),
            (Keys.U, Modifiers.CTRL)
        )
    """
    events = []
    for key in keys:
        if isinstance(key, tuple):
            symbol, modifiers = key
            events.append(KeyEvent(symbol=symbol, modifiers=modifiers))
        else:
            events.append(KeyEvent(symbol=key, modifiers=0))
    return events


# Mapping from single characters to key symbols for convenience
_CHAR_TO_KEY: dict[str, int] = {
    'A': Keys.A, 'B': Keys.B, 'C': Keys.C, 'D': Keys.D, 'E': Keys.E, 'F': Keys.F,
    'G': Keys.G, 'H': Keys.H, 'I': Keys.I, 'J': Keys.J, 'K': Keys.K, 'L': Keys.L,
    'M': Keys.M, 'N': Keys.N, 'O': Keys.O, 'P': Keys.P, 'Q': Keys.Q, 'R': Keys.R,
    'S': Keys.S, 'T': Keys.T, 'U': Keys.U, 'V': Keys.V, 'W': Keys.W, 'X': Keys.X,
    'Y': Keys.Y, 'Z': Keys.Z,
    'a': Keys.A, 'b': Keys.B, 'c': Keys.C, 'd': Keys.D, 'e': Keys.E, 'f': Keys.F,
    'g': Keys.G, 'h': Keys.H, 'i': Keys.I, 'j': Keys.J, 'k': Keys.K, 'l': Keys.L,
    'm': Keys.M, 'n': Keys.N, 'o': Keys.O, 'p': Keys.P, 'q': Keys.Q, 'r': Keys.R,
    's': Keys.S, 't': Keys.T, 'u': Keys.U, 'v': Keys.V, 'w': Keys.W, 'x': Keys.X,
    'y': Keys.Y, 'z': Keys.Z,
    '0': Keys._0, '1': Keys._1, '2': Keys._2, '3': Keys._3, '4': Keys._4,
    '5': Keys._5, '6': Keys._6, '7': Keys._7, '8': Keys._8, '9': Keys._9,
    ' ': Keys.SPACE, '/': Keys.SLASH, "'": Keys.APOSTROPHE,
}


def parse_key_string(key_string: str, uppercase_is_shift: bool = False) -> list[KeyEvent]:
    """Parse a string of key characters into KeyEvents.

    This is a convenience function for creating key sequences from strings.
    Each character maps to its corresponding key.

    Args:
        key_string: String of characters to convert to key events
        uppercase_is_shift: If True, uppercase letters add SHIFT modifier.
            Default False (cube notation style where R = R move).

    Returns:
        List of KeyEvent objects

    Example:
        # Cube notation: R L U (all normal moves)
        seq = parse_key_string("RLU")

        # With shift simulation (keyboard style)
        seq = parse_key_string("RLU", uppercase_is_shift=True)
    """
    events = []
    for char in key_string:
        if char in _CHAR_TO_KEY:
            symbol = _CHAR_TO_KEY[char]
            modifiers = Modifiers.NONE
            if uppercase_is_shift and char.isupper():
                modifiers = Modifiers.SHIFT
            events.append(KeyEvent(symbol=symbol, modifiers=modifiers, char=char))
    return events


__all__ = [
    # Classes
    'KeyEvent',
    'MouseEvent',
    'Keys',
    'Modifiers',
    'MouseButton',
    'TextureCoord',
    # Type aliases
    'Point3D',
    'Matrix4x4',
    'Color3',
    'Color4',
    'DisplayList',
    'TextureHandle',
    'TextureMap',
    # Functions
    'make_point3d',
    'make_identity_matrix',
    'make_translation_matrix',
    'make_rotation_matrix',
    'make_key_event',
    'make_key_sequence',
    'parse_key_string',
]
