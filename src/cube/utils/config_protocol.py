"""Configuration protocol for dependency inversion.

Domain imports these protocols from utils (foundation layer).
Application layer implements IServiceProvider.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ConfigProtocol(Protocol):
    """Configuration protocol - domain accesses config through this interface.

    All properties are read-only. Application provides the implementation
    that wraps the actual config.py values.
    """

    # Model settings
    @property
    def check_cube_sanity(self) -> bool:
        """Enable cube sanity checks."""
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

    # Solver settings
    @property
    def solver_debug(self) -> bool:
        """Enable solver debug output."""
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

    # Optimization settings
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

    # GUI settings used by domain (for sample markers)
    @property
    def gui_draw_sample_markers(self) -> bool:
        """Draw sample markers on cube faces."""
        ...

    # Debug settings
    @property
    def debug_texture(self) -> bool:
        """Enable texture debug output."""
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
