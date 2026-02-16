"""
Concrete command classes.

Each command type is a frozen dataclass with type-safe attributes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from cube.domain.geometric.cube_boy import FaceName
from cube.domain.solver import SolveStep

from ..ViewSetup import ViewSetup
from .base import Command, CommandContext, CommandResult

if TYPE_CHECKING:
    from cube.domain.algs.Alg import Alg
    from cube.domain.algs.SliceAbleAlg import SliceAbleAlg

# Type alias for shadow-toggleable faces
ShadowFace = Literal[FaceName.D, FaceName.B, FaceName.L]


# =============================================================================
# ROTATION COMMANDS
# =============================================================================

@dataclass(frozen=True)
class RotateCommand(Command):
    """Command to rotate a face/slice.

    Stores the Alg object directly (type-safe, no getattr).
    """
    alg: "SliceAbleAlg"
    inverse: bool = False

    def execute(self, ctx: CommandContext) -> CommandResult:
        sliced = ctx.vs.slice_alg(ctx.cube, self.alg)
        ctx.op.play(sliced, self.inverse)
        return CommandResult()


@dataclass(frozen=True)
class RotateWideCommand(Command):
    """Command to do wide rotation.

    Stores the Alg object directly (type-safe, no getattr).
    """
    alg: "Alg"
    inverse: bool = False

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.op.play(self.alg, self.inverse)
        return CommandResult()


@dataclass(frozen=True)
class CubeRotateCommand(Command):
    """Command to rotate the whole cube.

    Stores the Alg object directly (type-safe, no getattr).
    """
    alg: "Alg"
    inverse: bool = False

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.op.play(self.alg, self.inverse)
        return CommandResult()


# =============================================================================
# SCRAMBLE COMMANDS
# =============================================================================

@dataclass(frozen=True)
class ScrambleCommand(Command):
    """Command to scramble the cube with a seed."""
    seed: int

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.app.scramble(self.seed, None, animation=False, verbose=True)
        return CommandResult()


@dataclass(frozen=True)
class ScrambleF9Command(Command):
    """Command to scramble with F9 key seed."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.app.scramble(ctx.app.config.scramble_key_for_f9, None, animation=False, verbose=True)
        return CommandResult()


@dataclass(frozen=True)
class ScrambleFromFileCommand(Command):
    """Command to scramble with seed from F.txt file.

    Loads scramble seed from resources/scramble/F.txt and scrambles the cube.
    File is read each time, allowing dynamic seed changes without restart.
    """

    def execute(self, ctx: CommandContext) -> CommandResult:
        from cube.resources.scramble import load_scramble_seed
        try:
            seed = load_scramble_seed()
            ctx.app.scramble(seed, None, animation=False, verbose=True)
        except FileNotFoundError as e:
            ctx.app.set_error(f"File not found: {e}")
        except ValueError as e:
            ctx.app.set_error(f"Invalid seed: {e}")
        except Exception as e:
            ctx.app.set_error(f"Error loading seed: {e}")
        return CommandResult()


# =============================================================================
# SOLVE COMMANDS
# =============================================================================

@dataclass(frozen=True)
class SolveStepCommand(Command):
    """Command to execute a solve step."""
    step: SolveStep

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.slv.solve(what=self.step, animation=None)
        return CommandResult()


@dataclass(frozen=True)
class SolveAllCommand(Command):
    """Command to do full solve."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.slv.solve(animation=None)
        return CommandResult()


@dataclass(frozen=True)
class SolveAllNoAnimationCommand(Command):
    """Command to do full solve without animation."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.slv.solve(animation=False)
        return CommandResult()


@dataclass(frozen=True)
class SolveStepNoAnimationCommand(Command):
    """Command to execute a solve step without animation."""
    step: SolveStep

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.slv.solve(what=self.step, animation=False)
        return CommandResult()


