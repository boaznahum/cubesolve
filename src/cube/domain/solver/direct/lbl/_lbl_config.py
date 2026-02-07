NUMBER_OF_SLICES_TO_SOLVE=10000  # 100000 to all
BIG_LBL_RESOLVE_CENTER_SLICES=True
BIG_LBL_RESOLVE_EDGES_SLICES=True

PUT_SOLVED_MARKERS=True

# Block-based solving for centers:
# 1 = single piece only (safe, equivalent to original algorithm)
# >1 = allow multi-cell blocks (optimization, may have edge cases)
LBL_MAX_BLOCK_SIZE = 100  # Effectively unlimited

# Maximum block width (columns) for the commutator.
# 0 = auto (n_slices // 2), >0 = explicit limit.
#
# THE n/2 GEOMETRIC LIMIT:
# ========================
# The commutator formula is:  M[cols] × F × M[rotated_cols]' × F'
# where M[cols] and M[rotated_cols] must be DISJOINT column sets.
#
# When a block is rotated 90° on an n×n grid, its column footprint
# collapses to a single column. That column must NOT overlap the
# original block's columns, otherwise M[cols] and M[rotated_cols]
# share a slice move and the 3-cycle breaks catastrophically:
# only the overlapping column gets the 3-cycle; all other columns
# get their pieces permanently moved to the source face.
#
# Example on 13×13 grid (15x15 cube), row 5:
#
#   VALID 7x1 (cols 0-6):          INVALID 8x1 (cols 0-7):
#
#   cols: 0 1 2 3 4 5 6 7          cols: 0 1 2 3 4 5 6 7
#        [X X X X X X X]  .               [X X X X X X X X] .
#                        ↑                              ↑
#   CCW rotation → col 7 ✓         CCW rotation → col 7 ✗
#   {7} ∩ {0..6} = ∅  OK!          {7} ∩ {0..7} = {7}  OVERLAP!
#
# The rotated column = n-1-row (CCW) or row (CW).
# At middle rows (~n/2), max non-overlapping width ≈ n/2.
# At edge rows (0 or n-1), width can reach n-1.
LBL_MAX_BLOCK_COLS = 0  # 0 = auto ((n_slices + 1) // 2)

PATCH_ORDER_ORTHOGONAL_FACES= False # to make bug reproducible even when we split the solution to two runs

TRACE_SOLVED_EDGES= False

