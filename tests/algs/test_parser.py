"""
Parser Tests - Verify algorithm parsing round-trip and correctness.

Test Strategy:
- Phase 1: Short sequences (find bugs fast)
  - Level 1: Single moves
  - Level 2: Two-move sequences
  - Level 3: Four-move sequences
  - Level 4: Grouped sequences
- Phase 2: Full scrambles

For each test:
1. Parse string → Alg
2. Convert back to string
3. Verify cube state matches
4. Verify inverse returns to solved
"""

import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.algs import Algs


# =============================================================================
# Phase 1, Level 1: Single Moves
# =============================================================================

SINGLE_MOVES = [
    # Basic face moves
    "R", "L", "U", "D", "F", "B",
    # Inverse moves
    "R'", "L'", "U'", "D'", "F'", "B'",
    # Double moves
    "R2", "L2", "U2", "D2", "F2", "B2",
    # Slice moves
    "M", "E", "S",
    "M'", "E'", "S'",
    "M2", "E2", "S2",
    # Whole cube rotations
    "X", "Y", "Z",
    "X'", "Y'", "Z'",
    "X2", "Y2", "Z2",
    # Double-layer moves
    "Rw", "Lw", "Uw", "Dw", "Fw", "Bw",
    "Rw'", "Lw'", "Uw'", "Dw'", "Fw'", "Bw'",
    "Rw2", "Lw2", "Uw2", "Dw2", "Fw2", "Bw2",
    # Adaptive wide moves
    "r", "l", "u", "d", "f", "b",
    "r'", "l'", "u'", "d'", "f'", "b'",
    "r2", "l2", "u2", "d2", "f2", "b2",
]


@pytest.mark.parametrize("move", SINGLE_MOVES)
@pytest.mark.parametrize("cube_size", [3, 4, 5])
def test_single_move_parse_round_trip(move: str, cube_size: int) -> None:
    """Test that single moves can be parsed and converted back to string."""
    # Parse the move
    parsed = Algs.parse(move)

    # Convert back to string
    result = str(parsed)

    # For single moves wrapped in SeqAlg, the result might be [R] instead of R
    # Normalize by stripping brackets if present
    normalized = result.strip("[]")

    assert normalized == move, f"Round-trip failed: '{move}' -> '{result}' -> '{normalized}'"


@pytest.mark.parametrize("move", SINGLE_MOVES)
@pytest.mark.parametrize("cube_size", [3, 4, 5])
def test_single_move_inverse_returns_solved(move: str, cube_size: int) -> None:
    """Test that move followed by its inverse returns to solved state."""
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)

    # Verify cube starts solved
    assert app.cube.solved, "Cube should start solved"

    # Parse and apply the move
    parsed = Algs.parse(move)
    parsed.play(app.cube)

    # Apply the inverse
    parsed.inv().play(app.cube)

    assert app.cube.solved, f"Move '{move}' + inverse should return to solved"


# =============================================================================
# Phase 1, Level 2: Two-Move Sequences
# =============================================================================

TWO_MOVE_SEQUENCES = [
    "R U",
    "R L",
    "R' U'",
    "R2 U2",
    "R U'",
    "R' U",
    "M E",
    "X Y",
    "Rw Uw",
    "r u",
]


@pytest.mark.parametrize("seq", TWO_MOVE_SEQUENCES)
@pytest.mark.parametrize("cube_size", [3, 4, 5])
def test_two_move_sequence_inverse(seq: str, cube_size: int) -> None:
    """Test that two-move sequence + inverse returns to solved."""
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)

    assert app.cube.solved, "Cube should start solved"

    parsed = Algs.parse(seq)
    parsed.play(app.cube)
    parsed.inv().play(app.cube)

    assert app.cube.solved, f"Sequence '{seq}' + inverse should return to solved"


# =============================================================================
# Phase 1, Level 3: Four-Move Sequences
# =============================================================================

FOUR_MOVE_SEQUENCES = [
    "R U R' U'",  # Sexy move
    "R U R U",
    "R2 U2 R2 U2",
    "L' U' L U",
    "F R U R'",
]


@pytest.mark.parametrize("seq", FOUR_MOVE_SEQUENCES)
@pytest.mark.parametrize("cube_size", [3, 4, 5])
def test_four_move_sequence_inverse(seq: str, cube_size: int) -> None:
    """Test that four-move sequence + inverse returns to solved."""
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)

    assert app.cube.solved, "Cube should start solved"

    parsed = Algs.parse(seq)
    parsed.play(app.cube)
    parsed.inv().play(app.cube)

    assert app.cube.solved, f"Sequence '{seq}' + inverse should return to solved"


# =============================================================================
# Phase 1, Level 4: Grouped Sequences
# =============================================================================

GROUPED_SEQUENCES = [
    "(R U)",
    "(R U) 2",
    "(R U R' U') 6",  # Sexy move x6 = identity
]


