from typing import Tuple

######### Model  ########

# Only initial value, can be changed
CUBE_SIZE = 6

SHORT_PART_NAME = False
DONT_OPTIMIZED_PART_ID = False
PRINT_CUBE_AS_TEXT_DURING_SOLVE = False

CHECK_CUBE_SANITY = False

###### Operator ####

# Only initial value, can be changed
animation_enabled = True

######### Solvers  ########

SOLVER_DEBUG = True

CFOP=False

######  Viewer ########


VIEWER_MAX_SIZE_FOR_TEXTURE=10  # All works but very slow


VIEWER_TRACE_DRAW_UPDATE=False

PROF_VIEWER_SEARCH_FACET = False


GUI_DRAW_MARKERS = False
GUI_DRAW_SAMPLE_MARKERS = False

CELL_SIZE: int = 30

CORNER_SIZE = 0.2  # relative to cell size (should be 1 in 3x3)

AXIS_LENGTH = 4 * CELL_SIZE

MAX_MARKER_RADIUS = 5.0  # when decreasing cube size, we don't want the markers become larger and larger

VIEWER_DRAW_SHADOWS = ""  # "LDB"

# MARKER_COLOR = (165,42,42) # brown	#A52A2A	rgb(165,42,42) https://www.rapidtables.com/web/color/brown-color.html
# MARKER_COLOR = (105,105,105) # dimgray / dimgray	#696969	rgb(105,105,105)
# MARKER_COLOR: Tuple[int, int, int] = (0, 0, 0)  # dimgray / dimgray	#696969	rgb(105,105,105)

MARKERS = {
    #      color           r-outer thick, height (of cylinder)
    #      radius is - relative to marker size [0.0-1.0]
    #      thick is relative to outer radius , inner - (1-thick)*outer
    #      height in model resolution, +- above/below facet
    "C0": ((199, 21, 133), 1.0, 0.8, 0.1), # mediumvioletred	#C71585	rgb(199,21,133)
    "C1": ((199, 21, 133), 0.6, 1, 0.1), # mediumvioletred	#C71585	rgb(199,21,133),
    "C2": ((0, 100, 0), 1.0, 0.3, 0.1)  # darkgreen	#006400	rgb(0,100,0)
}

# text animation properties
ANIMATION_TEXT: list[Tuple[int, int, int, Tuple[int, int, int, int], bool]] = [
    # x, y from top, size, color, bold
    (10, 30, 20, (255, 255, 0, 255), True),
    (10, 55, 17, (255, 255, 255, 255), True),
    (10, 80, 14, (255, 255, 255, 255), False),
]

##############   Input handling

KEYBOAD_INPUT_DEBUG = False

#  If true, model rotating is done by dragging and right mouse click, rotating faces/slicing by dragging left bottom
#   or vice versa if FALSE
INPUT_MOUSE_MODEL_ROTATE_BY_DRAG_RIGHT_BOTTOM = True

# When dragging edge or corner, rotate adjusted face, and not the same face
INPUT_MOUSE_ROTATE_ADJUSTED_FACE= True

INPUT_MOUSE_DEBUG= False

############## Operator ##############
OPERATOR_SHOW_ALG_ANNOTATION = True

##############  Solver  ###################
OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS = False  # under test doesn't work well

OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES = False  # still fails on even, make it not biy, probably move tracers
OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES_ONLY_ZERO = True
OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_BLOCKS = True

SOLVER_SANITY_CHECK_IS_A_BOY = False

SOLVER_ANNOTATE_TRACKERS = False

##############  Testing
TEST_NUMBER_OF_SCRAMBLE_ITERATIONS = 20
AGGRESSIVE_TEST_NUMBER_OF_SCRAMBLE_START = 28
AGGRESSIVE_TEST_NUMBER_OF_SCRAMBLE_ITERATIONS = 300
SCRAMBLE_KEY_FOR_F9 = int(77)  # should be replaced by persist of last test

################ Logging
OPERATION_LOG = False
OPERATION_LOG_PATH = ".logs/operation.log"
LAST_SCRAMBLE_PATH = ".logs/last_scramble.txt"