@dataclass(frozen=True)
class SolveEdgesCommand(Command):
    """Command to solve NxN edges and track count."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        n0 = ctx.op.count
        ctx.slv.solve(what=SolveStep.NxNEdges, animation=None)
        ctx.window._last_edge_solve_count = ctx.op.count - n0
        return CommandResult()


@dataclass(frozen=True)
class DiagnosticsCommand(Command):
    """Command to print solver diagnostics to console."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        """Call solver's diagnostic() method."""
        ctx.slv.diagnostic()
        return CommandResult(no_gui_update=True)  # No visual change needed


@dataclass(frozen=True)
class HelpCommand(Command):
    """Command to print keyboard help to console with human-readable descriptions."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        """Print comprehensive help with descriptions."""
        print("\n")
        print("=" * 95)
        print("RUBIK'S CUBE SOLVER - COMPLETE KEYBOARD & MOUSE GUIDE".center(95))
        print("=" * 95)

        print("\n" + "FACE ROTATIONS".ljust(55) + "| KEY")
        print("-" * 95)
        print("  Rotate Right face clockwise".ljust(55) + "| R")
        print("  Rotate Right face counter-clockwise".ljust(55) + "| Shift+R")
        print("  Rotate Left face clockwise".ljust(55) + "| L")
        print("  Rotate Left face counter-clockwise".ljust(55) + "| Shift+L")
        print("  Rotate Up face clockwise".ljust(55) + "| U")
        print("  Rotate Up face counter-clockwise".ljust(55) + "| Shift+U")
        print("  Rotate Down face clockwise".ljust(55) + "| D")
        print("  Rotate Down face counter-clockwise".ljust(55) + "| Shift+D")
        print("  Rotate Front face clockwise".ljust(55) + "| F")
        print("  Rotate Front face counter-clockwise".ljust(55) + "| Shift+F")
        print("  Rotate Back face clockwise".ljust(55) + "| B")
        print("  Rotate Back face counter-clockwise".ljust(55) + "| Shift+B")

        print("\n" + "WIDE ROTATIONS (two outer layers)".ljust(55) + "| KEY")
        print("-" * 95)
        print("  Right two layers clockwise (Rw)".ljust(55) + "| Ctrl+R")
        print("  Right two layers counter-clockwise (Rw')".ljust(55) + "| Ctrl+Shift+R")
        print("  Left two layers clockwise (Lw)".ljust(55) + "| Ctrl+L")
        print("  Left two layers counter-clockwise (Lw')".ljust(55) + "| Ctrl+Shift+L")
        print("  Up two layers clockwise (Uw)".ljust(55) + "| Ctrl+U")
        print("  Up two layers counter-clockwise (Uw')".ljust(55) + "| Ctrl+Shift+U")
        print("  Down two layers clockwise (Dw)".ljust(55) + "| Ctrl+D")
        print("  Down two layers counter-clockwise (Dw')".ljust(55) + "| Ctrl+Shift+D")
        print("  Front two layers clockwise (Fw)".ljust(55) + "| Ctrl+F")
        print("  Front two layers counter-clockwise (Fw')".ljust(55) + "| Ctrl+Shift+F")
        print("  Back two layers clockwise (Bw)".ljust(55) + "| Ctrl+B")
        print("  Back two layers counter-clockwise (Bw')".ljust(55) + "| Ctrl+Shift+B")

        print("\n" + "SLICE MOVES (middle layers between faces)".ljust(55) + "| KEY")
        print("-" * 95)
        print("  Middle slice parallel to L-face (like Lw without L)".ljust(55) + "| M")
        print("  Middle slice counter-clockwise (M')".ljust(55) + "| Shift+M")
        print("  Equatorial slice parallel to D-face (like Dw without D)".ljust(55) + "| E")
        print("  Equatorial slice counter-clockwise (E')".ljust(55) + "| Shift+E")
        print("  Standing slice parallel to F-face (like Fw without F)".ljust(55) + "| S")
        print("  Standing slice counter-clockwise (S')".ljust(55) + "| Shift+S")

        print("\n" + "CUBE ROTATIONS (entire cube, not faces)".ljust(55) + "| KEY")
        print("-" * 95)
        print("  Rotate whole cube on R-axis (equiv to Rw for solved)".ljust(55) + "| X")
        print("  Rotate whole cube on R-axis counter-clockwise (X')".ljust(55) + "| Shift+X")
        print("  Rotate whole cube on U-axis (equiv to Uw for solved)".ljust(55) + "| Y")
        print("  Rotate whole cube on U-axis counter-clockwise (Y')".ljust(55) + "| Shift+Y")
        print("  Rotate whole cube on F-axis (equiv to Fw for solved)".ljust(55) + "| Z")
        print("  Rotate whole cube on F-axis counter-clockwise (Z')".ljust(55) + "| Shift+Z")

        print("\n" + "SCRAMBLING".ljust(55) + "| KEY")
        print("-" * 95)
        print("  Scramble cube with seed 0 (animated with moves shown)".ljust(55) + "| 0")
        print("  Scramble cube with seed 1-9 (fast, not animated)".ljust(55) + "| 1-9")
        print("  Scramble from F.txt file in resources/scramble/".ljust(55) + "| `  (backtick)")
        print("  Scramble with F9 configured seed (from config.py)".ljust(55) + "| F9")
        print("  Special scramble variations (experiment)".ljust(55) + "| Shift/Alt+0-9")
        print("  Scramble with testing (animate + step-by-step debug)".ljust(55) + "| Ctrl+1-9")

        print("\n" + "SOLVING COMMANDS".ljust(55) + "| KEY")
        print("-" * 95)
        print("  Solve entire cube (animated, see every step)".ljust(55) + "| /")
        print("  Solve entire cube instantly (no animation)".ljust(55) + "| Shift+/")
        print("  Solve Layer 1: white cross + corners".ljust(55) + "| F1")
        print("  Solve Layer 1 cross only (for practice)".ljust(55) + "| Ctrl+F1")
        print("  Solve Layer 2: middle edges around cube".ljust(55) + "| F2")
        print("  Solve Layer 3: yellow face (OLL + PLL)".ljust(55) + "| F3")
        print("  Solve Layer 3 cross only (for practice)".ljust(55) + "| Ctrl+F3")
        print("  Solve big cube centers (for 4x4, 5x5, 6x6...)".ljust(55) + "| F4")
        print("  Solve big cube edges (for 4x4, 5x5, 6x6...)".ljust(55) + "| F5")

        print("\n" + "VIEW/CAMERA CONTROL".ljust(55) + "| KEY")
        print("-" * 95)
        print("  Rotate view around X-axis (negative direction)".ljust(55) + "| Ctrl+X")
        print("  Rotate view around X-axis (positive direction)".ljust(55) + "| Alt+X")
        print("  Rotate view around Y-axis (negative direction)".ljust(55) + "| Ctrl+Y")
        print("  Rotate view around Y-axis (positive direction)".ljust(55) + "| Alt+Y")
        print("  Rotate view around Z-axis (negative direction)".ljust(55) + "| Ctrl+Z")
        print("  Rotate view around Z-axis (positive direction)".ljust(55) + "| Alt+Z")
        print("  Pan view up/down/left/right".ljust(55) + "| Arrow keys")
        print("  Zoom in (make cube larger)".ljust(55) + "| Ctrl+Up")
        print("  Zoom out (make cube smaller)".ljust(55) + "| Ctrl+Down")
        print("  Reset view to default camera position".ljust(55) + "| Alt+C")

        print("\n" + "ANIMATION & SPEED".ljust(55) + "| KEY")
        print("-" * 95)
        print("  Increase animation speed (faster moves)".ljust(55) + "| Shift+Up or NumPad+")
        print("  Decrease animation speed (slower moves)".ljust(55) + "| Shift+Down or NumPad-")
        print("  Pause/Resume animation (continue from where paused)".ljust(55) + "| Space")
        print("  Toggle single-step mode (pause after EACH move)".ljust(55) + "| Ctrl+Space")
        print("  Next step (when in single-step mode)".ljust(55) + "| Space")
        print("  Stop animation immediately (abort solve/scramble)".ljust(55) + "| S  (during anim)")

        print("\n" + "CUBE MODIFICATION".ljust(55) + "| KEY")
        print("-" * 95)
        print("  Increase cube size (2x2 -> 3x3 -> 4x4...)".ljust(55) + "| =  (Equal)")
        print("  Decrease cube size (4x4 -> 3x3 -> 2x2...)".ljust(55) + "| -  (Minus)")
        print("  Reset cube to solved (all white, yellow on top)".ljust(55) + "| C")
        print("  Reset cube AND camera view to defaults".ljust(55) + "| Ctrl+C")
        print("  Undo last move (user move or solver step)".ljust(55) + "| ,  (Comma)")

        print("\n" + "SLICE RANGE (for slicing on big cubes)".ljust(55) + "| KEY")
        print("-" * 95)
        print("  Increase start layer index for slicing".ljust(55) + "| [")
        print("  Decrease start layer index for slicing".ljust(55) + "| Shift+[")
        print("  Increase end layer index for slicing".ljust(55) + "| ]")
        print("  Decrease end layer index for slicing".ljust(55) + "| Shift+]")
        print("  Reset to default slice range (all layers)".ljust(55) + "| Alt+[")

        print("\n" + "LIGHTING CONTROLS (pyglet2 backend only)".ljust(55) + "| KEY")
        print("-" * 95)
        print("  Decrease ambient light brightness (10%-150%)".ljust(55) + "| Ctrl+[")
        print("  Increase ambient light brightness (10%-150%)".ljust(55) + "| Ctrl+]")
        print("  Decrease background gray level (0%-50% darker)".ljust(55) + "| Ctrl+Shift+[")
        print("  Increase background gray level (0%-50% lighter)".ljust(55) + "| Ctrl+Shift+]")

        print("\n" + "TEXTURES (pyglet2 backend only)".ljust(55) + "| KEY")
        print("-" * 95)
        print("  Cycle through texture sets (solid -> set1 -> ...)".ljust(55) + "| Ctrl+Shift+T")
        print("  [Configure texture sets in config.py: TEXTURE_SETS]".ljust(55) + "|")
        print("  [Texture images in: src/cube/resources/faces/]".ljust(55) + "|")

        print("\n" + "SHADOWS (for LDB faces visibility)".ljust(55) + "| KEY")
        print("-" * 95)
        print("  Toggle shadow on Left face (easier to see depth)".ljust(55) + "| F10")
        print("  Toggle shadow on Down face (easier to see depth)".ljust(55) + "| F11")
        print("  Toggle shadow on Back face (easier to see depth)".ljust(55) + "| F12")

        print("\n" + "RECORDING & PLAYBACK".ljust(55) + "| KEY")
        print("-" * 95)
        print("  Start recording moves (user and solver)".ljust(55) + "| Ctrl+P")
        print("  Stop recording moves".ljust(55) + "| Ctrl+P (again)")
        print("  Play back last recording".ljust(55) + "| P")
        print("  Play last recording in reverse (undo moves)".ljust(55) + "| Shift+P")
        print("  Delete last recording".ljust(55) + "| Alt+P")
        print("  EXAMPLE: Record -> Scramble -> Solve -> Play reverse".ljust(55) + "|")
        print("          This shows solve then unscrambles the cube".ljust(55) + "|")

        print("\n" + "DEBUG & TESTING".ljust(55) + "| KEY")
        print("-" * 95)
        print("  Toggle animation on/off globally".ljust(55) + "| O")
        print("  Toggle solver debug mode (shows steps)".ljust(55) + "| Ctrl+O")
        print("  Toggle cube sanity check after every move (slow!)".ljust(55) + "| Alt+O")
        print("  Print debug info: camera angles, layer dist...".ljust(55) + "| I")
        print("  Run full solver tests (compares all solvers)".ljust(55) + "| T")
        print("  Rerun last test with same scramble".ljust(55) + "| Alt+T")
        print("  Rerun last scramble (rescremble same pattern)".ljust(55) + "| Ctrl+T")
        print("  Print current solver state to console (button: Diag)".ljust(55) + "|")

        print("\n" + "SOLVERS & MODES".ljust(55) + "| KEY")
        print("-" * 95)
        print("  Switch to next available solver".ljust(55) + "| \\  (Backslash)")
        print("  Available: Beginner, LBL, Cage, Kociemba".ljust(55) + "|")

        print("\n" + "APPLICATION".ljust(55) + "| KEY")
        print("-" * 95)
        print("  Quit application".ljust(55) + "| Q")
        print("  Test annotations (developer debug)".ljust(55) + "| W")
        print("  Test special algorithm (developer debug)".ljust(55) + "| A")

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


# =============================================================================
# VIEW COMMANDS
# =============================================================================

@dataclass(frozen=True)
class ViewRotateCommand(Command):
    """Command to rotate the view."""
    axis: str  # 'x', 'y', or 'z'
    direction: int  # -1 or 1

    def execute(self, ctx: CommandContext) -> CommandResult:
        delta = ctx.vs.alpha_delta * self.direction
        if self.axis == 'x':
            ctx.vs.alpha_x += delta
        elif self.axis == 'y':
            ctx.vs.alpha_y += delta
        elif self.axis == 'z':
            ctx.vs.alpha_z += delta
        return CommandResult(no_gui_update=True)


@dataclass(frozen=True)
class PanCommand(Command):
    """Command to pan the view."""
    dx: int
    dy: int
    dz: int

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.vs.change_offset(self.dx, self.dy, self.dz)
        return CommandResult(no_gui_update=True)


@dataclass(frozen=True)
class ZoomInCommand(Command):
    """Command to zoom in."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.vs.dec_fov_y()
        ViewSetup.set_projection(ctx.vs, ctx.window.width, ctx.window.height, ctx.window.renderer)
        return CommandResult(no_gui_update=True)


