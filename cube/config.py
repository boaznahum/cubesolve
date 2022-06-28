from typing import Tuple

######### Model  ########

SHORT_PART_NAME = False
DONT_OPTIMIZED_PART_ID = True
PRINT_CUBE_AS_TEXT_DURING_SOLVE = False

CHECK_CUBE_SANITY = False

# Only initial value, can be changed
CUBE_SIZE = 3

###### Operator ####

# Only initial value, can be changed
animation_enabled = True

######### Solvers  ########

SOLVER_DEBUG = True

######  Viewer ########
GUI_DRAW_MARKERS = False

CELL_SIZE: int = 30

CORNER_SIZE = 0.2  # relative to cell size (should be 1 in 3x3)

AXIS_LENGTH = 4 * CELL_SIZE

MAX_MARKER_RADIUS = 4.0  # when decreasing cube size, we don't want the markers become larger and larger

VIEWER_DRAW_SHADOWS = ""  # "LDB"

# MARKER_COLOR = (165,42,42) # brown	#A52A2A	rgb(165,42,42) https://www.rapidtables.com/web/color/brown-color.html
# MARKER_COLOR = (105,105,105) # dimgray / dimgray	#696969	rgb(105,105,105)
# MARKER_COLOR: Tuple[int, int, int] = (0, 0, 0)  # dimgray / dimgray	#696969	rgb(105,105,105)

MARKERS = {
    "C1": (199, 21, 133),  # mediumvioletred	#C71585	rgb(199,21,133),
    "C2": (0, 100, 0)  # darkgreen	#006400	rgb(0,100,0)
}

# text animation properties
ANIMATION_TEXT: list[Tuple[int, int, int, Tuple[int, int, int, int], bool]] = [
    # x, y from top, size, color, bold
    (10, 30, 20, (255, 255, 0, 255), True),
    (10, 55, 17, (255, 255, 255, 255), True),
    (10, 80, 14, (255, 255, 255, 255), False),
]

##############   Input handling

KEYBOAD_INPUT_DEBUG = True

#  If true, model rotating is done by dragging and right mouse click, rotating faces/slicing by dragging left bottom
#   or vice versa if FALSE
INPUT_MOUSE_MODEL_ROTATE_BY_DRAG_RIGHT_BOTTOM = True


############## Operator ##############
OPERATOR_SHOW_ALG_ANNOTATION=True

##############  Solver  ###################
OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS = True  # under test doesn't work well, see _todo
# Size 8 scramble 1:
# With  160
# Without: 140

OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES = True
OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES_ONLY_ZERO = True
OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_BLOCKS = True

PROF_VIEWER_SEARCH_FACET = False
PROF_VIEWER_GUI_UPDATE = False

##############  Testing
TEST_NUMBER_OF_SCRAMBLE_ITERATIONS = 10
