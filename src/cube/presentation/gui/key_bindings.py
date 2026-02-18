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
    from cube.presentation.gui.key_bindings import lookup_command
    from cube.presentation.gui.commands import Command, Commands

    cmd = lookup_command(Keys.R, Modifiers.SHIFT, animation_running=False)
    # Returns Commands.ROTATE_R_PRIME
"""
from cube.presentation.gui.commands import Command, Commands
from cube.presentation.gui.types import Keys, Modifiers

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
    (Keys.R, 0, Commands.ROTATE_R),
    (Keys.R, Modifiers.SHIFT, Commands.ROTATE_R_PRIME),
    (Keys.R, Modifiers.CTRL, Commands.ROTATE_RW),
    (Keys.R, Modifiers.CTRL | Modifiers.SHIFT, Commands.ROTATE_RW_PRIME),

    (Keys.L, 0, Commands.ROTATE_L),
    (Keys.L, Modifiers.SHIFT, Commands.ROTATE_L_PRIME),
    (Keys.L, Modifiers.CTRL, Commands.ROTATE_LW),
    (Keys.L, Modifiers.CTRL | Modifiers.SHIFT, Commands.ROTATE_LW_PRIME),

    (Keys.U, 0, Commands.ROTATE_U),
    (Keys.U, Modifiers.SHIFT, Commands.ROTATE_U_PRIME),
    (Keys.U, Modifiers.CTRL, Commands.ROTATE_UW),
    (Keys.U, Modifiers.CTRL | Modifiers.SHIFT, Commands.ROTATE_UW_PRIME),

    (Keys.D, 0, Commands.ROTATE_D),
    (Keys.D, Modifiers.SHIFT, Commands.ROTATE_D_PRIME),
    (Keys.D, Modifiers.CTRL, Commands.ROTATE_DW),
    (Keys.D, Modifiers.CTRL | Modifiers.SHIFT, Commands.ROTATE_DW_PRIME),

    (Keys.F, 0, Commands.ROTATE_F),
    (Keys.F, Modifiers.SHIFT, Commands.ROTATE_F_PRIME),
    (Keys.F, Modifiers.CTRL, Commands.ROTATE_FW),
    (Keys.F, Modifiers.CTRL | Modifiers.SHIFT, Commands.ROTATE_FW_PRIME),

    (Keys.B, 0, Commands.ROTATE_B),
    (Keys.B, Modifiers.SHIFT, Commands.ROTATE_B_PRIME),
    (Keys.B, Modifiers.CTRL, Commands.ROTATE_BW),
    (Keys.B, Modifiers.CTRL | Modifiers.SHIFT, Commands.ROTATE_BW_PRIME),

    # -------------------------------------------------------------------------
    # Slice Moves
    # -------------------------------------------------------------------------
    (Keys.M, 0, Commands.SLICE_M),
    (Keys.M, Modifiers.SHIFT, Commands.SLICE_M_PRIME),
    (Keys.E, 0, Commands.SLICE_E),
    (Keys.E, Modifiers.SHIFT, Commands.SLICE_E_PRIME),
    (Keys.S, 0, Commands.SLICE_S),
    (Keys.S, Modifiers.SHIFT, Commands.SLICE_S_PRIME),

    # -------------------------------------------------------------------------
    # Cube Rotations (X/Y/Z without Ctrl/Alt)
    # -------------------------------------------------------------------------
    (Keys.X, 0, Commands.CUBE_X),
    (Keys.X, Modifiers.SHIFT, Commands.CUBE_X_PRIME),
    (Keys.Y, 0, Commands.CUBE_Y),
    (Keys.Y, Modifiers.SHIFT, Commands.CUBE_Y_PRIME),
    (Keys.Z, 0, Commands.CUBE_Z),
    (Keys.Z, Modifiers.SHIFT, Commands.CUBE_Z_PRIME),

    # -------------------------------------------------------------------------
    # Scrambles
    # -------------------------------------------------------------------------
    (Keys.GRAVE, 0, Commands.SCRAMBLE_F),  # Backtick (`) - scramble from F.txt
    (Keys._0, 0, Commands.SCRAMBLE_0),
    (Keys._1, 0, Commands.SCRAMBLE_1),
    (Keys._2, 0, Commands.SCRAMBLE_2),
    (Keys._3, 0, Commands.SCRAMBLE_3),
    (Keys._4, 0, Commands.SCRAMBLE_4),
    (Keys._5, 0, Commands.SCRAMBLE_5),
    (Keys._6, 0, Commands.SCRAMBLE_6),
    (Keys._7, 0, Commands.SCRAMBLE_7),
    (Keys._8, 0, Commands.SCRAMBLE_8),
    (Keys._9, 0, Commands.SCRAMBLE_9),
    (Keys.F9, 0, Commands.SCRAMBLE_F9),

    # -------------------------------------------------------------------------
    # Solve Commands
    # -------------------------------------------------------------------------
    (Keys.SLASH, 0, Commands.SOLVE_ALL),
    (Keys.SLASH, Modifiers.SHIFT, Commands.SOLVE_ALL_NO_ANIMATION),  # Instant solve
    (Keys.F1, 0, Commands.SOLVE_L1),
    (Keys.F1, Modifiers.CTRL, Commands.SOLVE_L1X),
    (Keys.F2, 0, Commands.SOLVE_L2),
    (Keys.F3, 0, Commands.SOLVE_L3),
    (Keys.F3, Modifiers.CTRL, Commands.SOLVE_L3X),
    (Keys.F4, 0, Commands.SOLVE_CENTERS),
    (Keys.F5, 0, Commands.SOLVE_EDGES),

    # -------------------------------------------------------------------------
    # View Control (Ctrl/Alt + X/Y/Z)
    # -------------------------------------------------------------------------
    (Keys.X, Modifiers.CTRL, Commands.VIEW_ALPHA_X_DEC),
    (Keys.X, Modifiers.ALT, Commands.VIEW_ALPHA_X_INC),
    (Keys.Y, Modifiers.CTRL, Commands.VIEW_ALPHA_Y_DEC),
    (Keys.Y, Modifiers.ALT, Commands.VIEW_ALPHA_Y_INC),
    (Keys.Z, Modifiers.CTRL, Commands.VIEW_ALPHA_Z_DEC),
    (Keys.Z, Modifiers.ALT, Commands.VIEW_ALPHA_Z_INC),

    # Arrow keys for pan
    (Keys.UP, 0, Commands.PAN_UP),
    (Keys.DOWN, 0, Commands.PAN_DOWN),
    (Keys.LEFT, 0, Commands.PAN_LEFT),
    (Keys.RIGHT, 0, Commands.PAN_RIGHT),

    # Ctrl+Arrow for zoom
    (Keys.UP, Modifiers.CTRL, Commands.ZOOM_IN),
    (Keys.DOWN, Modifiers.CTRL, Commands.ZOOM_OUT),

    # Alt+C for view reset
    (Keys.C, Modifiers.ALT, Commands.VIEW_RESET),

    # -------------------------------------------------------------------------
    # Animation Control
    # -------------------------------------------------------------------------
    (Keys.NUM_ADD, 0, Commands.SPEED_UP),
    (Keys.NUM_SUBTRACT, 0, Commands.SPEED_DOWN),
    (Keys.UP, Modifiers.SHIFT, Commands.SPEED_UP),      # Alternative for keyboards without numpad
    (Keys.DOWN, Modifiers.SHIFT, Commands.SPEED_DOWN),  # Alternative for keyboards without numpad
    (Keys.SPACE, 0, Commands.PAUSE_TOGGLE),
    (Keys.SPACE, Modifiers.CTRL, Commands.SINGLE_STEP_TOGGLE),

    # -------------------------------------------------------------------------
    # Shadow Toggles
    # -------------------------------------------------------------------------
    (Keys.F10, 0, Commands.SHADOW_TOGGLE_L),
    (Keys.F11, 0, Commands.SHADOW_TOGGLE_D),
    (Keys.F12, 0, Commands.SHADOW_TOGGLE_B),

    # -------------------------------------------------------------------------
    # Cube Size
    # -------------------------------------------------------------------------
    (Keys.EQUAL, 0, Commands.SIZE_INC),
    (Keys.MINUS, 0, Commands.SIZE_DEC),

    # -------------------------------------------------------------------------
    # Slice Selection
    # -------------------------------------------------------------------------
    (Keys.BRACKETLEFT, 0, Commands.SLICE_START_INC),
    (Keys.BRACKETLEFT, Modifiers.SHIFT, Commands.SLICE_START_DEC),
    (Keys.BRACKETLEFT, Modifiers.ALT, Commands.SLICE_RESET),
    (Keys.BRACKETRIGHT, 0, Commands.SLICE_STOP_INC),
    (Keys.BRACKETRIGHT, Modifiers.SHIFT, Commands.SLICE_STOP_DEC),

    # -------------------------------------------------------------------------
    # Lighting (pyglet2 backend only)
    # -------------------------------------------------------------------------
    (Keys.BRACKETLEFT, Modifiers.CTRL, Commands.BRIGHTNESS_DOWN),
    (Keys.BRACKETRIGHT, Modifiers.CTRL, Commands.BRIGHTNESS_UP),
    (Keys.BRACKETLEFT, Modifiers.CTRL | Modifiers.SHIFT, Commands.BACKGROUND_DOWN),
    (Keys.BRACKETRIGHT, Modifiers.CTRL | Modifiers.SHIFT, Commands.BACKGROUND_UP),
    (Keys.T, Modifiers.CTRL | Modifiers.SHIFT, Commands.TEXTURE_SET_NEXT),

    # -------------------------------------------------------------------------
    # Recording
    # -------------------------------------------------------------------------
    (Keys.P, 0, Commands.RECORDING_PLAY),
    (Keys.P, Modifiers.SHIFT, Commands.RECORDING_PLAY_PRIME),
    (Keys.P, Modifiers.CTRL, Commands.RECORDING_TOGGLE),
    (Keys.P, Modifiers.ALT, Commands.RECORDING_CLEAR),

    # -------------------------------------------------------------------------
    # Debug/Config
    # -------------------------------------------------------------------------
    (Keys.O, 0, Commands.TOGGLE_ANIMATION),
    (Keys.O, Modifiers.CTRL, Commands.TOGGLE_DEBUG),
    (Keys.O, Modifiers.ALT, Commands.TOGGLE_SANITY_CHECK),
    (Keys.I, 0, Commands.DEBUG_INFO),

    # -------------------------------------------------------------------------
    # Testing
    # -------------------------------------------------------------------------
    (Keys.T, 0, Commands.TEST_RUN),
    (Keys.T, Modifiers.ALT, Commands.TEST_RUN_LAST),
    (Keys.T, Modifiers.CTRL, Commands.TEST_SCRAMBLE_LAST),

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    (Keys.Q, 0, Commands.QUIT),
    (Keys.C, 0, Commands.RESET_CUBE),
    (Keys.C, Modifiers.CTRL, Commands.RESET_CUBE_AND_VIEW),
    (Keys.COMMA, 0, Commands.UNDO),
    (Keys.BACKSLASH, 0, Commands.SWITCH_SOLVER),

    # -------------------------------------------------------------------------
    # Full Mode
    # -------------------------------------------------------------------------
    (Keys.F8, 0, Commands.FULL_MODE_TOGGLE),
    (Keys.ESCAPE, 0, Commands.FULL_MODE_EXIT),

    # -------------------------------------------------------------------------
    # Special
    # -------------------------------------------------------------------------
    (Keys.W, 0, Commands.ANNOTATE),
    (Keys.A, 0, Commands.SPECIAL_ALG),
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
    (Keys.NUM_ADD, 0, Commands.SPEED_UP),
    (Keys.NUM_SUBTRACT, 0, Commands.SPEED_DOWN),
    (Keys.UP, Modifiers.SHIFT, Commands.SPEED_UP),      # Alternative for keyboards without numpad
    (Keys.DOWN, Modifiers.SHIFT, Commands.SPEED_DOWN),  # Alternative for keyboards without numpad
    (Keys.SPACE, 0, Commands.PAUSE_TOGGLE),
    (Keys.SPACE, Modifiers.CTRL, Commands.SINGLE_STEP_TOGGLE),

    # S means STOP during animation (not slice rotation)
    (Keys.S, 0, Commands.STOP_ANIMATION),

    # -------------------------------------------------------------------------
    # View Control (still works during animation)
    # -------------------------------------------------------------------------
    (Keys.X, Modifiers.CTRL, Commands.VIEW_ALPHA_X_DEC),
    (Keys.X, Modifiers.ALT, Commands.VIEW_ALPHA_X_INC),
    (Keys.Y, Modifiers.CTRL, Commands.VIEW_ALPHA_Y_DEC),
    (Keys.Y, Modifiers.ALT, Commands.VIEW_ALPHA_Y_INC),
    (Keys.Z, Modifiers.CTRL, Commands.VIEW_ALPHA_Z_DEC),
    (Keys.Z, Modifiers.ALT, Commands.VIEW_ALPHA_Z_INC),

    (Keys.UP, 0, Commands.PAN_UP),
    (Keys.DOWN, 0, Commands.PAN_DOWN),
    (Keys.LEFT, 0, Commands.PAN_LEFT),
    (Keys.RIGHT, 0, Commands.PAN_RIGHT),
    (Keys.UP, Modifiers.CTRL, Commands.ZOOM_IN),
    (Keys.DOWN, Modifiers.CTRL, Commands.ZOOM_OUT),
    (Keys.C, Modifiers.ALT, Commands.VIEW_RESET),

    # -------------------------------------------------------------------------
    # Shadow Toggles (still work during animation)
    # -------------------------------------------------------------------------
    (Keys.F10, 0, Commands.SHADOW_TOGGLE_L),
    (Keys.F11, 0, Commands.SHADOW_TOGGLE_D),
    (Keys.F12, 0, Commands.SHADOW_TOGGLE_B),

    # -------------------------------------------------------------------------
    # Lighting (pyglet2 backend only, works during animation)
    # -------------------------------------------------------------------------
    (Keys.BRACKETLEFT, Modifiers.CTRL, Commands.BRIGHTNESS_DOWN),
    (Keys.BRACKETRIGHT, Modifiers.CTRL, Commands.BRIGHTNESS_UP),
    (Keys.BRACKETLEFT, Modifiers.CTRL | Modifiers.SHIFT, Commands.BACKGROUND_DOWN),
    (Keys.BRACKETRIGHT, Modifiers.CTRL | Modifiers.SHIFT, Commands.BACKGROUND_UP),
    (Keys.T, Modifiers.CTRL | Modifiers.SHIFT, Commands.TEXTURE_SET_NEXT),

    # -------------------------------------------------------------------------
    # Solver Switch (works during animation)
    # -------------------------------------------------------------------------
    (Keys.BACKSLASH, 0, Commands.SWITCH_SOLVER),

    # -------------------------------------------------------------------------
    # Full Mode (works during animation)
    # -------------------------------------------------------------------------
    (Keys.F8, 0, Commands.FULL_MODE_TOGGLE),
    (Keys.ESCAPE, 0, Commands.FULL_MODE_EXIT),

    # -------------------------------------------------------------------------
    # Application (Q quits even during animation)
    # -------------------------------------------------------------------------
    (Keys.Q, 0, Commands.QUIT),
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


# =============================================================================
# REVERSE LOOKUP: Command → human-readable key label
# =============================================================================

# Build reverse map: key code → display name
_KEY_NAMES: dict[int, str] = {}

# Letters: attribute value → attribute name
for _attr in dir(Keys):
    if len(_attr) == 1 and _attr.isalpha():
        _KEY_NAMES[getattr(Keys, _attr)] = _attr

# Special display names
_KEY_NAMES.update({
    Keys.SPACE: "Space",
    Keys.ESCAPE: "Esc",
    Keys.RETURN: "Enter",
    Keys.TAB: "Tab",
    Keys.BACKSPACE: "Backspace",
    Keys.DELETE: "Delete",
    Keys.INSERT: "Insert",
    Keys.LEFT: "Left",
    Keys.RIGHT: "Right",
    Keys.UP: "Up",
    Keys.DOWN: "Down",
    Keys.HOME: "Home",
    Keys.END: "End",
    Keys.PAGE_UP: "PgUp",
    Keys.PAGE_DOWN: "PgDn",
    Keys.GRAVE: "`",
    Keys.SLASH: "/",
    Keys.APOSTROPHE: "'",
    Keys.MINUS: "-",
    Keys.EQUAL: "=",
    Keys.COMMA: ",",
    Keys.PERIOD: ".",
    Keys.BACKSLASH: "\\",
    Keys.BRACKETLEFT: "[",
    Keys.BRACKETRIGHT: "]",
    Keys.NUM_ADD: "Num+",
    Keys.NUM_SUBTRACT: "Num-",
})

# Numbers: _0 → "0", _1 → "1", etc.
for _i in range(10):
    _KEY_NAMES[getattr(Keys, f"_{_i}")] = str(_i)

# Function keys: F1–F12
for _i in range(1, 13):
    _KEY_NAMES[getattr(Keys, f"F{_i}")] = f"F{_i}"


def format_key(key: int, modifiers: int) -> str:
    """Format a key + modifiers into a human-readable string like 'Ctrl+Shift+F8'."""
    parts: list[str] = []
    if modifiers & Modifiers.CTRL:
        parts.append("Ctrl")
    if modifiers & Modifiers.ALT:
        parts.append("Alt")
    if modifiers & Modifiers.SHIFT:
        parts.append("Shift")
    if modifiers & Modifiers.META:
        parts.append("Meta")
    parts.append(_KEY_NAMES.get(key, f"?{key}"))
    return "+".join(parts)


class KeyBindingService:
    """Reverse lookup: Command → human-readable key binding string.

    Parameterized by binding list — each backend can provide its own.
    """

    def __init__(self, bindings: list[KeyBinding]) -> None:
        self._command_to_keys: dict[Command, list[tuple[int, int]]] = {}
        for key, mods, cmd in bindings:
            self._command_to_keys.setdefault(cmd, []).append((key, mods))

    def get_key_label(self, command: Command) -> str | None:
        """Return the primary key binding for a Command as a readable string, or None."""
        entries = self._command_to_keys.get(command)
        if not entries:
            return None
        key, mods = entries[0]
        return format_key(key, mods)

    def get_all_key_labels(self, command: Command) -> list[str]:
        """Return all key bindings for a Command as readable strings."""
        entries = self._command_to_keys.get(command)
        if not entries:
            return []
        return [format_key(key, mods) for key, mods in entries]
