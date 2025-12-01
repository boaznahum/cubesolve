"""
Key bindings - the single source of truth for key-to-command mapping.

This module defines ALL keyboard shortcuts in declarative tables:
- KEY_BINDINGS_NORMAL: Commands available when NOT animating
- KEY_BINDINGS_ANIMATION: Commands available DURING animation

Design:
- Two separate tables for context-dependent behavior
- lookup_command() picks the right table based on animation_running
- O(1) lookup via pre-built dictionaries

Usage:
    from cube.gui.key_bindings import lookup_command
    from cube.gui.Command import Command

    cmd = lookup_command(Keys.R, Modifiers.SHIFT, animation_running=False)
    # Returns Command.ROTATE_R_PRIME
"""
from cube.gui.types import Keys, Modifiers
from cube.gui.Command import Command

# Type alias for binding tuple: (key, modifiers, command)
KeyBinding = tuple[int, int, Command]

# =============================================================================
# NORMAL MODE BINDINGS
# =============================================================================
# These bindings are active when NO animation is running.

KEY_BINDINGS_NORMAL: list[KeyBinding] = [
    # -------------------------------------------------------------------------
    # Face Rotations
    # -------------------------------------------------------------------------
    (Keys.R, 0, Command.ROTATE_R),
    (Keys.R, Modifiers.SHIFT, Command.ROTATE_R_PRIME),
    (Keys.R, Modifiers.CTRL, Command.ROTATE_RW),
    (Keys.R, Modifiers.CTRL | Modifiers.SHIFT, Command.ROTATE_RW_PRIME),

    (Keys.L, 0, Command.ROTATE_L),
    (Keys.L, Modifiers.SHIFT, Command.ROTATE_L_PRIME),
    (Keys.L, Modifiers.CTRL, Command.ROTATE_LW),
    (Keys.L, Modifiers.CTRL | Modifiers.SHIFT, Command.ROTATE_LW_PRIME),

    (Keys.U, 0, Command.ROTATE_U),
    (Keys.U, Modifiers.SHIFT, Command.ROTATE_U_PRIME),
    (Keys.U, Modifiers.CTRL, Command.ROTATE_UW),
    (Keys.U, Modifiers.CTRL | Modifiers.SHIFT, Command.ROTATE_UW_PRIME),

    (Keys.D, 0, Command.ROTATE_D),
    (Keys.D, Modifiers.SHIFT, Command.ROTATE_D_PRIME),
    (Keys.D, Modifiers.CTRL, Command.ROTATE_DW),
    (Keys.D, Modifiers.CTRL | Modifiers.SHIFT, Command.ROTATE_DW_PRIME),

    (Keys.F, 0, Command.ROTATE_F),
    (Keys.F, Modifiers.SHIFT, Command.ROTATE_F_PRIME),
    (Keys.F, Modifiers.CTRL, Command.ROTATE_FW),
    (Keys.F, Modifiers.CTRL | Modifiers.SHIFT, Command.ROTATE_FW_PRIME),

    (Keys.B, 0, Command.ROTATE_B),
    (Keys.B, Modifiers.SHIFT, Command.ROTATE_B_PRIME),
    (Keys.B, Modifiers.CTRL, Command.ROTATE_BW),
    (Keys.B, Modifiers.CTRL | Modifiers.SHIFT, Command.ROTATE_BW_PRIME),

    # -------------------------------------------------------------------------
    # Slice Moves
    # -------------------------------------------------------------------------
    (Keys.M, 0, Command.SLICE_M),
    (Keys.M, Modifiers.SHIFT, Command.SLICE_M_PRIME),
    (Keys.E, 0, Command.SLICE_E),
    (Keys.E, Modifiers.SHIFT, Command.SLICE_E_PRIME),
    (Keys.S, 0, Command.SLICE_S),
    (Keys.S, Modifiers.SHIFT, Command.SLICE_S_PRIME),

    # -------------------------------------------------------------------------
    # Cube Rotations (X/Y/Z without Ctrl/Alt)
    # -------------------------------------------------------------------------
    (Keys.X, 0, Command.CUBE_X),
    (Keys.X, Modifiers.SHIFT, Command.CUBE_X_PRIME),
    (Keys.Y, 0, Command.CUBE_Y),
    (Keys.Y, Modifiers.SHIFT, Command.CUBE_Y_PRIME),
    (Keys.Z, 0, Command.CUBE_Z),
    (Keys.Z, Modifiers.SHIFT, Command.CUBE_Z_PRIME),

    # -------------------------------------------------------------------------
    # Scrambles
    # -------------------------------------------------------------------------
    (Keys._0, 0, Command.SCRAMBLE_0),
    (Keys._1, 0, Command.SCRAMBLE_1),
    (Keys._2, 0, Command.SCRAMBLE_2),
    (Keys._3, 0, Command.SCRAMBLE_3),
    (Keys._4, 0, Command.SCRAMBLE_4),
    (Keys._5, 0, Command.SCRAMBLE_5),
    (Keys._6, 0, Command.SCRAMBLE_6),
    (Keys._7, 0, Command.SCRAMBLE_7),
    (Keys._8, 0, Command.SCRAMBLE_8),
    (Keys._9, 0, Command.SCRAMBLE_9),
    (Keys.F9, 0, Command.SCRAMBLE_F9),

    # -------------------------------------------------------------------------
    # Solve Commands
    # -------------------------------------------------------------------------
    (Keys.SLASH, 0, Command.SOLVE_ALL),
    (Keys.SLASH, Modifiers.SHIFT, Command.SOLVE_ALL_NO_ANIMATION),  # Instant solve
    (Keys.F1, 0, Command.SOLVE_L1),
    (Keys.F1, Modifiers.CTRL, Command.SOLVE_L1X),
    (Keys.F2, 0, Command.SOLVE_L2),
    (Keys.F3, 0, Command.SOLVE_L3),
    (Keys.F3, Modifiers.CTRL, Command.SOLVE_L3X),
    (Keys.F4, 0, Command.SOLVE_CENTERS),
    (Keys.F5, 0, Command.SOLVE_EDGES),

    # -------------------------------------------------------------------------
    # View Control (Ctrl/Alt + X/Y/Z)
    # -------------------------------------------------------------------------
    (Keys.X, Modifiers.CTRL, Command.VIEW_ALPHA_X_DEC),
    (Keys.X, Modifiers.ALT, Command.VIEW_ALPHA_X_INC),
    (Keys.Y, Modifiers.CTRL, Command.VIEW_ALPHA_Y_DEC),
    (Keys.Y, Modifiers.ALT, Command.VIEW_ALPHA_Y_INC),
    (Keys.Z, Modifiers.CTRL, Command.VIEW_ALPHA_Z_DEC),
    (Keys.Z, Modifiers.ALT, Command.VIEW_ALPHA_Z_INC),

    # Arrow keys for pan
    (Keys.UP, 0, Command.PAN_UP),
    (Keys.DOWN, 0, Command.PAN_DOWN),
    (Keys.LEFT, 0, Command.PAN_LEFT),
    (Keys.RIGHT, 0, Command.PAN_RIGHT),

    # Ctrl+Arrow for zoom
    (Keys.UP, Modifiers.CTRL, Command.ZOOM_IN),
    (Keys.DOWN, Modifiers.CTRL, Command.ZOOM_OUT),

    # Alt+C for view reset
    (Keys.C, Modifiers.ALT, Command.VIEW_RESET),

    # -------------------------------------------------------------------------
    # Animation Control
    # -------------------------------------------------------------------------
    (Keys.NUM_ADD, 0, Command.SPEED_UP),
    (Keys.NUM_SUBTRACT, 0, Command.SPEED_DOWN),
    (Keys.SPACE, 0, Command.PAUSE_TOGGLE),
    (Keys.SPACE, Modifiers.CTRL, Command.SINGLE_STEP_TOGGLE),

    # -------------------------------------------------------------------------
    # Shadow Toggles
    # -------------------------------------------------------------------------
    (Keys.F10, 0, Command.SHADOW_TOGGLE_L),
    (Keys.F11, 0, Command.SHADOW_TOGGLE_D),
    (Keys.F12, 0, Command.SHADOW_TOGGLE_B),

    # -------------------------------------------------------------------------
    # Cube Size
    # -------------------------------------------------------------------------
    (Keys.EQUAL, 0, Command.SIZE_INC),
    (Keys.MINUS, 0, Command.SIZE_DEC),

    # -------------------------------------------------------------------------
    # Slice Selection
    # -------------------------------------------------------------------------
    (Keys.BRACKETLEFT, 0, Command.SLICE_START_INC),
    (Keys.BRACKETLEFT, Modifiers.SHIFT, Command.SLICE_START_DEC),
    (Keys.BRACKETLEFT, Modifiers.ALT, Command.SLICE_RESET),
    (Keys.BRACKETRIGHT, 0, Command.SLICE_STOP_INC),
    (Keys.BRACKETRIGHT, Modifiers.SHIFT, Command.SLICE_STOP_DEC),

    # -------------------------------------------------------------------------
    # Recording
    # -------------------------------------------------------------------------
    (Keys.P, 0, Command.RECORDING_PLAY),
    (Keys.P, Modifiers.SHIFT, Command.RECORDING_PLAY_PRIME),
    (Keys.P, Modifiers.CTRL, Command.RECORDING_TOGGLE),
    (Keys.P, Modifiers.ALT, Command.RECORDING_CLEAR),

    # -------------------------------------------------------------------------
    # Debug/Config
    # -------------------------------------------------------------------------
    (Keys.O, 0, Command.TOGGLE_ANIMATION),
    (Keys.O, Modifiers.CTRL, Command.TOGGLE_DEBUG),
    (Keys.O, Modifiers.ALT, Command.TOGGLE_SANITY_CHECK),
    (Keys.I, 0, Command.DEBUG_INFO),

    # -------------------------------------------------------------------------
    # Testing
    # -------------------------------------------------------------------------
    (Keys.T, 0, Command.TEST_RUN),
    (Keys.T, Modifiers.ALT, Command.TEST_RUN_LAST),
    (Keys.T, Modifiers.CTRL, Command.TEST_SCRAMBLE_LAST),

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    (Keys.Q, 0, Command.QUIT),
    (Keys.C, 0, Command.RESET_CUBE),
    (Keys.C, Modifiers.CTRL, Command.RESET_CUBE_AND_VIEW),
    (Keys.COMMA, 0, Command.UNDO),
    (Keys.BACKSLASH, 0, Command.SWITCH_SOLVER),

    # -------------------------------------------------------------------------
    # Special
    # -------------------------------------------------------------------------
    (Keys.W, 0, Command.ANNOTATE),
    (Keys.A, 0, Command.SPECIAL_ALG),
]


