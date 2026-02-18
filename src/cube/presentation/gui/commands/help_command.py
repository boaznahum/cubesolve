"""Help command - prints keyboard and mouse help to console."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from .base import Command, CommandContext, CommandResult

if TYPE_CHECKING:
    from cube.presentation.gui.key_bindings import KeyBindingService

# A help entry is one of:
#   (description, Command)          - key label auto-generated from binding
#   (description, Command, Command) - show both bindings joined with " or "
#   (description, str)              - literal key text
#   (description, None)             - info-only line, no key column
HelpEntry = Union[
    tuple[str, Command],
    tuple[str, Command, Command],
    tuple[str, str],
    tuple[str, None],
]


def _build_help_sections() -> list[tuple[str, list[HelpEntry]]]:
    """Build the help sections data structure.

    Deferred to avoid circular imports (Commands is in registry.py which imports this module).
    """
    from .registry import Commands

    return [
        ("FACE ROTATIONS", [
            ("Rotate Right face clockwise", Commands.ROTATE_R),
            ("Rotate Right face counter-clockwise", Commands.ROTATE_R_PRIME),
            ("Rotate Left face clockwise", Commands.ROTATE_L),
            ("Rotate Left face counter-clockwise", Commands.ROTATE_L_PRIME),
            ("Rotate Up face clockwise", Commands.ROTATE_U),
            ("Rotate Up face counter-clockwise", Commands.ROTATE_U_PRIME),
            ("Rotate Down face clockwise", Commands.ROTATE_D),
            ("Rotate Down face counter-clockwise", Commands.ROTATE_D_PRIME),
            ("Rotate Front face clockwise", Commands.ROTATE_F),
            ("Rotate Front face counter-clockwise", Commands.ROTATE_F_PRIME),
            ("Rotate Back face clockwise", Commands.ROTATE_B),
            ("Rotate Back face counter-clockwise", Commands.ROTATE_B_PRIME),
        ]),

        ("WIDE ROTATIONS (two outer layers)", [
            ("Right two layers clockwise (Rw)", Commands.ROTATE_RW),
            ("Right two layers counter-clockwise (Rw')", Commands.ROTATE_RW_PRIME),
            ("Left two layers clockwise (Lw)", Commands.ROTATE_LW),
            ("Left two layers counter-clockwise (Lw')", Commands.ROTATE_LW_PRIME),
            ("Up two layers clockwise (Uw)", Commands.ROTATE_UW),
            ("Up two layers counter-clockwise (Uw')", Commands.ROTATE_UW_PRIME),
            ("Down two layers clockwise (Dw)", Commands.ROTATE_DW),
            ("Down two layers counter-clockwise (Dw')", Commands.ROTATE_DW_PRIME),
            ("Front two layers clockwise (Fw)", Commands.ROTATE_FW),
            ("Front two layers counter-clockwise (Fw')", Commands.ROTATE_FW_PRIME),
            ("Back two layers clockwise (Bw)", Commands.ROTATE_BW),
            ("Back two layers counter-clockwise (Bw')", Commands.ROTATE_BW_PRIME),
        ]),

        ("SLICE MOVES (middle layers between faces)", [
            ("Middle slice parallel to L-face (like Lw without L)", Commands.SLICE_M),
            ("Middle slice counter-clockwise (M')", Commands.SLICE_M_PRIME),
            ("Equatorial slice parallel to D-face (like Dw without D)", Commands.SLICE_E),
            ("Equatorial slice counter-clockwise (E')", Commands.SLICE_E_PRIME),
            ("Standing slice parallel to F-face (like Fw without F)", Commands.SLICE_S),
            ("Standing slice counter-clockwise (S')", Commands.SLICE_S_PRIME),
        ]),

        ("CUBE ROTATIONS (entire cube, not faces)", [
            ("Rotate whole cube on R-axis (equiv to Rw for solved)", Commands.CUBE_X),
            ("Rotate whole cube on R-axis counter-clockwise (X')", Commands.CUBE_X_PRIME),
            ("Rotate whole cube on U-axis (equiv to Uw for solved)", Commands.CUBE_Y),
            ("Rotate whole cube on U-axis counter-clockwise (Y')", Commands.CUBE_Y_PRIME),
            ("Rotate whole cube on F-axis (equiv to Fw for solved)", Commands.CUBE_Z),
            ("Rotate whole cube on F-axis counter-clockwise (Z')", Commands.CUBE_Z_PRIME),
        ]),

        ("SCRAMBLING", [
            ("Scramble cube with seed 0 (animated with moves shown)", Commands.SCRAMBLE_0),
            ("Scramble cube with seed 1-9 (fast, not animated)", "1-9"),
            ("Scramble from F.txt file in resources/scramble/", Commands.SCRAMBLE_F),
            ("Scramble with F9 configured seed (from config.py)", Commands.SCRAMBLE_F9),
            ("Special scramble variations (experiment)", "Shift/Alt+0-9"),
            ("Scramble with testing (animate + step-by-step debug)", "Ctrl+1-9"),
        ]),

        ("SOLVING COMMANDS", [
            ("Solve entire cube (animated, see every step)", Commands.SOLVE_ALL),
            ("Solve entire cube instantly (no animation)", Commands.SOLVE_ALL_NO_ANIMATION),
            ("Solve Layer 1: white cross + corners", Commands.SOLVE_L1),
            ("Solve Layer 1 cross only (for practice)", Commands.SOLVE_L1X),
            ("Solve Layer 2: middle edges around cube", Commands.SOLVE_L2),
            ("Solve Layer 3: yellow face (OLL + PLL)", Commands.SOLVE_L3),
            ("Solve Layer 3 cross only (for practice)", Commands.SOLVE_L3X),
            ("Solve big cube centers (for 4x4, 5x5, 6x6...)", Commands.SOLVE_CENTERS),
            ("Solve big cube edges (for 4x4, 5x5, 6x6...)", Commands.SOLVE_EDGES),
        ]),

        ("VIEW/CAMERA CONTROL", [
            ("Rotate view around X-axis (negative direction)", Commands.VIEW_ALPHA_X_DEC),
            ("Rotate view around X-axis (positive direction)", Commands.VIEW_ALPHA_X_INC),
            ("Rotate view around Y-axis (negative direction)", Commands.VIEW_ALPHA_Y_DEC),
            ("Rotate view around Y-axis (positive direction)", Commands.VIEW_ALPHA_Y_INC),
            ("Rotate view around Z-axis (negative direction)", Commands.VIEW_ALPHA_Z_DEC),
            ("Rotate view around Z-axis (positive direction)", Commands.VIEW_ALPHA_Z_INC),
            ("Pan view up/down/left/right", "Arrow keys"),
            ("Zoom in (make cube larger)", Commands.ZOOM_IN),
            ("Zoom out (make cube smaller)", Commands.ZOOM_OUT),
            ("Reset view to default camera position", Commands.VIEW_RESET),
        ]),

        ("ANIMATION & SPEED", [
            ("Increase animation speed (faster moves)", Commands.SPEED_UP),
            ("Decrease animation speed (slower moves)", Commands.SPEED_DOWN),
            ("Pause/Resume animation (continue from where paused)", Commands.PAUSE_TOGGLE),
            ("Toggle single-step mode (pause after EACH move)", Commands.SINGLE_STEP_TOGGLE),
            ("Next step (when in single-step mode)", "Space"),
            ("Stop animation immediately (abort solve/scramble)", "S  (during anim)"),
        ]),

        ("CUBE MODIFICATION", [
            ("Increase cube size (2x2 -> 3x3 -> 4x4...)", Commands.SIZE_INC),
            ("Decrease cube size (4x4 -> 3x3 -> 2x2...)", Commands.SIZE_DEC),
            ("Reset cube to solved (all white, yellow on top)", Commands.RESET_CUBE),
            ("Reset cube AND camera view to defaults", Commands.RESET_CUBE_AND_VIEW),
            ("Undo last move (user move or solver step)", Commands.UNDO),
        ]),

        ("SLICE RANGE (for slicing on big cubes)", [
            ("Increase start layer index for slicing", Commands.SLICE_START_INC),
            ("Decrease start layer index for slicing", Commands.SLICE_START_DEC),
            ("Increase end layer index for slicing", Commands.SLICE_STOP_INC),
            ("Decrease end layer index for slicing", Commands.SLICE_STOP_DEC),
            ("Reset to default slice range (all layers)", Commands.SLICE_RESET),
        ]),

        ("LIGHTING CONTROLS (pyglet2 backend only)", [
            ("Decrease ambient light brightness (10%-150%)", Commands.BRIGHTNESS_DOWN),
            ("Increase ambient light brightness (10%-150%)", Commands.BRIGHTNESS_UP),
            ("Decrease background gray level (0%-50% darker)", Commands.BACKGROUND_DOWN),
            ("Increase background gray level (0%-50% lighter)", Commands.BACKGROUND_UP),
        ]),

        ("TEXTURES (pyglet2 backend only)", [
            ("Cycle through texture sets (solid -> set1 -> ...)", Commands.TEXTURE_SET_NEXT),
            ("[Configure texture sets in config.py: TEXTURE_SETS]", None),
            ("[Texture images in: src/cube/resources/faces/]", None),
        ]),

        ("SHADOWS (for LDB faces visibility)", [
            ("Toggle shadow on Left face (easier to see depth)", Commands.SHADOW_TOGGLE_L),
            ("Toggle shadow on Down face (easier to see depth)", Commands.SHADOW_TOGGLE_D),
            ("Toggle shadow on Back face (easier to see depth)", Commands.SHADOW_TOGGLE_B),
        ]),

        ("RECORDING & PLAYBACK", [
            ("Start recording moves (user and solver)", Commands.RECORDING_TOGGLE),
            ("Stop recording moves", "Ctrl+P (again)"),
            ("Play back last recording", Commands.RECORDING_PLAY),
            ("Play last recording in reverse (undo moves)", Commands.RECORDING_PLAY_PRIME),
            ("Delete last recording", Commands.RECORDING_CLEAR),
            ("EXAMPLE: Record -> Scramble -> Solve -> Play reverse", None),
            ("        This shows solve then unscrambles the cube", None),
        ]),

        ("DEBUG & TESTING", [
            ("Toggle animation on/off globally", Commands.TOGGLE_ANIMATION),
            ("Toggle solver debug mode (shows steps)", Commands.TOGGLE_DEBUG),
            ("Toggle cube sanity check after every move (slow!)", Commands.TOGGLE_SANITY_CHECK),
            ("Print debug info: camera angles, layer dist...", Commands.DEBUG_INFO),
            ("Run full solver tests (compares all solvers)", Commands.TEST_RUN),
            ("Rerun last test with same scramble", Commands.TEST_RUN_LAST),
            ("Rerun last scramble (rescremble same pattern)", Commands.TEST_SCRAMBLE_LAST),
            ("Print current solver state to console (button: Diag)", None),
        ]),

        ("SOLVERS & MODES", [
            ("Switch to next available solver", Commands.SWITCH_SOLVER),
            ("Available: Beginner, LBL, Cage, Kociemba", None),
        ]),

        ("FULL MODE (focus mode)", [
            ("Toggle full mode (hide toolbar & status text)", Commands.FULL_MODE_TOGGLE),
            ("Exit full mode (return to normal view)", Commands.FULL_MODE_EXIT),
            ("[Toolbar 'Full' button also toggles full mode]", None),
            ("[Small 'X' button in top-right exits full mode]", None),
        ]),

        ("APPLICATION", [
            ("Quit application", Commands.QUIT),
            ("Test annotations (developer debug)", Commands.ANNOTATE),
            ("Test special algorithm (developer debug)", Commands.SPECIAL_ALG),
        ]),
    ]


def _resolve_key_label(rest: tuple[object, ...], service: KeyBindingService) -> str:
    """Resolve the key label from a help entry's non-description parts."""
    if len(rest) == 1:
        val = rest[0]
        if val is None:
            return ""
        if isinstance(val, str):
            return val
        # It's a Command — show all bindings joined with " or "
        labels: list[str] = service.get_all_key_labels(val)  # type: ignore[arg-type]
        return " or ".join(labels) if labels else "?"
    if len(rest) == 2:
        # Two commands — join labels with " or "
        result_parts: list[str] = []
        for c in rest:
            label: str | None = service.get_key_label(c)  # type: ignore[arg-type]
            result_parts.append(label or "?")
        return " or ".join(result_parts)
    return "?"


