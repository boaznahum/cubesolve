"""
Move tables and pruning tables for the Kociemba two-phase algorithm.

Tables are computed once at import time and cached in module-level variables.
Based on dwalton76/rubiks-cube-NxNxN-solver's lookup table approach.

Move tables: How coordinates change under each of the 18 moves.
Pruning tables: Lower bound on moves needed to reach goal state.
"""

from __future__ import annotations

from cube.domain.solver._3x3.dwalton.cubie_defs import (
    MOVES_CO, MOVES_CP, MOVES_EO, MOVES_EP, N_MOVES,
    _ID_CO, _ID_CP, _ID_EO, _ID_EP,
    _compose_cp, _compose_ep,
)
from cube.domain.solver._3x3.dwalton.coords import (
    N_CO, N_CP, N_EO, N_EP, N_UDEP, N_UDSLICE,
    corner_orientation_coord, corner_perm_coord,
    edge8_perm_coord, edge_orientation_coord,
    eslice_perm_coord, ud_slice_coord,
)

# ============================================================================
# Move tables: coord_after = move_table[move][coord_before]
# ============================================================================

_tables_built = False

# Phase 1 move tables
co_move: list[list[int]] = []   # [18][2187]
eo_move: list[list[int]] = []   # [18][2048]
ud_move: list[list[int]] = []   # [18][495]

# Phase 2 move tables
cp_move: list[list[int]] = []   # [18][40320]
udep_move: list[list[int]] = []  # [18][40320]
ep_move: list[list[int]] = []   # [18][24]

# Pruning tables (flattened 2D arrays for speed)
co_ud_prune: list[int] = []     # [2187 * 495] Phase 1
eo_ud_prune: list[int] = []     # [2048 * 495] Phase 1
cp_ep_prune: list[int] = []     # [40320 * 24] Phase 2
udep_ep_prune: list[int] = []   # [40320 * 24] Phase 2


def _set_co_from_coord(coord: int, co: list[int]) -> None:
    """Decode corner orientation coordinate back to array."""
    parity = 0
    for i in range(6, -1, -1):
        co[i] = coord % 3
        parity += co[i]
        coord //= 3
    co[7] = (3 - parity % 3) % 3


def _set_eo_from_coord(coord: int, eo: list[int]) -> None:
    """Decode edge orientation coordinate back to array."""
    parity = 0
    for i in range(10, -1, -1):
        eo[i] = coord % 2
        parity += eo[i]
        coord //= 2
    eo[11] = parity % 2


def _set_ud_from_coord(coord: int, ep: list[int]) -> None:
    """Decode UD-slice coord to a representative edge permutation.

    Only the combination matters (which 4 slots), not the order within.
    Places E-slice edges (8,9,10,11) in the occupied slots, UD edges elsewhere.
    """
    from math import comb
    occupied = [False] * 12
    k = 4
    for i in range(11, -1, -1):
        c = comb(i, k)
        if coord >= c:
            occupied[i] = True
            coord -= c
            k -= 1

    # Fill ep: E-slice edges in occupied slots, UD edges elsewhere
    eslice_idx = 8
    ud_idx = 0
    for i in range(12):
        if occupied[i]:
            ep[i] = eslice_idx
            eslice_idx += 1
        else:
            ep[i] = ud_idx
            ud_idx += 1


def _set_cp_from_coord(coord: int, cp: list[int]) -> None:
    """Decode corner permutation coordinate back to array."""
    cp[:] = [0] * 8
    used = [False] * 8
    for i in range(8):
        fact = 1
        for f in range(1, 7 - i + 1):
            fact *= f
        idx = coord // fact
        coord %= fact
        count = 0
        for j in range(8):
            if not used[j]:
                if count == idx:
                    cp[i] = j
                    used[j] = True
                    break
                count += 1


def _set_edge8_from_coord(coord: int, ep: list[int]) -> None:
    """Decode UD-edge permutation coordinate back to first 8 positions."""
    used = [False] * 8
    for i in range(8):
        fact = 1
        for f in range(1, 7 - i + 1):
            fact *= f
        idx = coord // fact
        coord %= fact
        count = 0
        for j in range(8):
            if not used[j]:
                if count == idx:
                    ep[i] = j
                    used[j] = True
                    break
                count += 1


def _set_eslice_from_coord(coord: int, ep: list[int]) -> None:
    """Decode E-slice permutation coordinate to positions 8-11."""
    used = [False] * 4
    for i in range(4):
        fact = 1
        for f in range(1, 3 - i + 1):
            fact *= f
        idx = coord // fact
        coord %= fact
        count = 0
        for j in range(4):
            if not used[j]:
                if count == idx:
                    ep[8 + i] = 8 + j
                    used[j] = True
                    break
                count += 1