@dataclass(frozen=True)
class ZoomOutCommand(Command):
    """Command to zoom out."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.vs.inc_fov_y()
        ViewSetup.set_projection(ctx.vs, ctx.window.width, ctx.window.height, ctx.window.renderer)
        return CommandResult(no_gui_update=True)


@dataclass(frozen=True)
class ViewResetCommand(Command):
    """Command to reset the view."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.vs.reset()
        ViewSetup.set_projection(ctx.vs, ctx.window.width, ctx.window.height, ctx.window.renderer)
        return CommandResult(no_gui_update=True)


# =============================================================================
# ANIMATION COMMANDS
# =============================================================================

@dataclass(frozen=True)
class SpeedUpCommand(Command):
    """Command to increase animation speed."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.vs.inc_speed()
        return CommandResult()


@dataclass(frozen=True)
class SpeedDownCommand(Command):
    """Command to decrease animation speed."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.vs.dec_speed()
        return CommandResult()


@dataclass(frozen=True)
class PauseToggleCommand(Command):
    """Command to toggle pause."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.vs.paused_on_single_step_mode = None
        return CommandResult()


@dataclass(frozen=True)
class SingleStepToggleCommand(Command):
    """Command to toggle single-step mode."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.vs.single_step_mode = not ctx.vs.single_step_mode
        return CommandResult()


