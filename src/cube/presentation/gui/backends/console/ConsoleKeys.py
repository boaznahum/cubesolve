"""
Keyboard key constants for the console application.

This module defines all keyboard keys used by main_c.py.
Use these constants in both the keyboard handler and tests.
"""


class Keys:
    """Console keyboard key constants."""

    # Face rotations
    R = "R"  # Right face
    L = "L"  # Left face
    U = "U"  # Up face
    F = "F"  # Front face
    B = "B"  # Back face
    D = "D"  # Down face

    # Whole cube rotations
    X = "X"  # Rotate on R axis
    Y = "Y"  # Rotate on U axis

    # Slice moves
    M = "M"  # Middle slice

    # Modifiers
    INV = "'"  # Toggle inverse mode (prime)
    WIDE = "W"  # Toggle wide mode (lowercase moves like r, f, u)

    # Scramble
    SCRAMBLE_RANDOM = "0"  # Random scramble
    SCRAMBLE_1 = "1"  # Scramble with seed 1
    SCRAMBLE_2 = "2"  # Scramble with seed 2
    SCRAMBLE_3 = "3"  # Scramble with seed 3
    SCRAMBLE_4 = "4"  # Scramble with seed 4
    SCRAMBLE_5 = "5"  # Scramble with seed 5
    SCRAMBLE_6 = "6"  # Scramble with seed 6

    # Operations
    SOLVE = "?"  # Solve the cube
    UNDO = "<"  # Undo last move
    CLEAR = "C"  # Clear/reset cube
    ALGS = "A"  # Enter algorithm input mode
    STATUS = "S"  # Show detailed part status
    TEST = "T"  # Run test (50 scramble-solve cycles)
    HELP = "H"  # Show help

    # Control
    QUIT = "Q"  # Quit application
    CTRL_C = "\x03"  # Ctrl+C (alternative quit)

    @classmethod
    def scramble_seed(cls, seed: int) -> str:
        """Get the scramble key for a given seed (1-6)."""
        if 1 <= seed <= 6:
            return str(seed)
        raise ValueError(f"Seed must be 1-6, got {seed}")

    @classmethod
    def all_face_rotations(cls) -> str:
        """Return all face rotation keys as a string."""
        return cls.R + cls.L + cls.U + cls.F + cls.B + cls.D
