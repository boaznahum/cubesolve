"""
IDA* search for the Kociemba two-phase algorithm.

Based on dwalton76/rubiks-cube-NxNxN-solver's IDA* implementation with
pruning tables as heuristics.
"""

from __future__ import annotations

from cube.domain.solver._3x3.dwalton.coords import (
    N_EP, N_UDSLICE,
    corner_perm_coord, edge8_perm_coord, eslice_perm_coord,
    ud_slice_coord,
)
from cube.domain.solver._3x3.dwalton.cubie_defs import (
    MOVE_NAMES, N_MOVES, PHASE2_MOVES,
    _ID_EP,
    _compose_cp, _compose_ep,
    MOVES_CP, MOVES_CO, MOVES_EP, MOVES_EO,
)
from cube.domain.solver._3x3.dwalton import tables

# Solved UD-slice coordinate (E-slice edges in positions 8-11)
_SOLVED_UD = ud_slice_coord(_ID_EP)  # = 494


def _phase1_heuristic(co: int, eo: int, ud: int) -> int:
    """Phase 1 lower bound: max of two pruning tables."""
    h1 = tables.co_ud_prune[co * N_UDSLICE + ud]
    h2 = tables.eo_ud_prune[eo * N_UDSLICE + ud]
    return max(h1, h2)


def _phase2_heuristic(cp: int, udep: int, ep: int) -> int:
    """Phase 2 lower bound: max of two pruning tables."""
    h1 = tables.cp_ep_prune[cp * N_EP + ep]
    h2 = tables.udep_ep_prune[udep * N_EP + ep]
    return max(h1, h2)


def _moves_allowed(prev_move: int, moves: list[int]) -> list[int]:
    """Filter moves: skip same-face and enforce opposite-face ordering."""
    if prev_move == -1:
        return moves
    prev_face = prev_move // 3
    result: list[int] = []
    for m in moves:
        face = m // 3
        if face == prev_face:
            continue
        # For opposite faces (U/D=0/3, R/L=1/4, F/B=2/5), enforce ordering
        if face == prev_face + 3:
            continue
        result.append(m)
    return result


def solve(
    cp_init: list[int], co_init: list[int],
    ep_init: list[int], eo_init: list[int],
    max_length: int = 25,
) -> list[str] | None:
    """Find a solution using Kociemba's two-phase algorithm.

    Args:
        cp_init, co_init: Corner permutation and orientation arrays
        ep_init, eo_init: Edge permutation and orientation arrays
        max_length: Maximum total solution length

    Returns:
        List of move names, or None if no solution found
    """
    tables.build_all_tables()

    from cube.domain.solver._3x3.dwalton.coords import (
        corner_orientation_coord, edge_orientation_coord,
    )

    co_coord = corner_orientation_coord(co_init)
    eo_coord = edge_orientation_coord(eo_init)
    ud_coord = ud_slice_coord(ep_init)

    # Try increasing Phase 1 depths
    for phase1_depth in range(13):
        solution = _search_phase1(
            co_coord, eo_coord, ud_coord,
            cp_init[:], co_init[:], ep_init[:], eo_init[:],
            phase1_depth, max_length,
        )
        if solution is not None:
            return solution

    return None


def _search_phase1(
    co: int, eo: int, ud: int,
    cp_arr: list[int], co_arr: list[int],
    ep_arr: list[int], eo_arr: list[int],
    max_depth: int, max_total: int,
) -> list[str] | None:
    """IDA* search for Phase 1, tracking cubie state for Phase 2."""

    def dfs(co: int, eo: int, ud: int,
            cp_a: list[int], co_a: list[int],
            ep_a: list[int], eo_a: list[int],
            depth: int, prev_move: int,
            path: list[int]) -> list[str] | None:

        if depth == 0:
            if co == 0 and eo == 0 and ud == _SOLVED_UD:
                # Phase 1 solved — compute Phase 2 coords from cubie state
                cp_coord = corner_perm_coord(cp_a)
                udep_coord = edge8_perm_coord(ep_a)
                ep_coord = eslice_perm_coord(ep_a)
                remaining = max_total - len(path)
                p2 = _search_phase2(cp_coord, udep_coord, ep_coord, remaining)
                if p2 is not None:
                    return [MOVE_NAMES[m] for m in path] + p2
            return None

        h = _phase1_heuristic(co, eo, ud)
        if h > depth:
            return None

        for m in _moves_allowed(prev_move, list(range(N_MOVES))):
            new_co = tables.co_move[m][co]
            new_eo = tables.eo_move[m][eo]
            new_ud = tables.ud_move[m][ud]

            # Track cubie state
            new_cp, new_co_a = _compose_cp(cp_a, co_a, MOVES_CP[m], MOVES_CO[m])
            new_ep, new_eo_a = _compose_ep(ep_a, eo_a, MOVES_EP[m], MOVES_EO[m])

            path.append(m)
            result = dfs(new_co, new_eo, new_ud,
                         new_cp, new_co_a, new_ep, new_eo_a,
                         depth - 1, m, path)
            if result is not None:
                return result
            path.pop()

        return None

    return dfs(co, eo, ud,
               cp_arr, co_arr, ep_arr, eo_arr,
               max_depth, -1, [])


def _search_phase2(cp: int, udep: int, ep: int,
                   max_depth: int) -> list[str] | None:
    """IDA* search for Phase 2 with iterative deepening."""
    for depth in range(min(max_depth + 1, 19)):
        result = _dfs_phase2(cp, udep, ep, depth, -1, [])
        if result is not None:
            return result
    return None


def _dfs_phase2(cp: int, udep: int, ep: int,
                depth: int, prev_move: int,
                path: list[int]) -> list[str] | None:
    """DFS for Phase 2."""
    if depth == 0:
        if cp == 0 and udep == 0 and ep == 0:
            return [MOVE_NAMES[m] for m in path]
        return None

    h = _phase2_heuristic(cp, udep, ep)
    if h > depth:
        return None

    for m in _moves_allowed(prev_move, PHASE2_MOVES):
        new_cp = tables.cp_move[m][cp]
        new_udep = tables.udep_move[m][udep]
        new_ep = tables.ep_move[m][ep]

        path.append(m)
        result = _dfs_phase2(new_cp, new_udep, new_ep,
                             depth - 1, m, path)
        if result is not None:
            return result
        path.pop()

    return None
