"""Configuration protocol for dependency inversion.

Domain imports these protocols from utils (foundation layer).
Application layer implements IServiceProvider.

IMPORTANT: Only config_impl.py should import _config directly.
All other code must access config through this protocol via context.
"""

from typing import TYPE_CHECKING, Protocol, Tuple, runtime_checkable

if TYPE_CHECKING:
    from cube.domain.model.Color import Color
    from cube.utils.SSCode import SSCode
    from cube.application.markers.IMarkerFactory import IMarkerFactory
    from cube.application.markers.IMarkerManager import IMarkerManager
    from cube.utils.markers_config import MarkersConfig


@runtime_checkable
class ArrowConfigProtocol(Protocol):
    """Protocol for 3D arrow configuration.

    Defines the interface for arrow settings. The actual ArrowConfig
    dataclass in _config.py implements this protocol.
    """

    @property
    def enabled(self) -> bool:
        """Master switch to enable/disable 3D arrows."""
        ...

    @property
    def style(self) -> str:
        """Arrow style: 'simple', 'curved', 'compound'."""
        ...

    @property
    def animation(self) -> str:
        """Arrow animation: 'grow', 'fade', 'none'."""
        ...

    @property
    def head_style(self) -> str:
        """Arrow head style: 'cone', 'pyramid', 'flat'."""
        ...

    @property
    def color(self) -> Tuple[float, float, float]:
        """Arrow color (RGB 0.0-1.0)."""
        ...

    @property
    def shaft_radius(self) -> float:
        """Radius of arrow shaft cylinder."""
        ...

    @property
    def head_radius(self) -> float:
        """Radius of cone base."""
        ...

    @property
    def head_length(self) -> float:
        """Length of cone/head."""
        ...

    @property
    def height_offset(self) -> float:
        """Height above cube surface."""
        ...

    @property
    def animation_duration(self) -> float:
        """Seconds for grow animation."""
        ...

    @property
    def segments(self) -> int:
        """Smoothness of cylinders."""
        ...


# Type alias for marker definition: (color, outer_radius, thick, height)
MarkerDef = Tuple[Tuple[int, int, int], float, float, float]
# Type alias for animation text property: (x, y, size, color, bold)
AnimationTextDef = Tuple[int, int, int, Tuple[int, int, int, int], bool]


