"""Configuration protocol for dependency inversion.

Domain imports these protocols from utils (foundation layer).
Application layer implements IServiceProvider.

IMPORTANT: Only config_impl.py should import _config directly.
All other code must access config through this protocol via context.
"""

from typing import Protocol, runtime_checkable, Tuple


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

    # ==========================================================================
    # Solver settings
    # ==========================================================================
    @property
    def solver_debug(self) -> bool:
        """Enable solver debug output."""
        ...

    @solver_debug.setter
    def solver_debug(self, value: bool) -> None:
        """Set solver debug flag."""
        ...

    @property
    def solver_cfop(self) -> bool:
        """Use CFOP solver instead of beginner."""
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

    # ==========================================================================
    # GUI settings
    # ==========================================================================
    @property
    def gui_draw_markers(self) -> bool:
        """Draw markers on cube faces."""
        ...

    @property
    def gui_draw_sample_markers(self) -> bool:
        """Draw sample markers on cube faces."""
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
