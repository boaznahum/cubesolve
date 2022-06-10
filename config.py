from typing import Tuple

SOLVER_DEBUG = True

SHORT_PART_NAME = False
DONT_OPTIMIZED_PART_ID = True
PRINT_CUBE_AS_TEXT_DURING_SOLVE = False

CHECK_CUBE_SANITY = False

animation_enabled = True

# Viewer
GUI_DRAW_MARKERS = False

CELL_SIZE: int = 30

CORNER_SIZE = 0.2  # relative to cell size (should be 1 in 3x3)

AXIS_LENGTH = 4 * CELL_SIZE

MAX_MARKER_RADIUS = 4.0  # when decreasing cube size, we don't want the markers become larger and larger

#MARKER_COLOR = (165,42,42) # brown	#A52A2A	rgb(165,42,42) https://www.rapidtables.com/web/color/brown-color.html
#MARKER_COLOR = (105,105,105) # dimgray / dimgray	#696969	rgb(105,105,105)
MARKER_COLOR:Tuple[int, int, int] = (0,0,0) # dimgray / dimgray	#696969	rgb(105,105,105)

# Solver
OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS = False  # under test doesn't work well, see _todo
