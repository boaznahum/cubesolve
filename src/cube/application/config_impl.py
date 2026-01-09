"""Configuration implementation - implements ConfigProtocol by wrapping _config.py.

This is the ONLY module allowed to import _config directly.
All other code must access config through ConfigProtocol via context (app.config or vs.config).
"""

from cube.application import _config as cfg
from cube.domain.model.Color import Color
from cube.utils.config_protocol import AnimationTextDef, ArrowConfigProtocol, ConfigProtocol, MarkerDef
from cube.utils.markers_config import MarkersConfig
from cube.utils.SSCode import SSCode


class AppConfig(ConfigProtocol):
    """Application config implementation wrapping _config.py values.

    Implements ConfigProtocol by delegating to the actual config module.
    This is the single point of access to _config values.
    """

    # ==========================================================================
    # Model settings
    # ==========================================================================
    @property
    def check_cube_sanity(self) -> bool:
        """Enable cube sanity checks."""
        return cfg.CHECK_CUBE_SANITY

    @check_cube_sanity.setter
    def check_cube_sanity(self, value: bool) -> None:
        """Set cube sanity check flag."""
        cfg.CHECK_CUBE_SANITY = value

    @property
    def short_part_name(self) -> bool:
        """Use short names for parts."""
        return cfg.SHORT_PART_NAME

    @property
    def dont_optimized_part_id(self) -> bool:
        """Disable part ID optimization."""
        return cfg.DONT_OPTIMIZED_PART_ID

    @property
    def print_cube_as_text_during_solve(self) -> bool:
        """Print cube state as text during solve."""
        return cfg.PRINT_CUBE_AS_TEXT_DURING_SOLVE

    @property
    def cube_size(self) -> int:
        """Default cube size."""
        return cfg.CUBE_SIZE

    @property
    def enable_cube_cache(self) -> bool:
        """Enable cube caching for performance optimization."""
        return cfg.ENABLE_CUBE_CACHE

    # ==========================================================================
    # Solver settings
    # ==========================================================================
    @property
    def default_solver(self) -> str:
        """Default solver name (case-insensitive, prefix matching allowed)."""
        return cfg.DEFAULT_SOLVER

    @property
    def solver_debug(self) -> bool:
        """Enable solver debug output."""
        return cfg.SOLVER_DEBUG

    @solver_debug.setter
    def solver_debug(self, value: bool) -> None:
        """Set solver debug flag."""
        cfg.SOLVER_DEBUG = value


    @property
    def solver_annotate_trackers(self) -> bool:
        """Annotate trackers during solve."""
        return cfg.SOLVER_ANNOTATE_TRACKERS

    @property
    def solver_pll_rotate_while_search(self) -> bool:
        """Rotate during PLL search."""
        return cfg.SOLVER_PLL_ROTATE_WHILE_SEARCH

    @property
    def solver_sanity_check_is_a_boy(self) -> bool:
        """Check if cube is in BOY orientation."""
        return cfg.SOLVER_SANITY_CHECK_IS_A_BOY

    @property
    def cage_3x3_solver(self) -> str:
        """3x3 solver used by cage method for corner solving (Phase 1b)."""
        return cfg.CAGE_3X3_SOLVER

    @property
    def first_face_color(self) -> Color:
        """First face color for Layer 1 in beginner and LBL solvers."""
        return cfg.FIRST_FACE_COLOR

    # ==========================================================================
    # Optimization settings
    # ==========================================================================
    @property
    def optimize_odd_cube_centers_switch_centers(self) -> bool:
        """Optimize odd cube center switching."""
        return cfg.OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS

    @property
    def optimize_big_cube_centers_search_complete_slices(self) -> bool:
        """Search for complete slices in big cube centers."""
        return cfg.OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES

    @property
    def optimize_big_cube_centers_search_complete_slices_only_target_zero(self) -> bool:
        """Only search complete slices for target zero."""
        return cfg.OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES_ONLY_TARGET_ZERO

    @property
    def optimize_big_cube_centers_search_blocks(self) -> bool:
        """Search for blocks in big cube centers."""
        return cfg.OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_BLOCKS

    # ==========================================================================
    # Viewer settings
    # ==========================================================================
    @property
    def cell_size(self) -> int:
        """Size of each cell in the viewer."""
        return cfg.CELL_SIZE

    @property
    def corner_size(self) -> float:
        """Relative corner size (to cell size)."""
        return cfg.CORNER_SIZE

    @property
    def axis_enabled(self) -> bool:
        """Master switch for axis drawing - when False, no axis code runs."""
        return cfg.AXIS_ENABLED

    @property
    def axis_length(self) -> float:
        """Length of axis display."""
        return cfg.AXIS_LENGTH

    @property
    def max_marker_radius(self) -> float:
        """Maximum radius for markers."""
        return cfg.MAX_MARKER_RADIUS

    @property
    def viewer_max_size_for_texture(self) -> int:
        """Maximum cube size for texture rendering."""
        return cfg.VIEWER_MAX_SIZE_FOR_TEXTURE

    @property
    def viewer_draw_shadows(self) -> str:
        """Faces to draw shadows for (e.g., 'LDB')."""
        return cfg.VIEWER_DRAW_SHADOWS

    @property
    def viewer_trace_draw_update(self) -> bool:
        """Trace draw/update calls."""
        return cfg.VIEWER_TRACE_DRAW_UPDATE

    @property
    def prof_viewer_search_facet(self) -> bool:
        """Profile facet search."""
        return cfg.PROF_VIEWER_SEARCH_FACET

    @property
    def markers(self) -> dict[str, MarkerDef]:
        """Marker definitions by name."""
        return cfg.MARKERS  # type: ignore[return-value]

    @property
    def arrow_config(self) -> ArrowConfigProtocol:
        """Get 3D arrow configuration for solver annotations."""
        return cfg.ARROW_CONFIG

    # ==========================================================================
    # GUI settings
    # ==========================================================================
    @property
    def markers_config(self) -> MarkersConfig:
        """Get markers configuration (draw flags for various marker types)."""
        return cfg.MARKERS_CONFIG

    @property
    def gui_test_mode(self) -> bool:
        """GUI testing mode - exceptions propagate."""
        return cfg.GUI_TEST_MODE

    @property
    def quit_on_error_in_test_mode(self) -> bool:
        """Quit application on error in test mode."""
        return cfg.QUIT_ON_ERROR_IN_TEST_MODE

    @property
    def animation_text(self) -> list[AnimationTextDef]:
        """Animation text display properties."""
        return cfg.ANIMATION_TEXT  # type: ignore[return-value]

    @property
    def animation_enabled(self) -> bool:
        """Whether animation is enabled by default."""
        return cfg.animation_enabled

    @property
    def animation_speed(self) -> int:
        """Default animation speed index (0-7, higher is faster)."""
        # Clamp to valid range (0-7)
        return max(0, min(7, cfg.ANIMATION_SPEED))

    # ==========================================================================
    # Texture settings
    # ==========================================================================
    @property
    def texture_sets(self) -> list[str | None] | None:
        """List of texture set names to cycle through."""
        return cfg.TEXTURE_SETS

    @property
    def texture_set_index(self) -> int:
        """Initial texture set index."""
        return cfg.TEXTURE_SET_INDEX

    @property
    def debug_texture(self) -> bool:
        """Enable texture debug output."""
        return cfg.DEBUG_TEXTURE

    # ==========================================================================
    # Lighting settings
    # ==========================================================================
    @property
    def lighting_brightness(self) -> float:
        """Default brightness level."""
        return cfg.LIGHTING_BRIGHTNESS

    @property
    def lighting_background(self) -> float:
        """Default background gray level."""
        return cfg.LIGHTING_BACKGROUND

    # ==========================================================================
    # Celebration settings
    # ==========================================================================
    @property
    def celebration_effect(self) -> str:
        """Default celebration effect name."""
        return cfg.CELEBRATION_EFFECT

    @property
    def celebration_enabled(self) -> bool:
        """Whether celebration effects are enabled."""
        return cfg.CELEBRATION_ENABLED

    @property
    def celebration_duration(self) -> float:
        """Celebration effect duration in seconds."""
        return cfg.CELEBRATION_DURATION

    # ==========================================================================
    # Operator settings
    # ==========================================================================
    @property
    def operation_log(self) -> bool:
        """Enable operation logging."""
        return cfg.OPERATION_LOG

    @property
    def operation_log_path(self) -> str:
        """Path for operation log file."""
        return cfg.OPERATION_LOG_PATH

    @property
    def operator_show_alg_annotation(self) -> bool:
        """Show algorithm annotations."""
        return cfg.OPERATOR_SHOW_ALG_ANNOTATION

    # ==========================================================================
    # Testing settings
    # ==========================================================================
    @property
    def scramble_key_for_f9(self) -> int:
        """Scramble key for F9 shortcut."""
        return cfg.SCRAMBLE_KEY_FOR_F9

    @property
    def test_number_of_scramble_iterations(self) -> int:
        """Number of scramble iterations for tests."""
        return cfg.TEST_NUMBER_OF_SCRAMBLE_ITERATIONS

    @property
    def last_scramble_path(self) -> str:
        """Path for last scramble file."""
        return cfg.LAST_SCRAMBLE_PATH

    # ==========================================================================
    # Mouse input settings
    # ==========================================================================
    @property
    def input_mouse_debug(self) -> bool:
        """Enable mouse input debug output."""
        return cfg.INPUT_MOUSE_DEBUG

    @property
    def input_mouse_model_rotate_by_drag_right_bottom(self) -> bool:
        """Model rotation by dragging right/bottom."""
        return cfg.INPUT_MOUSE_MODEL_ROTATE_BY_DRAG_RIGHT_BOTTOM

    @property
    def input_mouse_rotate_adjusted_face(self) -> bool:
        """Rotate adjusted face on edge/corner drag."""
        return cfg.INPUT_MOUSE_ROTATE_ADJUSTED_FACE

    # ==========================================================================
    # Single-step mode settings
    # ==========================================================================
    def is_ss_code_enabled(self, code: SSCode) -> bool:
        """Check if a single-step mode code is enabled.

        Args:
            code: The SSCode to check

        Returns:
            True if the code is enabled in SS_CODES config, False otherwise
        """
        return cfg.SS_CODES.get(code, False)

    # ==========================================================================
    # Debug/Logging settings
    # ==========================================================================
    @property
    def quiet_all(self) -> bool:
        """Suppress all debug output."""
        return cfg.QUIET_ALL

    @quiet_all.setter
    def quiet_all(self, value: bool) -> None:
        """Set quiet_all mode."""
        cfg.QUIET_ALL = value

    @property
    def debug_all(self) -> bool:
        """Enable all debug output."""
        return cfg.DEBUG_ALL

    @debug_all.setter
    def debug_all(self, value: bool) -> None:
        """Set debug_all mode."""
        cfg.DEBUG_ALL = value
