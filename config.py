SOLVER_DEBUG=True

SHORT_PART_NAME=False
DONT_OPTIMIZED_PART_ID=True
PRINT_CUBE_AS_TEXT_DURING_SOLVE=False

CHECK_CUBE_SANITY=False

animation_enabled=True

# Viewer
GUI_DRAW_MARKERS=False

CELL_SIZE: int = 30

CORNER_SIZE = 0.2  # relative to cell size (should be 1 in 3x3)

AXIS_LENGTH = 4 * CELL_SIZE


# Solver
OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS = False  # under test doesn't work well