@dataclass(frozen=True)
class StopAnimationCommand(Command):
    """Command to stop animation."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.vs.single_step_mode_stop_pressed = True
        ctx.op.abort()
        return CommandResult()


@dataclass(frozen=True)
class ToggleAnimationCommand(Command):
    """Command to toggle animation on/off."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.op.toggle_animation_on()
        return CommandResult()


# =============================================================================
# LIGHTING COMMANDS (pyglet2 backend only)
# =============================================================================

@dataclass(frozen=True)
class BrightnessUpCommand(Command):
    """Command to increase brightness."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        new_level = ctx.window.adjust_brightness(0.05)
        if new_level is not None:
            ctx.vs.debug(False, f"Brightness: {new_level:.2f}")
        return CommandResult()


@dataclass(frozen=True)
class BrightnessDownCommand(Command):
    """Command to decrease brightness."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        new_level = ctx.window.adjust_brightness(-0.05)
        if new_level is not None:
            ctx.vs.debug(False, f"Brightness: {new_level:.2f}")
        return CommandResult()


@dataclass(frozen=True)
class BackgroundUpCommand(Command):
    """Command to increase background gray level."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        new_level = ctx.window.adjust_background(0.05)
        if new_level is not None:
            ctx.vs.debug(False, f"Background: {new_level:.2f}")
        return CommandResult()


@dataclass(frozen=True)
class BackgroundDownCommand(Command):
    """Command to decrease background gray level."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        new_level = ctx.window.adjust_background(-0.05)
        if new_level is not None:
            ctx.vs.debug(False, f"Background: {new_level:.2f}")
        return CommandResult()


