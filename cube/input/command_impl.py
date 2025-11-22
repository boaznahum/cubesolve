"""
Concrete command implementations.

This module contains all the specific commands that can be executed
in response to keyboard input or during testing.
"""

from typing import TYPE_CHECKING

from cube.algs import Alg
from cube.app.app_exceptions import AppExit
from cube.solver.solver import SolveStep
from .commands import Command, CommandResult, AppContext

if TYPE_CHECKING:
    from cube.main_window.main_g_abstract import AbstractWindow


class QuitCommand(Command):
    """Quit the application"""

    def execute(self, ctx: AppContext) -> CommandResult:
        ctx.op.abort()  # Abort any running operations
        if ctx.window:
            ctx.window.close()
        raise AppExit  # Signal to quit

    def can_execute_during_animation(self) -> bool:
        return True  # Can always quit


class RotateFaceCommand(Command):
    """Rotate a face of the cube"""

    def __init__(self, alg: Alg, inverted: bool = False):
        self.alg = alg
        self.inverted = inverted

    def execute(self, ctx: AppContext) -> CommandResult:
        # Use operator's animation setting
        ctx.op.play(self.alg, self.inverted)
        return CommandResult.success(needs_redraw=True)

    def can_execute_during_animation(self) -> bool:
        return False

    def __repr__(self) -> str:
        inv_str = " inverted" if self.inverted else ""
        return f"RotateFaceCommand({self.alg}{inv_str})"


class ToggleAnimationCommand(Command):
    """Toggle animation on/off"""

    def execute(self, ctx: AppContext) -> CommandResult:
        ctx.op.toggle_animation_on()
        return CommandResult.no_op()

    def can_execute_during_animation(self) -> bool:
        return True


class ToggleSolverDebugCommand(Command):
    """Toggle solver debug output"""

    def execute(self, ctx: AppContext) -> CommandResult:
        from cube import config
        config.SOLVER_DEBUG = not config.SOLVER_DEBUG
        return CommandResult.no_op()

    def can_execute_during_animation(self) -> bool:
        return True


class ToggleSanityCheckCommand(Command):
    """Toggle cube sanity checking"""

    def execute(self, ctx: AppContext) -> CommandResult:
        from cube import config
        config.CHECK_CUBE_SANITY = not config.CHECK_CUBE_SANITY
        return CommandResult.no_op()

    def can_execute_during_animation(self) -> bool:
        return True


class ChangeCubeSizeCommand(Command):
    """Change cube size (increase or decrease)"""

    def __init__(self, delta: int):
        self.delta = delta  # +1 or -1

    def execute(self, ctx: AppContext) -> CommandResult:
        new_size = ctx.vs.cube_size + self.delta
        if new_size < 3:
            return CommandResult.error("Minimum cube size is 3")

        ctx.vs.cube_size = new_size
        ctx.cube.reset(new_size)
        ctx.op.reset()

        # Viewer reset handled by caller based on result
        return CommandResult(needs_redraw=True, needs_viewer_reset=True)

    def can_execute_during_animation(self) -> bool:
        return False

    def __repr__(self) -> str:
        return f"ChangeCubeSizeCommand({self.delta:+d})"


class AdjustViewAngleCommand(Command):
    """Adjust view rotation angle"""

    def __init__(self, axis: str, delta: float):
        self.axis = axis  # 'x', 'y', or 'z'
        self.delta = delta

    def execute(self, ctx: AppContext) -> CommandResult:
        if self.axis == 'x':
            ctx.vs.alpha_x += self.delta
        elif self.axis == 'y':
            ctx.vs.alpha_y += self.delta
        elif self.axis == 'z':
            ctx.vs.alpha_z += self.delta
        else:
            return CommandResult.error(f"Unknown axis: {self.axis}")

        return CommandResult.success(needs_redraw=True)

    def can_execute_during_animation(self) -> bool:
        return True  # View changes allowed during animation

    def __repr__(self) -> str:
        return f"AdjustViewAngleCommand({self.axis}, {self.delta:+.1f})"


class ZoomCommand(Command):
    """Zoom in or out"""

    def __init__(self, zoom_in: bool, window_width: int = 0, window_height: int = 0):
        self.zoom_in = zoom_in
        self.window_width = window_width
        self.window_height = window_height

    def execute(self, ctx: AppContext) -> CommandResult:
        if self.zoom_in:
            ctx.vs.dec_fov_y()  # Smaller FOV = zoom in
        else:
            ctx.vs.inc_fov_y()  # Larger FOV = zoom out

        if self.window_width > 0 and self.window_height > 0:
            ctx.vs.set_projection(self.window_width, self.window_height)

        return CommandResult.success(needs_redraw=True)

    def can_execute_during_animation(self) -> bool:
        return True

    def __repr__(self) -> str:
        direction = "in" if self.zoom_in else "out"
        return f"ZoomCommand({direction})"


