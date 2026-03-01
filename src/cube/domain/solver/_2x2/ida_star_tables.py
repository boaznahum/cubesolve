"""IDA* pruning tables for optimal 2x2 Rubik's cube solving.

State space: 3,674,160 positions (7! × 3^6).
God's number: 11 moves (HTM).
Average optimal solution: 8.76 moves.

We fix the DBL corner in place and only use U, R, F moves (9 total).
Two coordinates encode the full state:
  - Twist (0–728): orientation of corners 0–5 in base-3
  - Permutation (0–5039): Lehmer code of corners 0–6

Three tables:
  1. twist_move[729 × 9]  — twist after each move
  2. perm_move[5040 × 9]  — permutation after each move
  3. pruning[5040 × 729]  — exact distance from solved (BFS)
"""

from __future__ import annotations

from array import array
from dataclasses import dataclass
from math import factorial

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

N_TWIST: int = 3 ** 6          # 729
N_CORNERS: int = factorial(7)  # 5040
N_MOVE: int = 9                # U, U2, U', R, R2, R', F, F2, F'

# Corner numbering (DBL=7 is fixed by U, R, F moves)
URF, UFL, ULB, UBR, DFR, DLF, DRB, DBL = range(8)

# ---------------------------------------------------------------------------
# Move definitions at cubie level: (corner_perm, corner_orient)
# Convention: "where-from" — cp[i] = j means position i gets piece from j.
# Corner 7 (DBL) is always identity/0-twist (fixed by all 9 moves).
#
# Twist convention:
#   0 = U/D reference sticker on U or D face (oriented)
#   1 = reference sticker one position CW
#   2 = reference sticker one position CCW
# ---------------------------------------------------------------------------

# Domain model U: UBR→URF→UFL→ULB→UBR cycle
# where-from: URF from UBR(3), UFL from URF(0), ULB from UFL(1), UBR from ULB(2)
_CP_U = [3, 0, 1, 2, 4, 5, 6, 7]
_CO_U = [0, 0, 0, 0, 0, 0, 0, 0]

# Domain model R: DFR→URF→UBR→DRB→DFR cycle
# where-from: URF from DFR(4), UBR from URF(0), DRB from UBR(3), DFR from DRB(6)
_CP_R = [4, 1, 2, 0, 6, 5, 3, 7]
_CO_R = [2, 0, 0, 1, 1, 0, 2, 0]

# Domain model F: UFL→URF→DFR→DLF→UFL cycle
# where-from: URF from UFL(1), UFL from DLF(5), DFR from URF(0), DLF from DFR(4)
_CP_F = [1, 5, 2, 3, 0, 4, 6, 7]
_CO_F = [1, 2, 0, 0, 2, 1, 0, 0]

# All 9 moves: base moves and their squares/inverses
# We store as (cp, co) tuples and generate U2/U'/R2/R'/F2/F' by composition.


def _compose(
    cp_a: list[int], co_a: list[int],
    cp_b: list[int], co_b: list[int],
) -> tuple[list[int], list[int]]:
    """Apply move B after state A: result[i] = A[B[i]] with twist composition."""
    cp = [cp_a[cp_b[i]] for i in range(8)]
    co = [(co_a[cp_b[i]] + co_b[i]) % 3 for i in range(8)]
    return cp, co


def _build_all_moves() -> list[tuple[list[int], list[int]]]:
    """Build the 9 moves: U, U2, U', R, R2, R', F, F2, F'."""
    moves: list[tuple[list[int], list[int]]] = []
    for cp_base, co_base in [(_CP_U, _CO_U), (_CP_R, _CO_R), (_CP_F, _CO_F)]:
        # Base move (quarter turn)
        m1 = (cp_base, co_base)
        # Double move
        m2 = _compose(cp_base, co_base, cp_base, co_base)
        # Inverse (triple = inverse for quarter turns)
        m3 = _compose(m2[0], m2[1], cp_base, co_base)
        moves.extend([m1, m2, m3])
    return moves


_ALL_MOVES: list[tuple[list[int], list[int]]] = _build_all_moves()

# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------


def twist_from_co(co: list[int]) -> int:
    """Compute twist coordinate from corner orientations (corners 0–5).

    Corner 6's orientation is derived (sum mod 3 = 0) so we skip it.
    Corner 7 (DBL) is fixed with orientation 0.
    """
    val: int = 0
    for i in range(6):
        val = val * 3 + co[i]
    return val


def co_from_twist(twist: int) -> list[int]:
    """Recover corner orientations from twist coordinate."""
    co: list[int] = [0] * 8
    total: int = 0
    for i in range(5, -1, -1):
        co[i] = twist % 3
        total += co[i]
        twist //= 3
    co[6] = (3 - total % 3) % 3
    co[7] = 0  # DBL fixed
    return co