@dataclass(frozen=True)
class TextureSetNextCommand(Command):
    """Command to cycle to next texture set."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        texture_set = ctx.window.next_texture_set()
        if texture_set is not None:
            ctx.vs.debug(False, f"Texture: {texture_set}")
        return CommandResult()


@dataclass(frozen=True)
class TextureSetPrevCommand(Command):
    """Command to cycle to previous texture set."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        texture_set = ctx.window.prev_texture_set()
        if texture_set is not None:
            ctx.vs.debug(False, f"Texture: {texture_set}")
        return CommandResult()


@dataclass(frozen=True)
class TextureToggleCommand(Command):
    """Command to toggle texture mode on/off."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        enabled = ctx.window.toggle_texture()
        ctx.vs.debug(False, f"Texture: {'ON' if enabled else 'OFF'}")
        return CommandResult()


# =============================================================================
# SHADOW COMMANDS
# =============================================================================

@dataclass(frozen=True)
class ShadowToggleCommand(Command):
    """Command to toggle shadow for a face."""
    face: ShadowFace

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.vs.toggle_shadows_mode(self.face)
        # Note: viewer.reset() not needed - update_gui_elements() will refresh the viewer
        return CommandResult()


@dataclass(frozen=True)
class ShadowToggleAllCommand(Command):
    """Command to toggle all face shadows on/off."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.vs.toggle_all_shadows_mode()
        return CommandResult()