def _print_section(title: str, entries: list[HelpEntry], service: KeyBindingService) -> None:
    """Print a help section with title and entries."""
    print(f"\n{title.ljust(55)}| KEY")
    print("-" * 95)
    for entry in entries:
        desc: str = entry[0]
        rest: tuple[object, ...] = entry[1:]
        key_label: str = _resolve_key_label(rest, service)
        if key_label:
            print(f"  {desc}".ljust(55) + f"| {key_label}")
        else:
            print(f"  {desc}".ljust(55) + "|")


@dataclass(frozen=True)
class HelpCommand(Command):
    """Command to print keyboard help to console with human-readable descriptions."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        """Print comprehensive help with descriptions."""
        from cube.presentation.gui.key_bindings import KEY_BINDINGS_NORMAL, KeyBindingService

        service = KeyBindingService(KEY_BINDINGS_NORMAL)
        help_sections = _build_help_sections()

        print("\n")
        print("=" * 95)
        print("RUBIK'S CUBE SOLVER - COMPLETE KEYBOARD & MOUSE GUIDE".center(95))
        print("=" * 95)

        for title, entries in help_sections:
            _print_section(title, entries, service)

        print("\n" + "=" * 95)
        print("MOUSE OPERATIONS".center(95))
        print("=" * 95)
        print("\n  Right-click + drag        -> Rotate the cube model freely in 3D space")
        print("  Left-click + drag         -> Rotate cube FACES/SLICES (smart detection)")
        print("  Alt + mouse drag          -> Pan the view (move left/right/up/down)")
        print("  Mouse wheel scroll        -> Zoom in/out (scroll up = zoom in)")
        print("  Shift + click on edge     -> Rotate slice counter-clockwise")
        print("  Ctrl + click on edge      -> Rotate slice clockwise")
        print("  Click on face center      -> Rotate face (direction based on drag)")
        print("  Click on corner piece     -> Rotate adjacent faces")

        print("\n" + "=" * 95 + "\n")
        return CommandResult(no_gui_update=True)