class PanCommand(Command):
    """Pan the view"""

    def __init__(self, axis: str, delta: float):
        self.axis = axis  # 'x' or 'y'
        self.delta = delta

    def execute(self, ctx: AppContext) -> CommandResult:
        if self.axis == 'x':
            ctx.vs.offset_x += self.delta
        elif self.axis == 'y':
            ctx.vs.offset_y += self.delta
        else:
            return CommandResult.error(f"Unknown pan axis: {self.axis}")

        return CommandResult.success(needs_redraw=True)

    def can_execute_during_animation(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"PanCommand({self.axis}, {self.delta:+.1f})"


class AdjustAnimationSpeedCommand(Command):
    """Adjust animation speed"""

    def __init__(self, increase: bool):
        self.increase = increase

    def execute(self, ctx: AppContext) -> CommandResult:
        if self.increase:
            ctx.vs.inc_speed()
        else:
            ctx.vs.dec_speed()
        return CommandResult.no_op()

    def can_execute_during_animation(self) -> bool:
        return True

    def __repr__(self) -> str:
        direction = "increase" if self.increase else "decrease"
        return f"AdjustAnimationSpeedCommand({direction})"


class ToggleSingleStepModeCommand(Command):
    """Toggle single-step mode on/off"""

    def execute(self, ctx: AppContext) -> CommandResult:
        ctx.vs.single_step_mode = not ctx.vs.single_step_mode
        return CommandResult.no_op()

    def can_execute_during_animation(self) -> bool:
        return True


class UnpauseSingleStepCommand(Command):
    """Unpause in single-step mode (advance to next step)"""

    def execute(self, ctx: AppContext) -> CommandResult:
        ctx.vs.paused_on_single_step_mode = None
        return CommandResult.no_op()

    def can_execute_during_animation(self) -> bool:
        return True


class AbortCommand(Command):
    """Abort current operation (solver, animation)"""

    def execute(self, ctx: AppContext) -> CommandResult:
        ctx.op.abort()
        return CommandResult.success(needs_redraw=True)

    def can_execute_during_animation(self) -> bool:
        return True


class SolveCommand(Command):
    """Solve the cube (full or partial)"""

    def __init__(self, animation: bool = True, step: SolveStep = SolveStep.ALL):
        self.animation = animation
        self.step = step

    def execute(self, ctx: AppContext) -> CommandResult:
        ctx.slv.solve(animation=self.animation, step=self.step)
        return CommandResult.success(needs_redraw=True)

    def can_execute_during_animation(self) -> bool:
        return False

    def __repr__(self) -> str:
        anim = "animated" if self.animation else "instant"
        return f"SolveCommand({anim}, {self.step.name})"


class ScrambleCommand(Command):
    """Scramble the cube"""

    def __init__(self, seed: int, animation: bool = False):
        self.seed = seed
        self.animation = animation

    def execute(self, ctx: AppContext) -> CommandResult:
        from cube.algs import Algs

        # Generate scramble algorithm
        scramble_alg = Algs.scramble(ctx.cube.size, seed=self.seed)

        # Save to app state
        ctx.vs.last_scramble = scramble_alg

        # Execute scramble
        ctx.op.play(scramble_alg, animation=self.animation)

        return CommandResult.success(needs_redraw=True)

    def can_execute_during_animation(self) -> bool:
        return False

    def __repr__(self) -> str:
        anim = "animated" if self.animation else "instant"
        return f"ScrambleCommand(seed={self.seed}, {anim})"


class ResetCubeCommand(Command):
    """Reset cube to solved state"""

    def __init__(self, reset_view: bool = False):
        self.reset_view = reset_view

    def execute(self, ctx: AppContext) -> CommandResult:
        ctx.cube.reset(ctx.vs.cube_size)
        ctx.op.reset()

        if self.reset_view:
            ctx.vs.reset_view()

        return CommandResult(needs_redraw=True, needs_viewer_reset=True)

    def can_execute_during_animation(self) -> bool:
        return False

    def __repr__(self) -> str:
        view_str = " + view" if self.reset_view else ""
        return f"ResetCubeCommand({view_str})"


class ResetViewCommand(Command):
    """Reset view only (not cube)"""

    def execute(self, ctx: AppContext) -> CommandResult:
        ctx.vs.reset_view()
        return CommandResult.success(needs_redraw=True)

    def can_execute_during_animation(self) -> bool:
        return True


class UndoCommand(Command):
    """Undo last move"""

    def execute(self, ctx: AppContext) -> CommandResult:
        ctx.op.undo()
        return CommandResult.success(needs_redraw=True)

    def can_execute_during_animation(self) -> bool:
        return False


class PlayRecordingCommand(Command):
    """Play recorded sequence"""

    def __init__(self, inverted: bool = False):
        self.inverted = inverted

    def execute(self, ctx: AppContext) -> CommandResult:
        recording = ctx.vs.last_recording
        if recording is None:
            return CommandResult.error("No recording to play")

        ctx.op.play_seq(recording, self.inverted)
        return CommandResult.success(needs_redraw=True)

    def can_execute_during_animation(self) -> bool:
        return False

    def __repr__(self) -> str:
        inv_str = " reversed" if self.inverted else ""
        return f"PlayRecordingCommand({inv_str})"


class ToggleRecordingCommand(Command):
    """Start or stop recording"""

    def execute(self, ctx: AppContext) -> CommandResult:
        if ctx.op.is_recording():
            # Stop recording
            recording = ctx.op.stop_recording()
            ctx.vs.last_recording = recording
        else:
            # Start recording
            ctx.op.start_recording()

        return CommandResult.no_op()

    def can_execute_during_animation(self) -> bool:
        return True


class ClearRecordingCommand(Command):
    """Clear last recording"""

    def execute(self, ctx: AppContext) -> CommandResult:
        ctx.vs.last_recording = None
        return CommandResult.no_op()

    def can_execute_during_animation(self) -> bool:
        return True
