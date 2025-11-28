"""
Keyboard key constants for GUI tests.

This module defines all keyboard key sequences used by GUI tests.
Use these constants in tests to avoid hardcoding key sequences.
"""


class GUIKeys:
    """GUI keyboard key constants for test sequences."""

    # Face rotations (lowercase in GUI)
    R = "r"  # Right face
    L = "l"  # Left face
    U = "u"  # Up face
    F = "f"  # Front face
    B = "b"  # Back face
    D = "d"  # Down face

    # Scramble keys
    SCRAMBLE_1 = "1"  # Scramble with seed 1
    SCRAMBLE_2 = "2"  # Scramble with seed 2
    SCRAMBLE_3 = "3"  # Scramble with seed 3
    SCRAMBLE_4 = "4"  # Scramble with seed 4
    SCRAMBLE_5 = "5"  # Scramble with seed 5
    SCRAMBLE_6 = "6"  # Scramble with seed 6

    # Operations
    SOLVE = "/"  # Solve the cube (SLASH key)
    QUIT = "q"  # Quit application

    # Animation speed control (Numpad +/-)
    SPEED_UP = "+"  # Increase animation speed (NUM_ADD)
    SPEED_DOWN = "-"  # Decrease animation speed (NUM_SUBTRACT)
