"""Configuration implementation - implements ConfigProtocol by wrapping _config.py.

This is the ONLY module allowed to import _config directly.
All other code must access config through ConfigProtocol via context (app.config or vs.config).

Environment Variables:
    CUBE_DISABLE_CACHE: Set to "1", "true", or "yes" to disable cube caching.
"""

import os

from cube.application import _config as cfg
from cube.config.face_tracer_config import FaceTrackerConfig, TrackerIndicatorConfig
from cube.domain.model.Color import Color
from cube.utils.config_protocol import (
    AnimationSpeedConfigProtocol, AnimationTextDef, ArrowConfigProtocol,
    AssistConfigProtocol, ConfigProtocol, MarkerDef, SessionConfigProtocol,
    SoundConfigProtocol,
)
from cube.utils.markers_config import MarkersConfig
from cube.utils.SSCode import SSCode


def _env_bool(name: str) -> bool | None:
    """Get boolean value from environment variable, or None if not set."""
    val = os.environ.get(name, "").lower()
    if val in ("1", "true", "yes"):
        return True
    if val in ("0", "false", "no"):
        return False
    return None


class AppConfig(ConfigProtocol):
    """Application config implementation wrapping _config.py values.

    Implements ConfigProtocol by delegating to a per-session ConfigData instance.
    Each session gets its own copy so changes don't leak across sessions.

    ConfigData is populated from the current module-level constants at creation
    time, so tests that set cfg.X = value before creating an AppConfig get the
    right values.
    """

    def __init__(self) -> None:
        self._data = cfg.CONFIG_DEFAULTS.copy()

    # ==========================================================================
    # Model settings
    # ==========================================================================
    @property
    def check_cube_sanity(self) -> bool:
        """Enable cube sanity checks."""
        return self._data.check_cube_sanity

    @check_cube_sanity.setter
    def check_cube_sanity(self, value: bool) -> None:
        """Set cube sanity check flag."""
        self._data.check_cube_sanity = value

    @property
    def short_part_name(self) -> bool:
        """Use short names for parts."""
        return self._data.short_part_name

    @property
    def dont_optimized_part_id(self) -> bool:
        """Disable part ID optimization."""
        return self._data.dont_optimized_part_id

    @property
    def print_cube_as_text_during_solve(self) -> bool:
        """Print cube state as text during solve."""
        return self._data.print_cube_as_text_during_solve

    @property
    def cube_size(self) -> int:
        """Default cube size."""
        return self._data.cube_size

    @property
    def enable_cube_cache(self) -> bool:
        """Enable cube caching for performance optimization.

        Can be disabled by setting CUBE_DISABLE_CACHE=1 environment variable.
        """
        env_disable = _env_bool("CUBE_DISABLE_CACHE")
        if env_disable is not None:
            return not env_disable  # DISABLE_CACHE=1 → enable=False
        return self._data.enable_cube_cache

    @property
    def prevent_random_face_pick_up_in_geometry(self) -> bool:
        """Prevent random face selection in geometry walking (debug flag)."""
        return self._data.prevent_random_face_pick_up_in_geometry

    # ==========================================================================
    # Solver settings
    # ==========================================================================
    @property
    def default_solver(self) -> str:
        """Default solver name (case-insensitive, prefix matching allowed)."""
        return self._data.default_solver

    @property
    def solver_for_tests(self) -> str:
        """Solver name for tests (must be implemented).

        Raises:
            RuntimeError: If the configured test solver is not implemented.
        """
        from cube.domain.solver.SolverName import SolverName
        solver_name = self._data.solver_for_tests
        try:
            solver = SolverName.lookup(solver_name)
            if not solver.meta.implemented:
                raise RuntimeError(
                    f"SOLVER_FOR_TESTS='{solver_name}' is not implemented. "
                    f"Please set SOLVER_FOR_TESTS to an implemented solver. "
                    f"Implemented solvers: {', '.join(s.display_name for s in SolverName.implemented())}"
                )
            return solver_name
        except ValueError as e:
            raise RuntimeError(f"Invalid SOLVER_FOR_TESTS='{solver_name}': {e}") from e

    @property
    def solver_debug(self) -> bool:
        """Enable solver debug output."""
        return self._data.solver_debug

    @solver_debug.setter
    def solver_debug(self, value: bool) -> None:
        """Set solver debug flag."""
        self._data.set_solver_debug(value)

    @property
    def solver_pll_rotate_while_search(self) -> bool:
        """Rotate during PLL search."""
        return self._data.solver_pll_rotate_while_search

    @property
    def face_tracker(self) -> FaceTrackerConfig:
        """Face tracker configuration (annotations, validation)."""
        return self._data.face_tracker

    @property
    def solver_sanity_check_is_a_boy(self) -> bool:
        """Check if cube is in BOY orientation."""
        return self._data.solver_sanity_check_is_a_boy

    @property
    def lbl_sanity_check(self) -> bool:
        """Enable LBL solver sanity checks (performance impact)."""
        return self._data.lbl_sanity_check

    @property
    def default_2x2_solver(self) -> str:
        """Default 2x2 solver used when a 3x3+ solver is asked to solve a 2x2."""
        return self._data.default_2x2_solver

    @property
    def cage_3x3_solver(self) -> str:
        """3x3 solver used by cage method for corner solving (Phase 1b)."""
        return self._data.cage_3x3_solver

    @property
    def first_face_color(self) -> Color:
        """First face color for Layer 1 in beginner and LBL solvers."""
        return self._data.first_face_color

    # ==========================================================================
    # Optimization settings
    # ==========================================================================
    @property
    def optimize_odd_cube_centers_switch_centers(self) -> bool:
        """Optimize odd cube center switching."""
        return self._data.optimize_odd_cube_centers_switch_centers

    @property
    def optimize_big_cube_centers_search_complete_slices(self) -> bool:
        """Search for complete slices in big cube centers."""
        return self._data.optimize_big_cube_centers_search_complete_slices

    @property
    def optimize_big_cube_centers_search_complete_slices_only_target_zero(self) -> bool:
        """Only search complete slices for target zero."""
        return self._data.optimize_big_cube_centers_search_complete_slices_only_target_zero

    @property
    def optimize_big_cube_centers_search_blocks(self) -> bool:
        """Search for blocks in big cube centers."""
        return self._data.optimize_big_cube_centers_search_blocks

    # ==========================================================================
    # Viewer settings
    # ==========================================================================
    @property
    def cell_size(self) -> int:
        """Size of each cell in the viewer."""
        return self._data.cell_size

    @property
    def corner_size(self) -> float:
        """Relative corner size (to cell size)."""
        return self._data.corner_size

    @property
    def axis_enabled(self) -> bool:
        """Master switch for axis drawing - when False, no axis code runs."""
        return self._data.axis_enabled

    @property
    def axis_length(self) -> float:
        """Length of axis display."""
        return self._data.axis_length

    @property
    def max_marker_radius(self) -> float:
        """Maximum radius for markers."""
        return self._data.max_marker_radius

    @property
    def viewer_max_size_for_texture(self) -> int:
        """Maximum cube size for texture rendering."""
        return self._data.viewer_max_size_for_texture

    @property
    def tracker_indicator(self) -> TrackerIndicatorConfig:
        """Tracker indicator configuration (colored circle on tracked center slices)."""
        return self._data.tracker_indicator

    @property
    def viewer_draw_shadows(self) -> str:
        """Faces to draw shadows for (e.g., 'LDB')."""
        return self._data.viewer_draw_shadows

    @property
    def viewer_trace_draw_update(self) -> bool:
        """Trace draw/update calls."""
        return self._data.viewer_trace_draw_update

    @property
    def prof_viewer_search_facet(self) -> bool:
        """Profile facet search."""
        return self._data.prof_viewer_search_facet

    @property
    def markers(self) -> dict[str, MarkerDef]:
        """Marker definitions by name."""
        return self._data.markers  # type: ignore[return-value]

    @property
    def arrow_config(self) -> ArrowConfigProtocol:
        """Get 3D arrow configuration for solver annotations."""
        return self._data.arrow_config

    # ==========================================================================
    # GUI settings
    # ==========================================================================
    @property
    def markers_config(self) -> MarkersConfig:
        """Get markers configuration (draw flags for various marker types)."""
        return self._data.markers_config

    @property
    def gui_test_mode(self) -> bool:
        """GUI testing mode - exceptions propagate."""
        return self._data.gui_test_mode

    @property
    def quit_on_error_in_test_mode(self) -> bool:
        """Quit application on error in test mode."""
        return self._data.quit_on_error_in_test_mode

    @property
    def animation_text(self) -> list[AnimationTextDef]:
        """Animation text display properties."""
        return self._data.animation_text  # type: ignore[return-value]

    @property
    def animation_enabled(self) -> bool:
        """Whether animation is enabled by default."""
        return self._data.animation_enabled

    @property
    def animation_speed_config(self) -> AnimationSpeedConfigProtocol:
        """Animation speed parameters for WebGL frontend."""
        return self._data.animation_speed_config

    @property
    def assist_config(self) -> AssistConfigProtocol:
        """Assist mode configuration for WebGL frontend."""
        return self._data.assist_config

    @property
    def sound_config(self) -> SoundConfigProtocol:
        """Sound effects configuration for WebGL frontend."""
        return self._data.sound_config

    @property
    def session_config(self) -> SessionConfigProtocol:
        """WebGL session configuration (keepalive timeout, etc.)."""
        return self._data.session_config

    @property
    def show_file_algs(self) -> bool:
        """Show F1-F5 file algorithm buttons in toolbar."""
        return self._data.show_file_algs

    @property
    def full_mode(self) -> bool:
        """Whether app starts in full mode (hides toolbar/status text)."""
        return self._data.full_mode

    # ==========================================================================
    # Texture settings
    # ==========================================================================
    @property
    def texture_sets(self) -> list[str | None] | None:
        """List of texture set names to cycle through."""
        return self._data.texture_sets

    @property
    def texture_set_index(self) -> int:
        """Initial texture set index."""
        return self._data.texture_set_index

    @property
    def debug_texture(self) -> bool:
        """Enable texture debug output."""
        return self._data.debug_texture

    # ==========================================================================
    # Lighting settings
    # ==========================================================================
    @property
    def lighting_brightness(self) -> float:
        """Default brightness level."""
        return self._data.lighting_brightness

    @property
    def lighting_background(self) -> float:
        """Default background gray level."""
        return self._data.lighting_background

    # ==========================================================================
    # Celebration settings
    # ==========================================================================
    @property
    def celebration_effect(self) -> str:
        """Default celebration effect name."""
        return self._data.celebration_effect

    @property
    def celebration_enabled(self) -> bool:
        """Whether celebration effects are enabled."""
        return self._data.celebration_enabled

    @property
    def celebration_duration(self) -> float:
        """Celebration effect duration in seconds."""
        return self._data.celebration_duration

    # ==========================================================================
    # Operator settings
    # ==========================================================================
    @property
    def operation_log(self) -> bool:
        """Enable operation logging."""
        return self._data.operation_log

    @property
    def operation_log_path(self) -> str:
        """Path for operation log file."""
        return self._data.operation_log_path

    @property
    def operator_show_alg_annotation(self) -> bool:
        """Show algorithm annotations."""
        return self._data.operator_show_alg_annotation

    @property
    def queue_heading_h1(self) -> bool:
        """Show h1 headings (solver phase names) in WebGL queue display."""
        return self._data.queue_heading_h1

    @queue_heading_h1.setter
    def queue_heading_h1(self, value: bool) -> None:
        """Set queue heading h1 flag."""
        self._data.set_queue_heading_h1(value)

    @property
    def queue_heading_h2(self) -> bool:
        """Show h2 headings (sub-step details) in WebGL queue display."""
        return self._data.queue_heading_h2

    @queue_heading_h2.setter
    def queue_heading_h2(self, value: bool) -> None:
        """Set queue heading h2 flag."""
        self._data.set_queue_heading_h2(value)

    @property
    def assist_enabled(self) -> bool:
        """Whether assist mode (move preview) is enabled."""
        return self._data.assist_config.enabled

    @assist_enabled.setter
    def assist_enabled(self, value: bool) -> None:
        """Set assist enabled flag."""
        self._data.assist_config.enabled = value

    # ==========================================================================
    # Testing settings
    # ==========================================================================
    @property
    def scramble_key_for_f9(self) -> int:
        """Scramble key for F9 shortcut."""
        return self._data.scramble_key_for_f9

    @property
    def test_number_of_scramble_iterations(self) -> int:
        """Number of scramble iterations for tests."""
        return self._data.test_number_of_scramble_iterations

    @property
    def last_scramble_path(self) -> str:
        """Path for last scramble file."""
        return self._data.last_scramble_path

    # ==========================================================================
    # Mouse input settings
    # ==========================================================================
    @property
    def input_mouse_debug(self) -> bool:
        """Enable mouse input debug output."""
        return self._data.input_mouse_debug

    @property
    def input_mouse_model_rotate_by_drag_right_bottom(self) -> bool:
        """Model rotation by dragging right/bottom."""
        return self._data.input_mouse_model_rotate_by_drag_right_bottom

    @property
    def input_mouse_rotate_adjusted_face(self) -> bool:
        """Rotate adjusted face on edge/corner drag."""
        return self._data.input_mouse_rotate_adjusted_face

    # ==========================================================================
    # Config change listeners
    # ==========================================================================
    def add_config_listener(self, listener: object) -> None:
        """Register a callback(field_name: str, new_value: object) for config changes."""
        self._data.add_listener(listener)

    def remove_config_listener(self, listener: object) -> None:
        """Unregister a config change listener."""
        self._data.remove_listener(listener)

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
        return self._data.ss_codes.get(code, False)
