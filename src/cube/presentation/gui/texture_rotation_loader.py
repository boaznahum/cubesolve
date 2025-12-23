"""
Texture Rotation Delta Table

Defines how texture_direction changes when faces/slices rotate.
These values were determined experimentally and are now fixed constants.

When face/slice X rotates CW, the delta is added to affected stickers' texture_direction.
0 = no update, 1/2/3 = add that amount (mod 4)
"""
from __future__ import annotations

# Texture rotation deltas - determined experimentally, now constants
# Format: {rotating_element: {target_face: delta, ...}, ...}
_TEXTURE_DELTAS: dict[str, dict[str, int]] = {
    # Face rotations
    'F': {'self': 1, 'U': 1, 'R': 1, 'D': 1, 'L': 1},
    'R': {'self': 1, 'U': 0, 'B': 2, 'D': 2, 'F': 0},
    'U': {'self': 1, 'B': 0, 'R': 0, 'F': 0, 'L': 0},
    'D': {'self': 1, 'F': 0, 'R': 0, 'B': 0, 'L': 0},
    'L': {'self': 1, 'U': 2, 'F': 0, 'D': 0, 'B': 2},
    'B': {'self': 1, 'U': 3, 'L': 3, 'D': 3, 'R': 3},
    # Slice rotations
    'M': {'F': 0, 'U': 2, 'B': 2, 'D': 0},
    'E': {'F': 0, 'R': 0, 'B': 0, 'L': 0},
    'S': {'U': 3, 'R': 3, 'D': 3, 'L': 3},
}


def get_delta(rotating_face: str, target: str) -> int:
    """Get delta to add to texture_direction.

    Args:
        rotating_face: The rotating face ('F', 'R', etc.) or slice ('M', 'E', 'S')
        target: 'self' or adjacent face name ('U', 'R', etc.)

    Returns:
        Delta value (0 = no update, 1/2/3 = add that amount)
    """
    face_config = _TEXTURE_DELTAS.get(rotating_face, {})
    return face_config.get(target, 0)
