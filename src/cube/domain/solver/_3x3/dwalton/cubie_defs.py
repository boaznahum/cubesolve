"""
Cubie-level move definitions for the Kociemba two-phase algorithm.

Based on Herbert Kociemba's algorithm as used in dwalton76/rubiks-cube-NxNxN-solver.

8 corners: URF=0, UFL=1, ULB=2, UBR=3, DFR=4, DLF=5, DBL=6, DRB=7
12 edges:  UR=0, UF=1, UL=2, UB=3, DR=4, DF=5, DL=6, DB=7, FR=8, FL=9, BL=10, BR=11

Each move is defined by corner/edge permutation and orientation changes.
Corner orientation: 0=oriented, 1=CW twist, 2=CCW twist (mod 3)
Edge orientation:   0=oriented, 1=flipped (mod 2)
"""

from __future__ import annotations

# Corner indices
URF, UFL, ULB, UBR, DFR, DLF, DBL, DRB = range(8)

# Edge indices
UR, UF, UL, UB, DR, DF, DL, DB, FR, FL, BL, BR = range(12)

# E-slice edges (equator layer between U and D)
E_SLICE_EDGES = frozenset({FR, FL, BL, BR})  # indices 8-11

# Number of moves (6 faces x 3 quarter-turns = 18)
N_MOVES = 18
MOVE_NAMES: list[str] = [
    "U", "U2", "U'", "R", "R2", "R'", "F", "F2", "F'",
    "D", "D2", "D'", "L", "L2", "L'", "B", "B2", "B'",
]

# Phase 2 move indices (U, U2, U', D, D2, D', R2, L2, F2, B2)
PHASE2_MOVES: list[int] = [0, 1, 2, 9, 10, 11, 4, 13, 7, 16]

# ============================================================================
# Move definitions: (corner_perm, corner_orient, edge_perm, edge_orient)
# Only clockwise quarter turns defined; half and inverse derived below.
# ============================================================================

# U move
_U_CP = [UBR, URF, UFL, ULB, DFR, DLF, DBL, DRB]
_U_CO = [0, 0, 0, 0, 0, 0, 0, 0]
_U_EP = [UB, UR, UF, UL, DR, DF, DL, DB, FR, FL, BL, BR]
_U_EO = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# R move
_R_CP = [DFR, UFL, ULB, URF, DRB, DLF, DBL, UBR]
_R_CO = [2, 0, 0, 1, 1, 0, 0, 2]
_R_EP = [FR, UF, UL, UB, BR, DF, DL, DB, DR, FL, BL, UR]
_R_EO = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# F move
_F_CP = [UFL, DLF, ULB, UBR, URF, DFR, DBL, DRB]
_F_CO = [1, 2, 0, 0, 2, 1, 0, 0]
_F_EP = [UR, FL, UL, UB, DR, FR, DL, DB, UF, DF, BL, BR]
_F_EO = [0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0]

# D move
_D_CP = [URF, UFL, ULB, UBR, DLF, DBL, DRB, DFR]
_D_CO = [0, 0, 0, 0, 0, 0, 0, 0]
_D_EP = [UR, UF, UL, UB, DF, DL, DB, DR, FR, FL, BL, BR]
_D_EO = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# L move
_L_CP = [URF, ULB, DBL, UBR, DFR, UFL, DLF, DRB]
_L_CO = [0, 1, 2, 0, 0, 2, 1, 0]
_L_EP = [UR, UF, BL, UB, DR, DF, FL, DB, FR, UL, DL, BR]
_L_EO = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# B move
_B_CP = [URF, UFL, UBR, DRB, DFR, DLF, ULB, DBL]
_B_CO = [0, 0, 1, 2, 0, 0, 2, 1]
_B_EP = [UR, UF, UL, BR, DR, DF, DL, BL, FR, FL, UB, DB]
_B_EO = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1]


def _compose_cp(cp1: list[int], co1: list[int],
                cp2: list[int], co2: list[int]) -> tuple[list[int], list[int]]:
    """Compose two corner permutation+orientation: apply cp2 then cp1."""
    cp = [cp1[cp2[i]] for i in range(8)]
    co = [(co1[cp2[i]] + co2[i]) % 3 for i in range(8)]
    return cp, co


def _compose_ep(ep1: list[int], eo1: list[int],
                ep2: list[int], eo2: list[int]) -> tuple[list[int], list[int]]:
    """Compose two edge permutation+orientation: apply ep2 then ep1."""
    ep = [ep1[ep2[i]] for i in range(12)]
    eo = [(eo1[ep2[i]] + eo2[i]) % 2 for i in range(12)]
    return ep, eo


# Build all 18 moves: 6 faces x (CW, half, CCW)
_BASE_MOVES = [
    (_U_CP, _U_CO, _U_EP, _U_EO),
    (_R_CP, _R_CO, _R_EP, _R_EO),
    (_F_CP, _F_CO, _F_EP, _F_EO),
    (_D_CP, _D_CO, _D_EP, _D_EO),
    (_L_CP, _L_CO, _L_EP, _L_EO),
    (_B_CP, _B_CO, _B_EP, _B_EO),
]

# All 18 moves: [U, U2, U', R, R2, R', F, F2, F', D, D2, D', L, L2, L', B, B2, B']
MOVES_CP: list[list[int]] = []
MOVES_CO: list[list[int]] = []
MOVES_EP: list[list[int]] = []
MOVES_EO: list[list[int]] = []

_ID_CP = list(range(8))
_ID_CO = [0] * 8
_ID_EP = list(range(12))
_ID_EO = [0] * 12

for cp1, co1, ep1, eo1 in _BASE_MOVES:
    # Quarter turn (CW)
    MOVES_CP.append(cp1)
    MOVES_CO.append(co1)
    MOVES_EP.append(ep1)
    MOVES_EO.append(eo1)

    # Half turn = CW composed with CW
    cp2, co2 = _compose_cp(cp1, co1, cp1, co1)
    ep2, eo2 = _compose_ep(ep1, eo1, ep1, eo1)
    MOVES_CP.append(cp2)
    MOVES_CO.append(co2)
    MOVES_EP.append(ep2)
    MOVES_EO.append(eo2)

    # Inverse (CCW) = CW composed with half
    cp3, co3 = _compose_cp(cp1, co1, cp2, co2)
    ep3, eo3 = _compose_ep(ep1, eo1, ep2, eo2)
    MOVES_CP.append(cp3)
    MOVES_CO.append(co3)
    MOVES_EP.append(ep3)
    MOVES_EO.append(eo3)