# =============================================================================
# CUBE SIZE COMMANDS
# =============================================================================

@dataclass(frozen=True)
class SizeIncCommand(Command):
    """Command to increase cube size."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.vs.cube_size += 1
        ctx.cube.reset(ctx.vs.cube_size)
        ctx.op.reset()
        # Note: viewer.reset() not needed - cube.reset() triggers CubeListener.on_reset()
        return CommandResult()


@dataclass(frozen=True)
class SizeDecCommand(Command):
    """Command to decrease cube size."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        if ctx.vs.cube_size > 3:
            ctx.vs.cube_size -= 1
        ctx.cube.reset(ctx.vs.cube_size)
        ctx.op.reset()
        # Note: viewer.reset() not needed - cube.reset() triggers CubeListener.on_reset()
        return CommandResult()


# =============================================================================
# SLICE SELECTION COMMANDS
# =============================================================================

@dataclass(frozen=True)
class SliceStartIncCommand(Command):
    """Command to increase slice start."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        vs = ctx.vs
        if vs.slice_start:
            vs.slice_start += 1
        else:
            vs.slice_start = 1
        if vs.slice_start > vs.slice_stop:
            vs.slice_start = vs.slice_stop
        return CommandResult()


@dataclass(frozen=True)
class SliceStartDecCommand(Command):
    """Command to decrease slice start."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        vs = ctx.vs
        if vs.slice_start:
            vs.slice_start -= 1
        else:
            vs.slice_start = 0
        if vs.slice_start < 1:
            vs.slice_start = 1
        return CommandResult()