def perm_from_cp(cp: list[int]) -> int:
    """Compute permutation coordinate (Lehmer code) from corners 0–6.

    Corner 7 (DBL) is fixed, so we encode a permutation of 7 elements.
    """
    val: int = 0
    for i in range(7):
        count: int = 0
        for j in range(i + 1, 7):
            if cp[j] < cp[i]:
                count += 1
        val = val * (7 - i) + count
    return val


def cp_from_perm(perm: int) -> list[int]:
    """Recover corner permutation from Lehmer code."""
    cp: list[int] = [0] * 8
    elements: list[int] = list(range(7))
    for i in range(7):
        fact: int = factorial(6 - i)
        idx: int = perm // fact
        perm %= fact
        cp[i] = elements[idx]
        elements.pop(idx)
    cp[7] = 7  # DBL fixed
    return cp


# ---------------------------------------------------------------------------
# Table builders
# ---------------------------------------------------------------------------


def _build_twist_move_table() -> array[int]:
    """twist_move[twist * N_MOVE + move] = new twist."""
    table: array[int] = array("H", [0] * (N_TWIST * N_MOVE))
    for twist in range(N_TWIST):
        co: list[int] = co_from_twist(twist)
        for m in range(N_MOVE):
            cp_m, co_m = _ALL_MOVES[m]
            # Apply move to orientation: new_co[i] = (co[cp_m[i]] + co_m[i]) % 3
            new_co: list[int] = [(co[cp_m[i]] + co_m[i]) % 3 for i in range(8)]
            table[twist * N_MOVE + m] = twist_from_co(new_co)
    return table


def _build_perm_move_table() -> array[int]:
    """perm_move[perm * N_MOVE + move] = new perm."""
    table: array[int] = array("H", [0] * (N_CORNERS * N_MOVE))
    for perm in range(N_CORNERS):
        cp: list[int] = cp_from_perm(perm)
        for m in range(N_MOVE):
            cp_m = _ALL_MOVES[m][0]
            # Apply move to permutation: new_cp[i] = cp[cp_m[i]]
            new_cp: list[int] = [cp[cp_m[i]] for i in range(8)]
            table[perm * N_MOVE + m] = perm_from_cp(new_cp)
    return table


def _build_pruning_table(
    twist_move: array[int],
    perm_move: array[int],
) -> bytearray:
    """BFS from solved state to compute exact distance for every position.

    pruning[perm * N_TWIST + twist] = number of moves from solved.
    Total entries: 5040 × 729 = 3,674,160.
    """
    total: int = N_CORNERS * N_TWIST
    table: bytearray = bytearray(b"\xff" * total)

    # Solved state: identity permutation (perm=0), zero twist (twist=0)
    table[0] = 0
    done: int = 1
    depth: int = 0

    while done < total:
        for idx in range(total):
            if table[idx] != depth:
                continue
            perm: int = idx // N_TWIST
            twist: int = idx % N_TWIST
            for m in range(N_MOVE):
                new_perm: int = perm_move[perm * N_MOVE + m]
                new_twist: int = twist_move[twist * N_MOVE + m]
                new_idx: int = new_perm * N_TWIST + new_twist
                if table[new_idx] == 0xFF:
                    table[new_idx] = depth + 1
                    done += 1
        depth += 1

    return table


# ---------------------------------------------------------------------------
# Lazy singleton
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Tables:
    """Precomputed IDA* tables for the 2x2 solver."""
    twist_move: array[int]
    perm_move: array[int]
    pruning: bytearray


_tables: Tables | None = None


def _load_precomputed() -> Tables:
    """Load tables from pre-computed data (zlib-compressed, base85-encoded).

    This is much faster than building via BFS (~50ms vs ~3 seconds).
    """
    import base64
    import zlib

    from cube.domain.solver._2x2._precomputed import (
        PERM_MOVE_Z85,
        PRUNING_Z85,
        TWIST_MOVE_Z85,
    )

    twist_move = array("H")
    twist_move.frombytes(zlib.decompress(base64.b85decode(TWIST_MOVE_Z85)))

    perm_move = array("H")
    perm_move.frombytes(zlib.decompress(base64.b85decode(PERM_MOVE_Z85)))

    pruning = bytearray(zlib.decompress(base64.b85decode(PRUNING_Z85)))

    return Tables(twist_move=twist_move, perm_move=perm_move, pruning=pruning)


def get_tables() -> Tables:
    """Get the precomputed tables. Cached as module-level singleton.

    Loads from pre-computed data file on first call (~50ms).
    Falls back to building tables from scratch if pre-computed data is missing.
    """
    global _tables  # noqa: PLW0603
    if _tables is None:
        try:
            _tables = _load_precomputed()
        except ImportError:
            # Fallback: build from scratch (slow, ~3 seconds)
            twist_move: array[int] = _build_twist_move_table()
            perm_move: array[int] = _build_perm_move_table()
            pruning: bytearray = _build_pruning_table(twist_move, perm_move)
            _tables = Tables(twist_move=twist_move, perm_move=perm_move, pruning=pruning)
    return _tables