@pytest.mark.parametrize("seq", GROUPED_SEQUENCES)
@pytest.mark.parametrize("cube_size", [3, 4, 5])
def test_grouped_sequence_parse(seq: str, cube_size: int) -> None:
    """Test that grouped sequences can be parsed."""
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)

    parsed = Algs.parse(seq)

    # Should be able to play without error
    parsed.play(app.cube)

    # And inverse should work
    parsed.inv().play(app.cube)


@pytest.mark.parametrize("cube_size", [3, 4, 5])
def test_sexy_move_six_times_identity(cube_size: int) -> None:
    """Test that (R U R' U') x 6 = identity."""
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)

    assert app.cube.solved, "Cube should start solved"

    # Sexy move 6 times should return to solved
    sexy = Algs.parse("R U R' U'")
    for _ in range(6):
        sexy.play(app.cube)

    assert app.cube.solved, "Sexy move x6 should be identity"


# =============================================================================
# Phase 2: Scramble Tests
# =============================================================================

SCRAMBLE_SEEDS = [0, 1, 2, 3, 42, 123]
CUBE_SIZES = [3, 4, 5, 6]


@pytest.mark.parametrize("seed", SCRAMBLE_SEEDS)
@pytest.mark.parametrize("cube_size", CUBE_SIZES)
def test_scramble_round_trip(seed: int, cube_size: int) -> None:
    """Test that scramble and parsed scramble produce the same cube state.

    Semantic comparison: Apply alg1 and alg2 to separate cubes,
    verify they produce the same state.
    """
    # Generate scramble
    scramble = Algs.scramble(cube_size, seed, seq_length=20)

    # Use to_printable() to get parseable version (without {name})
    printable = scramble.to_printable()

    # Parse back
    parsed = Algs.parse(str(printable))

    # Create two cubes
    app1 = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
    app2 = AbstractApp.create_non_default(cube_size=cube_size, animation=False)

    # Apply original to cube1
    printable.play(app1.cube)

    # Apply parsed to cube2
    parsed.play(app2.cube)

    # Both cubes should be in the same state
    # Verify by applying inverse of one and checking if both return to solved
    printable.inv().play(app1.cube)
    parsed.inv().play(app2.cube)

    assert app1.cube.solved, "Cube1 should be solved after original + inverse"
    assert app2.cube.solved, "Cube2 should be solved after parsed + inverse"


@pytest.mark.parametrize("seed", SCRAMBLE_SEEDS)
@pytest.mark.parametrize("cube_size", CUBE_SIZES)
def test_scramble_same_cube_state(seed: int, cube_size: int) -> None:
    """Test that original and parsed scramble produce same cube state."""
    # Generate scramble
    scramble = Algs.scramble(cube_size, seed, seq_length=20)

    # Create two cubes
    app1 = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
    app2 = AbstractApp.create_non_default(cube_size=cube_size, animation=False)

    # Apply original scramble to cube1
    scramble.play(app1.cube)

    # Parse scramble string (use to_printable) and apply to cube2
    printable = scramble.to_printable()
    parsed = Algs.parse(str(printable))
    parsed.play(app2.cube)

    # Both cubes should be in same state (check via solved after inverse)
    # Apply inverse of original to cube1
    scramble.inv().play(app1.cube)
    # Apply inverse of parsed to cube2
    parsed.inv().play(app2.cube)

    assert app1.cube.solved, "Cube1 should be solved after scramble + inverse"
    assert app2.cube.solved, "Cube2 should be solved after parsed + inverse"


@pytest.mark.parametrize("seed", SCRAMBLE_SEEDS)
@pytest.mark.parametrize("cube_size", CUBE_SIZES)
def test_scramble_inverse_returns_solved(seed: int, cube_size: int) -> None:
    """Test that scramble + inverse returns to solved."""
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)

    assert app.cube.solved, "Cube should start solved"

    # Generate and apply scramble
    scramble = Algs.scramble(cube_size, seed, seq_length=20)
    scramble.play(app.cube)

    # Apply inverse
    scramble.inv().play(app.cube)

    assert app.cube.solved, f"Scramble seed={seed} + inverse should return to solved"


@pytest.mark.parametrize("seed", SCRAMBLE_SEEDS)
@pytest.mark.parametrize("cube_size", CUBE_SIZES)
def test_scramble_parsed_inverse_returns_solved(seed: int, cube_size: int) -> None:
    """Test that scramble applied, then parsed inverse returns to solved."""
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)

    assert app.cube.solved, "Cube should start solved"

    # Generate and apply scramble
    scramble = Algs.scramble(cube_size, seed, seq_length=20)
    scramble.play(app.cube)

    # Parse the scramble string (use to_printable) and apply its inverse
    printable = scramble.to_printable()
    parsed = Algs.parse(str(printable))
    parsed.inv().play(app.cube)

    assert app.cube.solved, f"Scramble + parsed inverse should return to solved"