@dataclass(frozen=True)
class SliceStopIncCommand(Command):
    """Command to increase slice stop."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        vs = ctx.vs
        vs.slice_stop += 1
        if vs.slice_stop > ctx.cube.size:
            vs.slice_stop = ctx.cube.size
        return CommandResult()


@dataclass(frozen=True)
class SliceStopDecCommand(Command):
    """Command to decrease slice stop."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        vs = ctx.vs
        vs.slice_stop -= 1
        if vs.slice_stop < vs.slice_start:
            vs.slice_stop = vs.slice_start
        return CommandResult()


@dataclass(frozen=True)
class SliceResetCommand(Command):
    """Command to reset slice selection."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.vs.slice_start = ctx.vs.slice_stop = 0
        return CommandResult()


# =============================================================================
# RECORDING COMMANDS
# =============================================================================

@dataclass(frozen=True)
class RecordingPlayCommand(Command):
    """Command to play recording."""
    inverse: bool = False

    def execute(self, ctx: CommandContext) -> CommandResult:
        recording = ctx.vs.last_recording
        if recording is not None:
            ctx.op.play_seq(recording, self.inverse)
        return CommandResult()


@dataclass(frozen=True)
class RecordingToggleCommand(Command):
    """Command to toggle recording."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        recording = ctx.op.toggle_recording()
        if recording is not None:
            ctx.vs.last_recording = recording
        return CommandResult()


@dataclass(frozen=True)
class RecordingClearCommand(Command):
    """Command to clear recording."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.vs.last_recording = None
        return CommandResult()


# =============================================================================
# DEBUG/CONFIG COMMANDS
# =============================================================================

@dataclass(frozen=True)
class ToggleDebugCommand(Command):
    """Command to toggle solver debug."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        cfg = ctx.app.config
        cfg.solver_debug = not cfg.solver_debug
        return CommandResult()


@dataclass(frozen=True)
class ToggleSanityCheckCommand(Command):
    """Command to toggle sanity check."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        cfg = ctx.app.config
        cfg.check_cube_sanity = not cfg.check_cube_sanity
        return CommandResult()


@dataclass(frozen=True)
class DebugInfoCommand(Command):
    """Command to print debug info."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        vs = ctx.vs
        print(f"{vs.alpha_x + vs.alpha_x_0=} {vs.alpha_y + vs.alpha_y_0=} {vs.alpha_z + vs.alpha_z_0=}")
        ctx.cube.cqr.print_dist()
        return CommandResult(no_gui_update=True)


# =============================================================================
# TESTING COMMANDS
# =============================================================================

@dataclass(frozen=True)
class TestRunCommand(Command):
    """Command to run tests."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.app.run_tests(1, ctx.app.config.test_number_of_scramble_iterations)
        return CommandResult()


@dataclass(frozen=True)
class TestRunLastCommand(Command):
    """Command to run last test."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        last_test_key, last_test_size = ctx.vs.get_last_scramble_test()
        ctx.app.run_single_test(last_test_key, last_test_size, ctx.app.config.solver_debug, animation=True)
        return CommandResult()


@dataclass(frozen=True)
class TestScrambleLastCommand(Command):
    """Command to scramble with last test key."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        last_test_key, last_test_size = ctx.vs.get_last_scramble_test()
        ctx.app.scramble(last_test_key, last_test_size, animation=False)
        return CommandResult()


# =============================================================================
# APPLICATION COMMANDS
# =============================================================================

@dataclass(frozen=True)
class QuitCommand(Command):
    """Command to quit the application."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        from cube.application.exceptions.app_exceptions import AppExit
        ctx.op.abort()
        ctx.window.close()
        raise AppExit


@dataclass(frozen=True)
class ResetCubeCommand(Command):
    """Command to reset the cube."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.app.reset()
        return CommandResult()


@dataclass(frozen=True)
class ResetCubeAndViewCommand(Command):
    """Command to reset cube and view."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.app.reset()
        ctx.vs.reset()
        ViewSetup.set_projection(ctx.vs, ctx.window.width, ctx.window.height, ctx.window.renderer)
        return CommandResult()


