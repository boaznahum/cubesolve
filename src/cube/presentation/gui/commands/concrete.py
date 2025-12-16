"""
Concrete command classes.

Each command type is a frozen dataclass with type-safe attributes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TYPE_CHECKING

from cube.domain.model.cube_boy import FaceName
from cube.domain.solver import SolveStep
from .base import Command, CommandContext, CommandResult
from ..ViewSetup import ViewSetup

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
class SolveEdgesCommand(Command):
    """Command to solve NxN edges and track count."""

    def execute(self, ctx: CommandContext) -> CommandResult:
        n0 = ctx.op.count
        ctx.slv.solve(what=SolveStep.NxNEdges, animation=None)
        ctx.window._last_edge_solve_count = ctx.op.count - n0
        return CommandResult()


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
