NUMBER_OF_SLICES_TO_SOLVE=10000  # 100000 to all
BIG_LBL_RESOLVE_CENTER_SLICES=True
BIG_LBL_RESOLVE_EDGES_SLICES=True

PUT_SOLVED_MARKERS=True

# Block-based solving for centers:
# 1 = single piece only (safe, equivalent to original algorithm)
# >1 = allow multi-cell blocks (optimization, may have edge cases)
LBL_MAX_BLOCK_SIZE = 100  # Effectively unlimited

PATCH_ORDER_ORTHOGONAL_FACES= False # to make bug reproducible even when we split the solution to two runs

TRACE_SOLVED_EDGES= False

