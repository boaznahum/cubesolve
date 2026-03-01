"""IDA* search for optimal 2x2 Rubik's cube solutions.

Uses precomputed pruning tables for exact distance — zero wasted iterations.
Finds optimal solutions (≤11 moves HTM) in sub-millisecond time.
"""

from __future__ import annotations

from array import array

from cube.domain.solver._2x2.ida_star_tables import N_MOVE, N_TWIST, Tables


def solve(perm: int, twist: int, tables: Tables) -> list[int]:
    """Find an optimal solution for the given 2x2 state.

    Args:
        perm: Corner permutation coordinate (0–5039).
        twist: Corner twist coordinate (0–728).
        tables: Precomputed move/pruning tables.

    Returns:
        List of move indices (0–8) representing the optimal solution.
        Empty list if already solved.
    """
    if perm == 0 and twist == 0:
        return []

    pruning: bytearray = tables.pruning
    depth_limit: int = pruning[perm * N_TWIST + twist]

    solution: list[int] = []

    if _search(perm, twist, 0, depth_limit, -1, solution,
               tables.perm_move, tables.twist_move, pruning):
        return solution

    # Should never reach here with exact pruning table
    raise RuntimeError("IDA* search failed — pruning table may be corrupt")


def _search(
    perm: int,
    twist: int,
    depth: int,
    limit: int,
    last_move: int,
    solution: list[int],
    perm_move: array[int],
    twist_move: array[int],
    pruning: bytearray,
) -> bool:
    """Recursive IDA* search with same-face pruning.

    Args:
        perm: Current permutation coordinate.
        twist: Current twist coordinate.
        depth: Current search depth.
        limit: Maximum depth for this iteration.
        last_move: Previous move index (-1 if none), for same-face pruning.
        solution: Accumulates the solution moves (modified in place).
        perm_move: Permutation move table.
        twist_move: Twist move table.
        pruning: Pruning table.

    Returns:
        True if solution found, False otherwise.
    """
    dist: int = pruning[perm * N_TWIST + twist]
    if dist == 0:
        return True
    if depth + dist > limit:
        return False

    perm_base: int = perm * N_MOVE
    twist_base: int = twist * N_MOVE

    for m in range(N_MOVE):
        # Same-face pruning: skip moves on the same face as the last move.
        # Moves 0-2 are U/U2/U', 3-5 are R/R2/R', 6-8 are F/F2/F'.
        if last_move >= 0 and m // 3 == last_move // 3:
            continue

        new_perm: int = perm_move[perm_base + m]
        new_twist: int = twist_move[twist_base + m]

        solution.append(m)
        if _search(new_perm, new_twist, depth + 1, limit, m, solution,
                   perm_move, twist_move, pruning):
            return True
        solution.pop()

    return False
