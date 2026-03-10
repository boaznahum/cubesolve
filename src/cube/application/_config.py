"""
PRIVATE MODULE - DO NOT IMPORT DIRECTLY!

This module contains configuration values for the application. It is intentionally
named with a leading underscore to indicate it is private to the application package.

To access configuration values from outside the application package:
1. Use the ConfigProtocol via cube.config property (preferred for domain/presentation layers)
2. Import as `from cube.application import _config as config` (for tests only)

DO NOT use `from cube.application._config import X` in production code.
Access config values through the ConfigProtocol interface instead.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Tuple

from cube.config.face_tracer_config import FaceTrackerConfig, TrackerIndicatorConfig
from cube.utils.markers_config import MarkersConfig

########## Per-session mutable configuration ##########
# ConfigData holds fields that can vary per client session.
# Each session gets its own copy; changes don't leak across sessions.

# Type alias for config change listener callback
ConfigListener = object  # Callable[[str, object], None] — avoid import cycle


@dataclass
class ConfigData:
    """Mutable per-session configuration fields.

    Each client session gets its own copy (via copy()).
    Listeners are notified when fields change via set_* methods.
    """
    solver_debug: bool = True
    operator_buffer_mode: bool = True
    queue_heading_h1: bool = True
    queue_heading_h2: bool = True

    # Listeners are NOT copied — each session registers its own
    _listeners: list[ConfigListener] = field(default_factory=list, repr=False, compare=False)

    def copy(self) -> ConfigData:
        """Create a copy with empty listener list."""
        new = copy.copy(self)
        new._listeners = []
        return new

    def add_listener(self, listener: ConfigListener) -> None:
        """Register a callback(field_name: str, new_value: object) for changes."""
        self._listeners.append(listener)

    def remove_listener(self, listener: ConfigListener) -> None:
        """Unregister a change listener."""
        self._listeners.remove(listener)

    def _notify(self, field_name: str, value: object) -> None:
        """Notify all listeners of a field change."""
        for listener in self._listeners:
            listener(field_name, value)  # type: ignore[operator]

    def set_solver_debug(self, value: bool) -> None:
        """Set solver_debug and notify listeners."""
        if self.solver_debug != value:
            self.solver_debug = value
            self._notify("solver_debug", value)

    def set_operator_buffer_mode(self, value: bool) -> None:
        """Set operator_buffer_mode and notify listeners."""
        if self.operator_buffer_mode != value:
            self.operator_buffer_mode = value
            self._notify("operator_buffer_mode", value)

    def set_queue_heading_h1(self, value: bool) -> None:
        """Set queue_heading_h1 and notify listeners."""
        if self.queue_heading_h1 != value:
            self.queue_heading_h1 = value
            self._notify("queue_heading_h1", value)

    def set_queue_heading_h2(self, value: bool) -> None:
        """Set queue_heading_h2 and notify listeners."""
        if self.queue_heading_h2 != value:
            self.queue_heading_h2 = value
            self._notify("queue_heading_h2", value)


# Module-level default instance — used as template for new sessions
DEFAULT_CONFIG_DATA = ConfigData()


########## Some top important
# Only initial value, can be changed
CUBE_SIZE = 3

# Enable cube caching for performance optimization
# Env override: CUBE_DISABLE_CACHE=1 to disable
ENABLE_CUBE_CACHE = True
PREVENT_RANDOM_FACE_PICK_UP_IN_GEOMETRY=False

# Default solver name - case-insensitive, prefix matching allowed if unambiguous
# Available solvers: Beginner Reducer, CFOP, Kociemba, Cage, Big LBL
# Examples: "beginner", "cf" (for CFOP), "k" (for Kociemba), "big" (for Big LBL)
# Note: Keep this list in sync with SolverName enum in src/cube/domain/solver/SolverName.py
#DEFAULT_SOLVER = "Kociemba"
DEFAULT_SOLVER = "Beginner Reducer"

# Solver used by tests (must be implemented - raises error if not)
# Tests use this instead of DEFAULT_SOLVER to avoid failures when DEFAULT_SOLVER
# is set to a work-in-progress solver
SOLVER_FOR_TESTS = "Beginner Reducer"

# D2efault 2x2 solver — used when any 3x3+ solver is asked to solve a 2x2 cube
# Options: "2x2 Beginner", "2x2 IDA*"
# Note: Keep in sync with SolverName enum in src/cube/domain/solver/SolverName.py
DEFAULT_2X2_SOLVER = "2x2 Beginner" # "2x2 IDA*"

# 3x3 solver used by cage method for corner solving (Phase 1b)
# Options: "beginner", "cfop", "kociemba"
CAGE_3X3_SOLVER = "cfop"

######### Model  ########


SHORT_PART_NAME = False
DONT_OPTIMIZED_PART_ID = False
PRINT_CUBE_AS_TEXT_DURING_SOLVE = False

CHECK_CUBE_SANITY = False


######### Solvers  Solvers Solvers Solvers########

# First face color - the color that determines Layer 1 for 3x3 beginner and LBL solvers
# This is the color to start with, not a fixed face position (cube may be rotated)
# Used by: 3x3 beginner solver, Reducer cube solver
from cube.domain.model.Color import Color as _Color  # noqa: E402

#L1 color
FIRST_FACE_COLOR: _Color = _Color.WHITE


############## Operator ##############
OPERATOR_SHOW_ALG_ANNOTATION = True

# Buffer mode - when enabled, op.with_buffer() buffers moves and simplifies on flush.
# When disabled, op.with_buffer() is a transparent no-op (moves play immediately).
# Disable to isolate bugs: "is this a buffer bug or a solver bug?"
OPERATOR_BUFFER_MODE = True

# Queue heading visibility — controls which heading levels appear in WebGL queue display
QUEUE_HEADING_H1 = True   # Show h1 headings (solver phase names)
QUEUE_HEADING_H2 = True  # Show h2 headings (sub-step details)

##############  Solver  ##################

SOLVER_DEBUG = True

OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS = False  # under test doesn't work well

OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES = True
OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES_ONLY_TARGET_ZERO = True
OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_BLOCKS = True

SOLVER_SANITY_CHECK_IS_A_BOY = False # NON-DEFAULT

LBL_SANITY_CHECK = False  # performance


##############  FaceTracer  ##################

FACE_TRACKER = FaceTrackerConfig(
    annotate=True,
    validate=False,  # various  validations, performance cost
    leave_last_annotation=True,
    use_simple_f5_tracker=True,  # no longer used
    enable_track_piece_caching=True,  # PERFORMANCE: 4.82x speedup (35s vs 170s on 1080 tests)
)

SOLVER_PLL_ROTATE_WHILE_SEARCH = False

###### Operator   and  Animation ####

# Only initial value, can be changed
animation_enabled = True

################ WebGL

@dataclass
class AnimationSpeedConfig:
    """Animation speed parameters for WebGL frontend.

    Speed is computed as: d0 * (dn / d0) ** (index / 7.0)
    """
    # Default speed index (0-7, higher is faster)
    default_index: float = 2
    # Step size between adjacent speed dropdown options
    step: float = 0.5
    # Duration (ms) at speed index 0 (slowest)
    d0: float = 2000
    # Duration (ms) at speed index 7 (fastest)
    dn: float = 50
    # Timeout (seconds) for blocking mode wait — prevents permanent hang
    # if WebSocket dies without reconnect
    blocking_timeout: float = 60.0


ANIMATION_SPEED_CONFIG = AnimationSpeedConfig()


@dataclass
class AssistConfig:
    """Assist mode configuration for WebGL frontend.

    When enabled, shows a brief move indicator before each animation.
    """
    # Whether assist is enabled by default
    enabled: bool = True
    # Duration (ms) of the move indicator preview
    delay_ms: int = 400


ASSIST_CONFIG = AssistConfig()


@dataclass
class SoundConfig:
    """Sound effects configuration for WebGL frontend.

    When enabled, plays a procedural click/whir sound on each cube rotation.
    """
    # Whether sound is enabled by default
    enabled: bool = False


SOUND_CONFIG = SoundConfig()

# Single-step mode codes - enable specific breakpoints for debugging
# Import SSCode here to avoid circular imports (config is loaded early)
from cube.utils.SSCode import SSCode  # noqa: E402

SS_CODES: dict[SSCode, bool] = {
    SSCode.NxN_CORNER_PARITY_FIX: False,  # Pause before corner parity fix
    SSCode.NxN_EDGE_PARITY_FIX: False,
    SSCode.REDUCER_CENTERS_DONE: False,
    SSCode.REDUCER_EDGES_DONE: False,
    SSCode.L1_CROSS_DONE: False,
    SSCode.L1_CORNERS_DONE: False,
    SSCode.L2_DONE: False,
    SSCode.L3_CROSS_DONE: False,
    SSCode.L3_CORNERS_DONE: False,
    SSCode.F2L_WIDE_MOVE: False,  # Pause before wide move in F2L
}



######  Viewer ########

# Full mode - hides toolbar and status text, showing only 3D cube + animation annotations
FULL_MODE = False


VIEWER_MAX_SIZE_FOR_TEXTURE = 10  # All works but very slow

VIEWER_TRACE_DRAW_UPDATE = False

PROF_VIEWER_SEARCH_FACET = False

# Marker configuration - all marker-related flags in one place
MARKERS_CONFIG = MarkersConfig()

MARKERS_CONFIG.GUI_DRAW_MARKERS = False
MARKERS_CONFIG.GUI_DRAW_SAMPLE_MARKERS = False
MARKERS_CONFIG.GUI_DRAW_LTR_ORIGIN_ARROWS = True  # Draw LTR coordinate system markers (origin, X arrow, Y arrow)
MARKERS_CONFIG.DRAW_CENTER_INDEXES = False  # Draw center index markers during rotation (SLOW - debug only)

# Tracker indicator (colored circle on tracked center slices for even cubes)
TRACKER_INDICATOR = TrackerIndicatorConfig()

CELL_SIZE: int = 30

CORNER_SIZE = 0.2  # relative to cell size (should be 1 in 3x3)

AXIS_ENABLED = False  # Master switch for axis drawing - when False, no axis code runs
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
    "C0": ((199, 21, 133), 1.0, 0.8, 0.1),  # mediumvioletred	#C71585	rgb(199,21,133)
    "C1": ((199, 21, 133), 0.6, 1, 0.1),  # mediumvioletred	#C71585	rgb(199,21,133),
    "C2": ((0, 100, 0), 1.0, 0.3, 0.1)  # darkgreen	#006400	rgb(0,100,0)
}


################ 3D Arrows (source-to-destination direction indicators)


@dataclass
class ArrowConfig:
    """Configuration for 3D arrows showing source-to-destination direction.

    Access via ConfigProtocol.arrow_config property.
    """
    # Master switch to enable/disable 3D arrows
    enabled: bool = False

    # Arrow style: "simple" (straight), "curved" (bezier), "compound" (multiple segments)
    style: str = "simple"

    # Arrow animation: "grow" (extends from source), "fade" (fades in), "none" (instant)
    animation: str = "grow"

    # Arrow head style: "cone" (3D cone), "pyramid" (3D pyramid), "flat" (2D triangle)
    head_style: str = "cone"

    # Arrow color (RGB 0.0-1.0) - bright gold to stand out from markers
    color: Tuple[float, float, float] = (1.0, 0.78, 0.0)

    # Arrow geometry
    shaft_radius: float = 2.0  # Radius of arrow shaft cylinder
    head_radius: float = 5.0  # Radius of cone base
    head_length: float = 12.0  # Length of cone/head
    height_offset: float = 25.0  # Height above cube surface (floating effect)
    animation_duration: float = 0.5  # Seconds for grow animation
    segments: int = 16  # Smoothness of cylinders


# Default arrow configuration instance - modify this to change arrow settings
ARROW_CONFIG = ArrowConfig()

# text animation properties
ANIMATION_TEXT: list[Tuple[int, int, int, Tuple[int, int, int, int], bool]] = [
    # x, y from top, size, color, bold
    (10, 30, 20, (255, 255, 0, 255), True),
    (10, 55, 17, (255, 255, 255, 255), True),
    (10, 80, 14, (255, 255, 255, 255), False),
]

##############   Input handling

KEYBOAD_INPUT_DEBUG = False

# GUI Testing mode - when enabled, exceptions in GUI loop propagate and app quits on error
GUI_TEST_MODE = False
QUIT_ON_ERROR_IN_TEST_MODE = True

# Show F1-F5 file algorithm buttons in toolbar
SHOW_FILE_ALGS = True

#  If true, model rotating is done by dragging and right mouse click, rotating faces/slicing by dragging left bottom
#   or vice versa if FALSE
INPUT_MOUSE_MODEL_ROTATE_BY_DRAG_RIGHT_BOTTOM = True

# When dragging edge or corner, rotate adjusted face, and not the same face
INPUT_MOUSE_ROTATE_ADJUSTED_FACE = True

INPUT_MOUSE_DEBUG = False


##############  Testing
TEST_NUMBER_OF_SCRAMBLE_ITERATIONS = 20
AGGRESSIVE_TEST_NUMBER_SIZES = [3, 6, 7]
#AGGRESSIVE_TEST_NUMBER__SIZES = [6,]
AGGRESSIVE_TEST_NUMBER_OF_SCRAMBLE_START = 0
AGGRESSIVE_TEST_NUMBER_OF_SCRAMBLE_ITERATIONS = 100 * len(AGGRESSIVE_TEST_NUMBER_SIZES)
SCRAMBLE_KEY_FOR_F9 = int(203)  # should be replaced by persisting of last test

##############  Testing aggressive 2
AGGRESSIVE_2_TEST_NUMBER_SIZES = [3, 6, 7]
#AGGRESSIVE_2_TEST_SOLVERS = SolverName.all()
AGGRESSIVE_2_TEST_NUMBER_OF_SCRAMBLE_START = 0
AGGRESSIVE_2_TEST_NUMBER_OF_SCRAMBLE_ITERATIONS = 100  # per solver and size

################ Logging
OPERATION_LOG = False
OPERATION_LOG_PATH = ".logs/operation.log"
LAST_SCRAMBLE_PATH = ".logs/last_scramble.txt"

################ Celebration Effects
# Available effects: "none", "confetti", "victory_spin", "sparkle", "glow", "combo"
CELEBRATION_EFFECTS = ["none", "confetti", "victory_spin", "sparkle", "glow", "combo"]
CELEBRATION_EFFECT = "combo"  # Default effect
CELEBRATION_ENABLED = False
CELEBRATION_DURATION = 3.0  # seconds

################ Lighting (pyglet2 backend only)
# Brightness: ambient light level (0.1 = dark, 1.0 = normal, 1.5 = overbright)
LIGHTING_BRIGHTNESS = 0.65  # Default ambient light level
# Background: gray level for window background (0.0 = black, 0.5 = gray)
LIGHTING_BACKGROUND = 0.15  # Default background (black)

################ Textures (pyglet2 backend only)
# List of texture sets to cycle through with Ctrl+Shift+T
# Can be preset names ("set1", "family"), paths, or None for solid colors
# Ctrl+Shift+T cycles: debug4x4 → debug3x3 → arrows → ... → None (solid) → debug4x4 → ...
TEXTURE_SETS: list[str | None] | None = [None, "debug4x4", "debug3x3", "arrows", "family", "letters", "numbers", "set2"]
# Index of initial texture set (0 = first in list, or None to start with solid colors)
TEXTURE_SET_INDEX: int = 0  # Start with debug4x4 for 4x4 cube debugging
# Debug texture loading/assignment (controlled by vs.debug with this flag)
DEBUG_TEXTURE: bool = False


################ Deploy

@dataclass
class SessionConfig:
    """WebGL session configuration."""
    # How long (seconds) to keep a disconnected WebSocket session alive.
    # If the client reconnects within this window, their cube state is restored.
    # Set to 0 to disable server-side session keep-alive.
    keepalive_timeout: int = 30 * 60  # 30 minutes


SESSION_CONFIG = SessionConfig()
