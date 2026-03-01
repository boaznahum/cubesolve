"""
Coordinate computation for the Kociemba two-phase algorithm.

Converts cubie-level state (permutation + orientation arrays) into integer
coordinates for table lookup.

Based on dwalton76/rubiks-cube-NxNxN-solver's table-based approach.
"""

from __future__ import annotations

from math import comb

from cube.domain.solver._3x3.dwalton.cubie_defs import E_SLICE_EDGES


def corner_orientation_coord(co: list[int]) -> int:
    """Corner orientation coordinate: 0..2186 (3^7 - 1).

    The 8th corner's orientation is determined by the other 7.
    Encodes as a base-3 number using first 7 corners.
    """
    val = 0
    for i in range(7):
        val = val * 3 + co[i]
    return val


def edge_orientation_coord(eo: list[int]) -> int:
    """Edge orientation coordinate: 0..2047 (2^11 - 1).

    The 12th edge's orientation is determined by the other 11.
    Encodes as a base-2 number using first 11 edges.
    """
    val = 0
    for i in range(11):
        val = val * 2 + eo[i]
    return val


def ud_slice_coord(ep: list[int]) -> int:
    """UD-slice coordinate: 0..494 (C(12,4) - 1).

    Tracks which 4 of 12 edge positions contain E-slice edges (FR,FL,BL,BR).
    Uses combinatorial number system encoding.
    """
    # Which positions hold E-slice edges?
    occupied = [1 if ep[i] in E_SLICE_EDGES else 0 for i in range(12)]

    # Combinatorial number system: encode which 4 of 12 slots are occupied
    val = 0
    k = 4
    for i in range(11, -1, -1):
        if occupied[i]:
            val += comb(i, k)
            k -= 1
    return val


def corner_perm_coord(cp: list[int]) -> int:
    """Corner permutation coordinate: 0..40319 (8!).

    Lehmer code / factorial number system encoding.
    """
    val = 0
    for i in range(7):
        count = 0
        for j in range(i + 1, 8):
            if cp[j] < cp[i]:
                count += 1
        val = (val + count) * (7 - i)
    return val


def edge8_perm_coord(ep: list[int]) -> int:
    """UD-edge permutation coordinate: 0..40319 (8!).

    Permutation of the 8 U/D-layer edges (UR,UF,UL,UB,DR,DF,DL,DB = 0..7).
    Only valid in Phase 2 when E-slice edges are in E-slice positions.
    """
    # Extract the 8 UD edges (indices 0-7 in the perm)
    ud = ep[:8]
    val = 0
    for i in range(7):
        count = 0
        for j in range(i + 1, 8):
            if ud[j] < ud[i]:
                count += 1
        val = (val + count) * (7 - i)
    return val


def eslice_perm_coord(ep: list[int]) -> int:
    """E-slice edge permutation coordinate: 0..23 (4!).

    Permutation of edges in positions 8-11 (FR, FL, BL, BR slots).
    Only valid in Phase 2 when E-slice edges are in their slots.
    Maps the edge values to 0-3 range first.
    """
    # Edges in E-slice positions, mapped to 0-3
    es = [ep[i] - 8 for i in range(8, 12)]
    val = 0
    for i in range(3):
        count = 0
        for j in range(i + 1, 4):
            if es[j] < es[i]:
                count += 1
        val = (val + count) * (3 - i)
    return val


# Coordinate sizes
N_CO = 2187     # 3^7
N_EO = 2048     # 2^11
N_UDSLICE = 495  # C(12,4)
N_CP = 40320    # 8!
N_UDEP = 40320  # 8!
N_EP = 24       # 4!
