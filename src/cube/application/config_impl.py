"""Configuration implementation - implements ConfigProtocol by wrapping config.py.

This module provides the concrete implementation of ConfigProtocol that wraps
the existing config.py values.
"""

from cube.application import _config as cfg


class AppConfig:
    """Application config implementation wrapping config.py values.

    Implements ConfigProtocol by delegating to the actual config module.
    """

    # Model settings
    @property
    def check_cube_sanity(self) -> bool:
        """Enable cube sanity checks."""
        return cfg.CHECK_CUBE_SANITY

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

    # Solver settings
    @property
    def solver_debug(self) -> bool:
        """Enable solver debug output."""
        return cfg.SOLVER_DEBUG

    @property
    def solver_cfop(self) -> bool:
        """Use CFOP solver instead of beginner."""
        return cfg.SOLVER_CFOP

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

    # Optimization settings
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

    # GUI settings used by domain (for sample markers)
    @property
    def gui_draw_sample_markers(self) -> bool:
        """Draw sample markers on cube faces."""
        return cfg.GUI_DRAW_SAMPLE_MARKERS

    # Debug settings
    @property
    def debug_texture(self) -> bool:
        """Enable texture debug output."""
        return cfg.DEBUG_TEXTURE