def _build_move_tables() -> None:
    """Build all move tables."""
    global co_move, eo_move, ud_move, cp_move, udep_move, ep_move

    # CO move table
    co_move = [[-1] * N_CO for _ in range(N_MOVES)]
    co_arr = [0] * 8
    for coord in range(N_CO):
        _set_co_from_coord(coord, co_arr)
        for m in range(N_MOVES):
            _, new_co = _compose_cp(_ID_CP, co_arr, MOVES_CP[m], MOVES_CO[m])
            co_move[m][coord] = corner_orientation_coord(new_co)

    # EO move table
    eo_move = [[-1] * N_EO for _ in range(N_MOVES)]
    eo_arr = [0] * 12
    for coord in range(N_EO):
        _set_eo_from_coord(coord, eo_arr)
        for m in range(N_MOVES):
            _, new_eo = _compose_ep(_ID_EP, eo_arr, MOVES_EP[m], MOVES_EO[m])
            eo_move[m][coord] = edge_orientation_coord(new_eo)

    # UD-slice move table
    ud_move = [[-1] * N_UDSLICE for _ in range(N_MOVES)]
    ep_arr = [0] * 12
    for coord in range(N_UDSLICE):
        _set_ud_from_coord(coord, ep_arr)
        for m in range(N_MOVES):
            new_ep, _ = _compose_ep(ep_arr, _ID_EO, MOVES_EP[m], MOVES_EO[m])
            ud_move[m][coord] = ud_slice_coord(new_ep)

    # CP move table
    cp_move = [[-1] * N_CP for _ in range(N_MOVES)]
    cp_arr = [0] * 8
    for coord in range(N_CP):
        _set_cp_from_coord(coord, cp_arr)
        for m in range(N_MOVES):
            new_cp, _ = _compose_cp(cp_arr, _ID_CO, MOVES_CP[m], MOVES_CO[m])
            cp_move[m][coord] = corner_perm_coord(new_cp)

    # UDEP move table (8 UD edges)
    udep_move = [[-1] * N_UDEP for _ in range(N_MOVES)]
    ep_arr2 = list(range(12))  # need full 12 for composition
    for coord in range(N_UDEP):
        _set_edge8_from_coord(coord, ep_arr2)
        # Keep E-slice in identity positions for UD-edge table
        for i in range(8, 12):
            ep_arr2[i] = i
        for m in range(N_MOVES):
            new_ep, _ = _compose_ep(ep_arr2, _ID_EO, MOVES_EP[m], MOVES_EO[m])
            udep_move[m][coord] = edge8_perm_coord(new_ep)

    # E-slice perm move table
    ep_move = [[-1] * N_EP for _ in range(N_MOVES)]
    ep_arr3 = list(range(12))
    for coord in range(N_EP):
        # Keep UD edges in identity, set E-slice from coord
        for i in range(8):
            ep_arr3[i] = i
        _set_eslice_from_coord(coord, ep_arr3)
        for m in range(N_MOVES):
            new_ep, _ = _compose_ep(ep_arr3, _ID_EO, MOVES_EP[m], MOVES_EO[m])
            ep_move[m][coord] = eslice_perm_coord(new_ep)


def _build_pruning_table(
    move_table_a: list[list[int]], n_a: int,
    move_table_b: list[list[int]], n_b: int,
    moves: list[int],
    goal_a: int = 0,
    goal_b: int = 0,
) -> list[int]:
    """Build a pruning table using BFS from the goal state.

    Returns a flat array of size n_a * n_b where
    prune[a * n_b + b] = minimum moves to reach (goal_a, goal_b).
    """
    size = n_a * n_b
    table = [-1] * size
    goal_idx = goal_a * n_b + goal_b
    table[goal_idx] = 0
    done = 1
    depth = 0

    while done < size:
        for idx in range(size):
            if table[idx] != depth:
                continue
            a = idx // n_b
            b = idx % n_b
            for m in moves:
                new_a = move_table_a[m][a]
                new_b = move_table_b[m][b]
                new_idx = new_a * n_b + new_b
                if table[new_idx] == -1:
                    table[new_idx] = depth + 1
                    done += 1
        depth += 1

    return table


def build_all_tables() -> None:
    """Build all move tables and pruning tables. Called once at first use."""
    global _tables_built, co_ud_prune, eo_ud_prune, cp_ep_prune, udep_ep_prune

    if _tables_built:
        return

    _build_move_tables()

    all_moves = list(range(N_MOVES))

    # Phase 1 pruning tables
    # Solved UD-slice coord: E-slice edges (8,9,10,11) in positions 8-11
    solved_ud = ud_slice_coord(_ID_EP)  # = 494
    co_ud_prune = _build_pruning_table(
        co_move, N_CO, ud_move, N_UDSLICE, all_moves,
        goal_a=0, goal_b=solved_ud,
    )
    eo_ud_prune = _build_pruning_table(
        eo_move, N_EO, ud_move, N_UDSLICE, all_moves,
        goal_a=0, goal_b=solved_ud,
    )

    # Phase 2 pruning tables (only phase 2 moves)
    from cube.domain.solver._3x3.dwalton.cubie_defs import PHASE2_MOVES
    cp_ep_prune = _build_pruning_table(cp_move, N_CP, ep_move, N_EP, PHASE2_MOVES)
    udep_ep_prune = _build_pruning_table(udep_move, N_UDEP, ep_move, N_EP, PHASE2_MOVES)

    _tables_built = True
