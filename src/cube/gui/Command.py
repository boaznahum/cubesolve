"""
Command enum - semantic actions for the cube solver.

Each command defines its handler lazily. The handler is created on first
execute() and cached for subsequent calls.

Design:
- Command enum value is a tuple: (factory_function, *args)
- execute(ctx) creates handler on first call, caches it
- No switch/case needed - each command knows what to do
- CommandContext provides access to app, cube, operator, etc.
- Imports are lazy (inside handlers) to avoid load-time dependencies
- Commands support + and * operators for building sequences

Usage:
    from cube.gui.Command import Command, CommandContext, CommandSequence

    # Execute single command
    ctx = CommandContext.from_window(window)
    Command.SCRAMBLE_1.execute(ctx)

    # Build command sequences with + and *
    seq = Command.SPEED_UP * 5 + Command.SCRAMBLE_1 + Command.SOLVE_ALL + Command.QUIT
    seq.execute_all(ctx)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Callable

from cube.model.cube_boy import FaceName
from cube.solver import SolveStep

if TYPE_CHECKING:
    from cube.app.AbstractApp import AbstractApp
    from cube.main_window.AbstractWindow import AbstractWindow


# =============================================================================
# COMMAND CONTEXT
# =============================================================================

@dataclass
class CommandContext:
    """Execution context for commands.

    Provides access to all application components needed by command handlers.
    """
    window: "AbstractWindow"

    @property
    def app(self) -> "AbstractApp":
        return self.window.app

    @property
    def op(self):
        return self.app.op

    @property
    def vs(self):
        return self.app.vs

    @property
    def slv(self):
        return self.app.slv

    @property
    def cube(self):
        return self.app.cube

    @property
    def viewer(self):
        return self.window.viewer

    @classmethod
    def from_window(cls, window: "AbstractWindow") -> "CommandContext":
        """Create context from a window."""
        return cls(window=window)


# =============================================================================
# RESULT TYPE
# =============================================================================

@dataclass
class CommandResult:
    """Result of command execution."""
    handled: bool = True
    no_gui_update: bool = False  # True if GUI doesn't need updating


# Type alias for handler function
Handler = Callable[["CommandContext"], CommandResult | None]


# =============================================================================
# COMMAND SEQUENCE
# =============================================================================

class CommandSequence:
    """A sequence of commands that can be executed together.

    Supports + and * operators for building sequences:
        seq = Command.SPEED_UP * 3 + Command.SCRAMBLE_1 + Command.SOLVE_ALL

    Usage:
        seq.execute_all(ctx)  # Execute all commands in sequence
    """

    def __init__(self, commands: list["Command"] | None = None):
        """Initialize with optional list of commands."""
        self._commands: list["Command"] = commands if commands else []

    @property
    def commands(self) -> list["Command"]:
        """Get the list of commands."""
        return self._commands

    def __add__(self, other: "Command | CommandSequence") -> "CommandSequence":
        """Concatenate with another command or sequence."""
        if isinstance(other, CommandSequence):
            return CommandSequence(self._commands + other._commands)
        else:
            # other is a Command
            return CommandSequence(self._commands + [other])

    def __radd__(self, other: "Command") -> "CommandSequence":
        """Support Command + CommandSequence."""
        return CommandSequence([other] + self._commands)

    def __mul__(self, n: int) -> "CommandSequence":
        """Repeat the sequence n times."""
        return CommandSequence(self._commands * n)

    def __rmul__(self, n: int) -> "CommandSequence":
        """Support n * sequence."""
        return self.__mul__(n)

    def __len__(self) -> int:
        """Number of commands in sequence."""
        return len(self._commands)

    def __iter__(self):
        """Iterate over commands."""
        return iter(self._commands)

    def __repr__(self) -> str:
        """String representation."""
        cmd_names = [cmd.name for cmd in self._commands]
        return f"CommandSequence([{', '.join(cmd_names)}])"

    def execute_all(self, ctx: "CommandContext") -> list[CommandResult]:
        """Execute all commands in sequence.

        Args:
            ctx: CommandContext providing access to app components

        Returns:
            List of CommandResult from each command
        """
        results = []
        for cmd in self._commands:
            results.append(cmd.execute(ctx))
        return results


# =============================================================================
# HANDLER FACTORIES (called lazily on first execute)
# =============================================================================

def _rotate(alg_name: str, inverse: bool) -> Handler:
    """Create handler for face/slice rotation."""
    from cube.algs import Algs
    alg = getattr(Algs, alg_name)

    def handler(ctx: CommandContext) -> None:
        sliced = ctx.vs.slice_alg(ctx.cube, alg)
        ctx.op.play(sliced, inverse)
    return handler


def _rotate_wide(alg_name: str, inverse: bool) -> Handler:
    """Create handler for wide rotation."""
    from cube.algs import Algs
    alg = getattr(Algs, alg_name)

    def handler(ctx: CommandContext) -> None:
        ctx.op.play(alg, inverse)
    return handler


def _cube_rotate(alg_name: str, inverse: bool) -> Handler:
    """Create handler for whole-cube rotation."""
    from cube.algs import Algs
    alg = getattr(Algs, alg_name)

    def handler(ctx: CommandContext) -> None:
        ctx.op.play(alg, inverse)
    return handler


def _scramble(seed: int) -> Handler:
    """Create handler for scramble command."""
    def handler(ctx: CommandContext) -> None:
        ctx.app.scramble(seed, None, animation=False, verbose=True)
    return handler


def _solve(step: SolveStep) -> Handler:
    """Create handler for partial solve."""
    def handler(ctx: CommandContext) -> None:
        ctx.slv.solve(what=step, animation=None)
    return handler


def _view_rotate(axis: str, direction: int) -> Handler:
    """Create handler for view rotation."""
    def handler(ctx: CommandContext) -> CommandResult:
        delta = ctx.vs.alpha_delta * direction
        if axis == 'x':
            ctx.vs.alpha_x += delta
        elif axis == 'y':
            ctx.vs.alpha_y += delta
        elif axis == 'z':
            ctx.vs.alpha_z += delta
        return CommandResult(no_gui_update=True)
    return handler


def _pan(dx: int, dy: int, dz: int) -> Handler:
    """Create handler for view panning."""
    def handler(ctx: CommandContext) -> CommandResult:
        ctx.vs.change_offset(dx, dy, dz)
        return CommandResult(no_gui_update=True)
    return handler


def _shadow_toggle(face: FaceName) -> Handler:
    """Create handler for shadow toggle."""
    def handler(ctx: CommandContext) -> None:
        ctx.vs.toggle_shadows_mode(face)
        ctx.viewer.reset()
    return handler


def _recording_play(inverse: bool) -> Handler:
    """Create handler for recording playback."""
    def handler(ctx: CommandContext) -> None:
        recording = ctx.vs.last_recording
        if recording is not None:
            ctx.op.play_seq(recording, inverse)
    return handler


def _simple(fn: Callable[["CommandContext"], CommandResult | None]) -> Handler:
    """Wrap a simple function as a handler (identity for consistency)."""
    return fn


# =============================================================================
# STANDALONE HANDLERS
# =============================================================================

def _solve_all(ctx: CommandContext) -> None:
    """Full solve."""
    ctx.slv.solve(animation=None)


def _solve_edges(ctx: CommandContext) -> None:
    """Solve NxN edges and track count."""
    n0 = ctx.op.count
    ctx.slv.solve(what=SolveStep.NxNEdges, animation=None)
    ctx.window._last_edge_solve_count = ctx.op.count - n0


def _zoom_in(ctx: CommandContext) -> CommandResult:
    """Zoom in."""
    ctx.vs.dec_fov_y()
    ctx.vs.set_projection(ctx.window.width, ctx.window.height, ctx.window.renderer)
    return CommandResult(no_gui_update=True)


def _zoom_out(ctx: CommandContext) -> CommandResult:
    """Zoom out."""
    ctx.vs.inc_fov_y()
    ctx.vs.set_projection(ctx.window.width, ctx.window.height, ctx.window.renderer)
    return CommandResult(no_gui_update=True)


def _view_reset(ctx: CommandContext) -> CommandResult:
    """Reset view."""
    ctx.vs.reset()
    ctx.vs.set_projection(ctx.window.width, ctx.window.height, ctx.window.renderer)
    return CommandResult(no_gui_update=True)


def _speed_up(ctx: CommandContext) -> None:
    ctx.vs.inc_speed()


def _speed_down(ctx: CommandContext) -> None:
    ctx.vs.dec_speed()


def _pause_toggle(ctx: CommandContext) -> None:
    ctx.vs.paused_on_single_step_mode = None


def _single_step_toggle(ctx: CommandContext) -> None:
    ctx.vs.single_step_mode = not ctx.vs.single_step_mode


def _stop_animation(ctx: CommandContext) -> None:
    ctx.vs.single_step_mode_stop_pressed = True
    ctx.op.abort()


def _size_inc(ctx: CommandContext) -> None:
    ctx.vs.cube_size += 1
    ctx.cube.reset(ctx.vs.cube_size)
    ctx.op.reset()
    ctx.viewer.reset()


def _size_dec(ctx: CommandContext) -> None:
    if ctx.vs.cube_size > 3:
        ctx.vs.cube_size -= 1
    ctx.cube.reset(ctx.vs.cube_size)
    ctx.op.reset()
    ctx.viewer.reset()


def _slice_start_inc(ctx: CommandContext) -> None:
    vs = ctx.vs
    if vs.slice_start:
        vs.slice_start += 1
    else:
        vs.slice_start = 1
    if vs.slice_start > vs.slice_stop:
        vs.slice_start = vs.slice_stop


def _slice_start_dec(ctx: CommandContext) -> None:
    vs = ctx.vs
    if vs.slice_start:
        vs.slice_start -= 1
    else:
        vs.slice_start = 0
    if vs.slice_start < 1:
        vs.slice_start = 1


def _slice_stop_inc(ctx: CommandContext) -> None:
    vs = ctx.vs
    vs.slice_stop += 1
    if vs.slice_stop > ctx.cube.size:
        vs.slice_stop = ctx.cube.size


def _slice_stop_dec(ctx: CommandContext) -> None:
    vs = ctx.vs
    vs.slice_stop -= 1
    if vs.slice_stop < vs.slice_start:
        vs.slice_stop = vs.slice_start


def _slice_reset(ctx: CommandContext) -> None:
    ctx.vs.slice_start = ctx.vs.slice_stop = 0


def _recording_toggle(ctx: CommandContext) -> None:
    recording = ctx.op.toggle_recording()
    if recording is not None:
        ctx.vs.last_recording = recording


def _recording_clear(ctx: CommandContext) -> None:
    ctx.vs.last_recording = None


def _toggle_animation(ctx: CommandContext) -> None:
    ctx.op.toggle_animation_on()


def _toggle_debug(ctx: CommandContext) -> None:
    from cube import config
    config.SOLVER_DEBUG = not config.SOLVER_DEBUG


def _toggle_sanity(ctx: CommandContext) -> None:
    from cube import config
    config.CHECK_CUBE_SANITY = not config.CHECK_CUBE_SANITY


def _debug_info(ctx: CommandContext) -> CommandResult:
    vs = ctx.vs
    print(f"{vs.alpha_x + vs.alpha_x_0=} {vs.alpha_y + vs.alpha_y_0=} {vs.alpha_z + vs.alpha_z_0=}")
    ctx.cube.cqr.print_dist()
    return CommandResult(no_gui_update=True)


def _test_run(ctx: CommandContext) -> None:
    from cube import config
    ctx.app.run_tests(1, config.TEST_NUMBER_OF_SCRAMBLE_ITERATIONS)


def _test_run_last(ctx: CommandContext) -> None:
    from cube import config
    last_test_key, last_test_size = ctx.vs.get_last_scramble_test()
    ctx.app.run_single_test(last_test_key, last_test_size, config.SOLVER_DEBUG, animation=None)


def _test_scramble_last(ctx: CommandContext) -> None:
    last_test_key, last_test_size = ctx.vs.get_last_scramble_test()
    ctx.app.scramble(last_test_key, last_test_size, animation=False)


def _quit(ctx: CommandContext) -> None:
    from cube.app.app_exceptions import AppExit
    ctx.op.abort()
    ctx.window.close()
    raise AppExit


def _reset_cube(ctx: CommandContext) -> None:
    ctx.app.reset()


def _reset_cube_and_view(ctx: CommandContext) -> None:
    ctx.app.reset()
    ctx.vs.reset()
    ctx.vs.set_projection(ctx.window.width, ctx.window.height, ctx.window.renderer)


def _undo(ctx: CommandContext) -> None:
    ctx.op.undo(animation=True)


def _switch_solver(ctx: CommandContext) -> None:
    ctx.app.switch_to_next_solver()
    ctx.op.reset()


def _annotate(ctx: CommandContext) -> None:
    from cube.algs import Algs
    ctx.cube.front.corner_top_right.annotate(False)
    ctx.cube.front.corner_top_left.annotate(True)
    ctx.op.play(Algs.AN)


def _special_alg(ctx: CommandContext) -> None:
    from cube.algs import Algs
    slices = [2, 4, 5]
    Rs = Algs.R[slices]
    Ls = Algs.L[slices]
    U = Algs.U
    F = Algs.F

    alg = (Rs.prime + U * 2 + Ls + F * 2 + Ls.prime + F * 2 +
           Rs * 2 + U * 2 + Rs + U * 2 + Rs.p + U * 2 + F * 2 +
           Rs * 2 + F * 2)

    ctx.op.play(alg, False)


def _scramble_f9(ctx: CommandContext) -> None:
    from cube import config
    ctx.app.scramble(config.SCRAMBLE_KEY_FOR_F9, None, animation=False, verbose=True)


# =============================================================================
# COMMAND ENUM
# =============================================================================

# Handler cache - populated lazily on first execute
_handler_cache: dict["Command", Handler] = {}


class Command(Enum):
    """All commands for the cube solver.

    Each value is either:
    - A tuple (factory, *args) for lazy handler creation
    - A direct handler function wrapped with _simple
    """

    # Face Rotations - lazy with alg name string (no Algs import at load time)
    ROTATE_R = (_rotate, "R", False)
    ROTATE_R_PRIME = (_rotate, "R", True)
    ROTATE_L = (_rotate, "L", False)
    ROTATE_L_PRIME = (_rotate, "L", True)
    ROTATE_U = (_rotate, "U", False)
    ROTATE_U_PRIME = (_rotate, "U", True)
    ROTATE_D = (_rotate, "D", False)
    ROTATE_D_PRIME = (_rotate, "D", True)
    ROTATE_F = (_rotate, "F", False)
    ROTATE_F_PRIME = (_rotate, "F", True)
    ROTATE_B = (_rotate, "B", False)
    ROTATE_B_PRIME = (_rotate, "B", True)

    # Wide Rotations
    ROTATE_RW = (_rotate_wide, "Rw", False)
    ROTATE_RW_PRIME = (_rotate_wide, "Rw", True)
    ROTATE_LW = (_rotate_wide, "Lw", False)
    ROTATE_LW_PRIME = (_rotate_wide, "Lw", True)
    ROTATE_UW = (_rotate_wide, "Uw", False)
    ROTATE_UW_PRIME = (_rotate_wide, "Uw", True)
    ROTATE_DW = (_rotate_wide, "Dw", False)
    ROTATE_DW_PRIME = (_rotate_wide, "Dw", True)
    ROTATE_FW = (_rotate_wide, "Fw", False)
    ROTATE_FW_PRIME = (_rotate_wide, "Fw", True)
    ROTATE_BW = (_rotate_wide, "Bw", False)
    ROTATE_BW_PRIME = (_rotate_wide, "Bw", True)

    # Slice Moves
    SLICE_M = (_rotate, "M", False)
    SLICE_M_PRIME = (_rotate, "M", True)
    SLICE_E = (_rotate, "E", False)
    SLICE_E_PRIME = (_rotate, "E", True)
    SLICE_S = (_rotate, "S", False)
    SLICE_S_PRIME = (_rotate, "S", True)

    # Cube Rotations
    CUBE_X = (_cube_rotate, "X", False)
    CUBE_X_PRIME = (_cube_rotate, "X", True)
    CUBE_Y = (_cube_rotate, "Y", False)
    CUBE_Y_PRIME = (_cube_rotate, "Y", True)
    CUBE_Z = (_cube_rotate, "Z", False)
    CUBE_Z_PRIME = (_cube_rotate, "Z", True)

    # Scrambles
    SCRAMBLE_0 = (_scramble, 0)
    SCRAMBLE_1 = (_scramble, 1)
    SCRAMBLE_2 = (_scramble, 2)
    SCRAMBLE_3 = (_scramble, 3)
    SCRAMBLE_4 = (_scramble, 4)
    SCRAMBLE_5 = (_scramble, 5)
    SCRAMBLE_6 = (_scramble, 6)
    SCRAMBLE_7 = (_scramble, 7)
    SCRAMBLE_8 = (_scramble, 8)
    SCRAMBLE_9 = (_scramble, 9)
    SCRAMBLE_F9 = (_simple, _scramble_f9)

    # Solve Commands
    SOLVE_ALL = (_simple, _solve_all)
    SOLVE_L1 = (_solve, SolveStep.L1)
    SOLVE_L1X = (_solve, SolveStep.L1x)
    SOLVE_L2 = (_solve, SolveStep.L2)
    SOLVE_L3 = (_solve, SolveStep.L3)
    SOLVE_L3X = (_solve, SolveStep.L3x)
    SOLVE_CENTERS = (_solve, SolveStep.NxNCenters)
    SOLVE_EDGES = (_simple, _solve_edges)

    # View Control
    VIEW_ALPHA_X_DEC = (_view_rotate, 'x', -1)
    VIEW_ALPHA_X_INC = (_view_rotate, 'x', 1)
    VIEW_ALPHA_Y_DEC = (_view_rotate, 'y', -1)
    VIEW_ALPHA_Y_INC = (_view_rotate, 'y', 1)
    VIEW_ALPHA_Z_DEC = (_view_rotate, 'z', -1)
    VIEW_ALPHA_Z_INC = (_view_rotate, 'z', 1)
    PAN_UP = (_pan, 0, 1, 0)
    PAN_DOWN = (_pan, 0, -1, 0)
    PAN_LEFT = (_pan, -1, 0, 0)
    PAN_RIGHT = (_pan, 1, 0, 0)
    ZOOM_IN = (_simple, _zoom_in)
    ZOOM_OUT = (_simple, _zoom_out)
    VIEW_RESET = (_simple, _view_reset)

    # Animation Control
    SPEED_UP = (_simple, _speed_up)
    SPEED_DOWN = (_simple, _speed_down)
    PAUSE_TOGGLE = (_simple, _pause_toggle)
    SINGLE_STEP_TOGGLE = (_simple, _single_step_toggle)
    STOP_ANIMATION = (_simple, _stop_animation)

    # Shadow Toggles
    SHADOW_TOGGLE_L = (_shadow_toggle, FaceName.L)
    SHADOW_TOGGLE_D = (_shadow_toggle, FaceName.D)
    SHADOW_TOGGLE_B = (_shadow_toggle, FaceName.B)

    # Cube Size
    SIZE_INC = (_simple, _size_inc)
    SIZE_DEC = (_simple, _size_dec)

    # Slice Selection
    SLICE_START_INC = (_simple, _slice_start_inc)
    SLICE_START_DEC = (_simple, _slice_start_dec)
    SLICE_STOP_INC = (_simple, _slice_stop_inc)
    SLICE_STOP_DEC = (_simple, _slice_stop_dec)
    SLICE_RESET = (_simple, _slice_reset)

    # Recording
    RECORDING_PLAY = (_recording_play, False)
    RECORDING_PLAY_PRIME = (_recording_play, True)
    RECORDING_TOGGLE = (_simple, _recording_toggle)
    RECORDING_CLEAR = (_simple, _recording_clear)

    # Debug/Config
    TOGGLE_ANIMATION = (_simple, _toggle_animation)
    TOGGLE_DEBUG = (_simple, _toggle_debug)
    TOGGLE_SANITY_CHECK = (_simple, _toggle_sanity)
    DEBUG_INFO = (_simple, _debug_info)

    # Testing
    TEST_RUN = (_simple, _test_run)
    TEST_RUN_LAST = (_simple, _test_run_last)
    TEST_SCRAMBLE_LAST = (_simple, _test_scramble_last)

    # Application
    QUIT = (_simple, _quit)
    RESET_CUBE = (_simple, _reset_cube)
    RESET_CUBE_AND_VIEW = (_simple, _reset_cube_and_view)
    UNDO = (_simple, _undo)
    SWITCH_SOLVER = (_simple, _switch_solver)

    # Special
    ANNOTATE = (_simple, _annotate)
    SPECIAL_ALG = (_simple, _special_alg)

    def _get_handler(self) -> Handler:
        """Get or create the handler for this command (lazy with cache)."""
        if self not in _handler_cache:
            value = self.value
            if isinstance(value, tuple):
                factory, *args = value
                _handler_cache[self] = factory(*args)
            else:
                # Direct handler function (shouldn't happen with current design)
                _handler_cache[self] = value
        return _handler_cache[self]

    def execute(self, ctx: CommandContext) -> CommandResult:
        """Execute this command with given context.

        Handler is created lazily on first call and cached.

        Args:
            ctx: CommandContext providing access to app components

        Returns:
            CommandResult with execution status
        """
        handler = self._get_handler()
        result = handler(ctx)
        if result is None:
            return CommandResult()
        return result

    def __add__(self, other: "Command | CommandSequence") -> CommandSequence:
        """Concatenate with another command or sequence.

        Example:
            seq = Command.SCRAMBLE_1 + Command.SOLVE_ALL + Command.QUIT
        """
        if isinstance(other, CommandSequence):
            return CommandSequence([self] + other._commands)
        else:
            return CommandSequence([self, other])

    def __mul__(self, n: int) -> CommandSequence:
        """Repeat this command n times.

        Example:
            seq = Command.SPEED_UP * 5  # 5 speed-ups
        """
        return CommandSequence([self] * n)

    def __rmul__(self, n: int) -> CommandSequence:
        """Support n * Command syntax."""
        return self.__mul__(n)
