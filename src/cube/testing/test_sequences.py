"""
Abstract test sequences for backend-agnostic testing.

This module defines standard key sequences that work across all backends.
Use these instead of backend-specific key codes.
"""

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class TestSequence:
    """A named test sequence.

    Attributes:
        name: Human-readable name for the sequence.
        keys: Key sequence string.
        description: What the sequence does.
        expected_timeout: Expected execution time in seconds.
    """
    name: str
    keys: str
    description: str
    expected_timeout: float = 30.0


class TestSequences:
    """Standard test sequences for all backends.

    These sequences use character-based key mappings that work with
    all backends via inject_key_sequence().

    Usage:
        # Get a predefined sequence
        seq = TestSequences.SCRAMBLE_AND_SOLVE

        # Use in tests
        window.inject_key_sequence(seq.keys)

        # Or just the keys string
        window.inject_key_sequence(TestSequences.scramble_solve_quit())
    """

    # Face rotation keys (work in all backends)
    R: ClassVar[str] = "r"  # Right face
    L: ClassVar[str] = "l"  # Left face
    U: ClassVar[str] = "u"  # Up face
    D: ClassVar[str] = "d"  # Down face
    F: ClassVar[str] = "f"  # Front face
    B: ClassVar[str] = "b"  # Back face

    # Scramble keys
    SCRAMBLE_RANDOM: ClassVar[str] = "0"  # Random scramble
    SCRAMBLE_1: ClassVar[str] = "1"  # Seed 1
    SCRAMBLE_2: ClassVar[str] = "2"  # Seed 2
    SCRAMBLE_3: ClassVar[str] = "3"  # Seed 3
    SCRAMBLE_4: ClassVar[str] = "4"  # Seed 4
    SCRAMBLE_5: ClassVar[str] = "5"  # Seed 5
    SCRAMBLE_6: ClassVar[str] = "6"  # Seed 6

    # Commands
    SOLVE: ClassVar[str] = "/"  # Solve (SLASH key maps to ? in GUI)
    QUIT: ClassVar[str] = "q"  # Quit
    UNDO: ClassVar[str] = "<"  # Undo
    SPACE: ClassVar[str] = " "  # Space (continue/pause)

    # Speed control
    SPEED_UP: ClassVar[str] = "+"  # Faster animation
    SPEED_DOWN: ClassVar[str] = "-"  # Slower animation

    # Predefined sequences
    SCRAMBLE_AND_SOLVE: ClassVar[TestSequence] = TestSequence(
        name="Scramble and Solve",
        keys="1?q",
        description="Scramble with seed 1, solve, quit",
        expected_timeout=60.0
    )

    MULTIPLE_SCRAMBLES: ClassVar[TestSequence] = TestSequence(
        name="Multiple Scrambles",
        keys="123?q",
        description="Three scrambles (seeds 1,2,3), solve, quit",
        expected_timeout=90.0
    )

    FACE_ROTATIONS: ClassVar[TestSequence] = TestSequence(
        name="Face Rotations",
        keys="rrrludfbq",
        description="Multiple face rotations, quit",
        expected_timeout=30.0
    )

    QUICK_SOLVE: ClassVar[TestSequence] = TestSequence(
        name="Quick Solve",
        keys="+++1?q",
        description="Speed up, scramble, solve, quit",
        expected_timeout=30.0
    )

    @classmethod
    def scramble_solve_quit(cls, seed: int = 1, speed_ups: int = 0) -> str:
        """Generate a scramble-solve-quit sequence.

        Args:
            seed: Scramble seed (1-6 or 0 for random).
            speed_ups: Number of speed increases.

        Returns:
            Key sequence string.

        Example:
            >>> TestSequences.scramble_solve_quit(1, 3)
            '+++1?q'
        """
        speed = cls.SPEED_UP * speed_ups
        scramble = str(seed) if 0 <= seed <= 6 else "1"
        return f"{speed}{scramble}?q"

    @classmethod
    def multi_scramble_solve_quit(cls, seeds: list[int], speed_ups: int = 0) -> str:
        """Generate a multi-scramble-solve-quit sequence.

        Args:
            seeds: List of scramble seeds.
            speed_ups: Number of speed increases.

        Returns:
            Key sequence string.

        Example:
            >>> TestSequences.multi_scramble_solve_quit([1, 2, 3], 3)
            '+++123?q'
        """
        speed = cls.SPEED_UP * speed_ups
        scrambles = "".join(str(s) for s in seeds if 0 <= s <= 6)
        return f"{speed}{scrambles}?q"

    @classmethod
    def face_rotation_sequence(cls, faces: str, quit_after: bool = True) -> str:
        """Generate a face rotation sequence.

        Args:
            faces: Face letters (e.g., "RRLUDF").
            quit_after: Whether to add quit at end.

        Returns:
            Key sequence string.

        Example:
            >>> TestSequences.face_rotation_sequence("RRLU")
            'rrluq'
        """
        rotations = faces.lower()
        return f"{rotations}q" if quit_after else rotations

    @classmethod
    def get_all_sequences(cls) -> list[TestSequence]:
        """Get all predefined test sequences.

        Returns:
            List of TestSequence objects.
        """
        return [
            cls.SCRAMBLE_AND_SOLVE,
            cls.MULTIPLE_SCRAMBLES,
            cls.FACE_ROTATIONS,
            cls.QUICK_SOLVE,
        ]