@runtime_checkable
class ConfigProtocol(Protocol):
    """Configuration protocol - all code accesses config through this interface.

    Application provides the implementation that wraps the actual _config.py values.
    Access via app.config or vs.config depending on context.
    """

    # ==========================================================================
    # Model settings
    # ==========================================================================
    @property
    def check_cube_sanity(self) -> bool:
        """Enable cube sanity checks."""
        ...

    @check_cube_sanity.setter
    def check_cube_sanity(self, value: bool) -> None:
        """Set cube sanity check flag."""
        ...

    @property
    def short_part_name(self) -> bool:
        """Use short names for parts."""
        ...

    @property
    def dont_optimized_part_id(self) -> bool:
        """Disable part ID optimization."""
        ...

    @property
    def print_cube_as_text_during_solve(self) -> bool:
        """Print cube state as text during solve."""
        ...

    @property
    def cube_size(self) -> int:
        """Default cube size."""
        ...

    @property
    def enable_cube_cache(self) -> bool:
        """Enable cube caching for performance optimization."""
        ...

    # ==========================================================================
    # Solver settings
    # ==========================================================================
    @property
    def default_solver(self) -> str:
        """Default solver name (case-insensitive, prefix matching allowed)."""
        ...

    @property
    def solver_debug(self) -> bool:
        """Enable solver debug output."""
        ...

    @solver_debug.setter
    def solver_debug(self, value: bool) -> None:
        """Set solver debug flag."""
        ...

    @property
    def solver_annotate_trackers(self) -> bool:
        """Annotate trackers during solve."""
        ...

    @property
    def solver_pll_rotate_while_search(self) -> bool:
        """Rotate during PLL search."""
        ...

    @property
    def solver_sanity_check_is_a_boy(self) -> bool:
        """Check if cube is in BOY orientation."""
        ...

    @property
    def cage_3x3_solver(self) -> str:
        """3x3 solver used by cage method for corner solving (Phase 1b).

        Options: "beginner", "cfop", "kociemba"
        Default: "beginner"
        """
        ...

    @property
    def first_face_color(self) -> "Color":
        """First face color for Layer 1 in beginner and LBL solvers.

        This determines which face is treated as Layer 1 (bottom layer).
        The solver finds the face with this color and starts solving from there.
        Default: WHITE
        """
        ...

    # ==========================================================================
    # Optimization settings
    # ==========================================================================
    @property
    def optimize_odd_cube_centers_switch_centers(self) -> bool:
        """Optimize odd cube center switching."""
        ...

    @property
    def optimize_big_cube_centers_search_complete_slices(self) -> bool:
        """Search for complete slices in big cube centers."""
        ...

    @property
    def optimize_big_cube_centers_search_complete_slices_only_target_zero(self) -> bool:
        """Only search complete slices for target zero."""
        ...

    @property
    def optimize_big_cube_centers_search_blocks(self) -> bool:
        """Search for blocks in big cube centers."""
        ...

    # ==========================================================================
    # Viewer settings
    # ==========================================================================
    @property
    def cell_size(self) -> int:
        """Size of each cell in the viewer."""
        ...

    @property
    def corner_size(self) -> float:
        """Relative corner size (to cell size)."""
        ...

    @property
    def axis_enabled(self) -> bool:
        """Master switch for axis drawing - when False, no axis code runs."""
        ...

    @property
    def axis_length(self) -> float:
        """Length of axis display."""
        ...

    @property
    def max_marker_radius(self) -> float:
        """Maximum radius for markers."""
        ...

    @property
    def viewer_max_size_for_texture(self) -> int:
        """Maximum cube size for texture rendering."""
        ...

    @property
    def viewer_draw_shadows(self) -> str:
        """Faces to draw shadows for (e.g., 'LDB')."""
        ...

    @property
    def viewer_trace_draw_update(self) -> bool:
        """Trace draw/update calls."""
        ...

    @property
    def prof_viewer_search_facet(self) -> bool:
        """Profile facet search."""
        ...

    @property
    def markers(self) -> dict[str, MarkerDef]:
        """Marker definitions by name."""
        ...

    @property
    def arrow_config(self) -> ArrowConfigProtocol:
        """Get 3D arrow configuration for solver annotations.

        Returns an ArrowConfigProtocol with all arrow settings.
        Access via app.config.arrow_config or vs.config.arrow_config.
        """
        ...

    # ==========================================================================
    # GUI settings
    # ==========================================================================
    @property
    def markers_config(self) -> "MarkersConfig":
        """Get markers configuration (draw flags for various marker types)."""
        ...

    @property
    def gui_test_mode(self) -> bool:
        """GUI testing mode - exceptions propagate."""
        ...

    @property
    def quit_on_error_in_test_mode(self) -> bool:
        """Quit application on error in test mode."""
        ...

    @property
    def animation_text(self) -> list[AnimationTextDef]:
        """Animation text display properties."""
        ...

    @property
    def animation_enabled(self) -> bool:
        """Whether animation is enabled by default."""
        ...

    @property
    def animation_speed(self) -> int:
        """Default animation speed index (0-7, higher is faster).

        Speed presets:
        0: 45 deg/s (slowest)
        1: 90 deg/s
        2: 180 deg/s
        3: 360 deg/s (default)
        4: 540 deg/s
        5: 900 deg/s
        6: 1800 deg/s
        7: 3000 deg/s (fastest)
        """
        ...

    # ==========================================================================
    # Texture settings
    # ==========================================================================
    @property
    def texture_sets(self) -> list[str | None] | None:
        """List of texture set names to cycle through."""
        ...

    @property
    def texture_set_index(self) -> int:
        """Initial texture set index."""
        ...

    @property
    def debug_texture(self) -> bool:
        """Enable texture debug output."""
        ...

    # ==========================================================================
    # Lighting settings
    # ==========================================================================
    @property
    def lighting_brightness(self) -> float:
        """Default brightness level."""
        ...

    @property
    def lighting_background(self) -> float:
        """Default background gray level."""
        ...

    # ==========================================================================
    # Celebration settings
    # ==========================================================================
    @property
    def celebration_effect(self) -> str:
        """Default celebration effect name."""
        ...

    @property
    def celebration_enabled(self) -> bool:
        """Whether celebration effects are enabled."""
        ...

    @property
    def celebration_duration(self) -> float:
        """Celebration effect duration in seconds."""
        ...

    # ==========================================================================
    # Operator settings
    # ==========================================================================
    @property
    def operation_log(self) -> bool:
        """Enable operation logging."""
        ...

    @property
    def operation_log_path(self) -> str:
        """Path for operation log file."""
        ...

    @property
    def operator_show_alg_annotation(self) -> bool:
        """Show algorithm annotations."""
        ...

    # ==========================================================================
    # Testing settings
    # ==========================================================================
    @property
    def scramble_key_for_f9(self) -> int:
        """Scramble key for F9 shortcut."""
        ...

    @property
    def test_number_of_scramble_iterations(self) -> int:
        """Number of scramble iterations for tests."""
        ...

    @property
    def last_scramble_path(self) -> str:
        """Path for last scramble file."""
        ...

    # ==========================================================================
    # Mouse input settings
    # ==========================================================================
    @property
    def input_mouse_debug(self) -> bool:
        """Enable mouse input debug output."""
        ...

    @property
    def input_mouse_model_rotate_by_drag_right_bottom(self) -> bool:
        """Model rotation by dragging right/bottom."""
        ...

    @property
    def input_mouse_rotate_adjusted_face(self) -> bool:
        """Rotate adjusted face on edge/corner drag."""
        ...

    # ==========================================================================
    # Single-step mode settings
    # ==========================================================================
    def is_ss_code_enabled(self, code: "SSCode") -> bool:
        """Check if a single-step mode code is enabled.

        Args:
            code: The SSCode to check

        Returns:
            True if the code is enabled in SS_CODES config, False otherwise
        """
        ...


@runtime_checkable
class IServiceProvider(Protocol):
    """Service provider protocol - provides access to application services.

    Domain classes receive this via dependency injection.
    Application (_App) implements this protocol.
    Tests use a lightweight TestServiceProvider.

    Extensible: future services (debug, logging) can be added here.
    """

    @property
    def config(self) -> ConfigProtocol:
        """Get the application configuration."""
        ...

    @property
    def marker_factory(self) -> "IMarkerFactory":
        """Get the marker factory for creating marker configurations."""
        ...

    @property
    def marker_manager(self) -> "IMarkerManager":
        """Get the marker manager for adding/retrieving markers on cube stickers."""
        ...