# =============================================================================
# ANIMATION MODE BINDINGS
# =============================================================================
# These bindings are active DURING animation.
# Limited set - only commands that make sense during animation.

KEY_BINDINGS_ANIMATION: list[KeyBinding] = [
    # -------------------------------------------------------------------------
    # Animation Control
    # -------------------------------------------------------------------------
    (Keys.NUM_ADD, 0, Command.SPEED_UP),
    (Keys.NUM_SUBTRACT, 0, Command.SPEED_DOWN),
    (Keys.SPACE, 0, Command.PAUSE_TOGGLE),
    (Keys.SPACE, Modifiers.CTRL, Command.SINGLE_STEP_TOGGLE),

    # S means STOP during animation (not slice rotation)
    (Keys.S, 0, Command.STOP_ANIMATION),

    # -------------------------------------------------------------------------
    # View Control (still works during animation)
    # -------------------------------------------------------------------------
    (Keys.X, Modifiers.CTRL, Command.VIEW_ALPHA_X_DEC),
    (Keys.X, Modifiers.ALT, Command.VIEW_ALPHA_X_INC),
    (Keys.Y, Modifiers.CTRL, Command.VIEW_ALPHA_Y_DEC),
    (Keys.Y, Modifiers.ALT, Command.VIEW_ALPHA_Y_INC),
    (Keys.Z, Modifiers.CTRL, Command.VIEW_ALPHA_Z_DEC),
    (Keys.Z, Modifiers.ALT, Command.VIEW_ALPHA_Z_INC),

    (Keys.UP, 0, Command.PAN_UP),
    (Keys.DOWN, 0, Command.PAN_DOWN),
    (Keys.LEFT, 0, Command.PAN_LEFT),
    (Keys.RIGHT, 0, Command.PAN_RIGHT),
    (Keys.UP, Modifiers.CTRL, Command.ZOOM_IN),
    (Keys.DOWN, Modifiers.CTRL, Command.ZOOM_OUT),
    (Keys.C, Modifiers.ALT, Command.VIEW_RESET),

    # -------------------------------------------------------------------------
    # Shadow Toggles (still work during animation)
    # -------------------------------------------------------------------------
    (Keys.F10, 0, Command.SHADOW_TOGGLE_L),
    (Keys.F11, 0, Command.SHADOW_TOGGLE_D),
    (Keys.F12, 0, Command.SHADOW_TOGGLE_B),

    # -------------------------------------------------------------------------
    # Solver Switch (works during animation)
    # -------------------------------------------------------------------------
    (Keys.BACKSLASH, 0, Command.SWITCH_SOLVER),

    # -------------------------------------------------------------------------
    # Application (Q quits even during animation)
    # -------------------------------------------------------------------------
    (Keys.Q, 0, Command.QUIT),
]


# =============================================================================
# LOOKUP TABLES (O(1) access)
# =============================================================================

_NORMAL_MAP: dict[tuple[int, int], Command] = {
    (key, mods): cmd for key, mods, cmd in KEY_BINDINGS_NORMAL
}

_ANIMATION_MAP: dict[tuple[int, int], Command] = {
    (key, mods): cmd for key, mods, cmd in KEY_BINDINGS_ANIMATION
}


def lookup_command(key: int, modifiers: int, animation_running: bool) -> Command | None:
    """Look up the command for a key+modifier combination.

    Args:
        key: Key code from Keys class
        modifiers: Modifier flags from Modifiers class
        animation_running: Whether animation is currently running

    Returns:
        Command enum value, or None if no binding exists
    """
    table = _ANIMATION_MAP if animation_running else _NORMAL_MAP
    return table.get((key, modifiers))


def get_all_bindings(animation_running: bool = False) -> list[KeyBinding]:
    """Get all key bindings for the given mode.

    Useful for generating documentation or help screens.
    """
    return KEY_BINDINGS_ANIMATION if animation_running else KEY_BINDINGS_NORMAL