@dataclass(frozen=True)
class UndoCommand(Command):
    """Command to undo last move."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.op.undo(animation=True)
        return CommandResult()


@dataclass(frozen=True)
class SwitchSolverCommand(Command):
    """Command to switch to next solver."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.app.switch_to_next_solver()
        ctx.op.reset()

        # Rebuild toolbar solver buttons for new solver
        # Use getattr to safely access optional _toolbar attribute (pyglet2 only)
        toolbar = getattr(ctx.window, '_toolbar', None)
        if toolbar is not None:
            toolbar.rebuild_solver_buttons(ctx.app)

        return CommandResult()


# =============================================================================
# SPECIAL COMMANDS
# =============================================================================

@dataclass(frozen=True)
class AnnotateCommand(Command):
    """Command to annotate corners."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        from cube.domain.algs import Algs
        ctx.cube.front.corner_top_right.annotate(False)
        ctx.cube.front.corner_top_left.annotate(True)
        ctx.op.play(Algs.AN)
        return CommandResult()


@dataclass(frozen=True)
class SpecialAlgCommand(Command):
    """Command to execute special algorithm (requires 7x7+ cube)."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        from cube.domain.algs import Algs
        # This algorithm requires slices [2, 4, 5] which only exist on 7x7+ cubes
        if ctx.cube.size < 7:
            ctx.app.set_error(f"Special alg requires 7x7+ cube (current: {ctx.cube.size}x{ctx.cube.size})")
            return CommandResult()

        slices = [2, 4, 5]
        Rs = Algs.R[slices]
        Ls = Algs.L[slices]
        U = Algs.U
        F = Algs.F

        alg = (Rs.prime + U * 2 + Ls + F * 2 + Ls.prime + F * 2 +
               Rs * 2 + U * 2 + Rs + U * 2 + Rs.p + U * 2 + F * 2 +
               Rs * 2 + F * 2)

        ctx.op.play(alg, False)
        return CommandResult()


# =============================================================================
# TIMING COMMANDS
# =============================================================================

@dataclass(frozen=True)
class SleepCommand(Command):
    """Command to pause for a duration (non-blocking, GUI stays responsive).

    Use this in command sequences to add delays between actions.

    Example:
        Commands.SLEEP_3 + Commands.QUIT  # Wait 3 seconds, then quit
        Commands.Sleep(5) + Commands.SOLVE_ALL  # Wait 5 seconds, then solve
    """
    duration: float = 1.0  # Duration in seconds

    def execute(self, ctx: CommandContext) -> CommandResult:
        """Return result with delay_next_command set."""
        return CommandResult(delay_next_command=self.duration, no_gui_update=True)


# =============================================================================
# FILE ALGORITHM COMMANDS
# =============================================================================

@dataclass(frozen=True)
class ExecuteFileAlgCommand(Command):
    """Execute algorithm from file slot (1-5).

    Loads algorithm from f{slot}.txt resource file and executes it on the cube.
    Respects current animation setting.

    Args:
        slot: File number 1-5
        inverse: If True, play the inverse (prime) of the algorithm
    """
    slot: int
    inverse: bool = False

    def execute(self, ctx: CommandContext) -> CommandResult:
        from cube.domain.exceptions import InternalSWError
        from cube.resources.algs import load_file_alg
        try:
            alg = load_file_alg(self.slot)
            if self.inverse:
                alg = alg.prime

            # Log file name and algorithm
            file_name = f"f{self.slot}.txt"
            ctx.cube.sp.logger.debug(None, f"Executing algorithm from {file_name}: {alg}")

            ctx.op.play(alg)  # Respects current animation setting
        except FileNotFoundError as e:
            ctx.app.set_error(f"File not found: {e}")
        except ValueError as e:
            ctx.app.set_error(f"Invalid file: {e}")
        except InternalSWError as e:
            ctx.app.set_error(f"Parse error: {e}")
        except Exception as e:
            ctx.app.set_error(f"Error: {e}")
        return CommandResult()
