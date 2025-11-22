"""
Keyboard event generator that yields commands.

This module provides the generator that converts keyboard events into commands.
The generator pattern allows both real GUI event loops and test harnesses to
control execution flow.
"""

from dataclasses import dataclass
from typing import Iterator, Iterable, Any

# Import key constants - handle headless environments
try:
    from pyglet.window import key  # type: ignore
except (ImportError, OSError):
    # Headless environment - key constants will be provided by test file
    key: Any = None  # type: ignore

from cube.algs import Algs
from cube.solver.solver import SolveStep
from .commands import Command
from .command_impl import (
    QuitCommand, RotateFaceCommand, ToggleAnimationCommand,
    ToggleSolverDebugCommand, ToggleSanityCheckCommand,
    ChangeCubeSizeCommand, AdjustViewAngleCommand, ZoomCommand, PanCommand,
    AdjustAnimationSpeedCommand, ToggleSingleStepModeCommand,
    UnpauseSingleStepCommand, AbortCommand, SolveCommand, ScrambleCommand,
    ResetCubeCommand, ResetViewCommand, UndoCommand,
    PlayRecordingCommand, ToggleRecordingCommand, ClearRecordingCommand,
)


@dataclass
class KeyEvent:
    """
    Represents a keyboard event.

    Attributes:
        symbol: The key symbol (from pyglet.window.key)
        modifiers: Modifier keys pressed (Shift, Ctrl, Alt)
    """
    symbol: int
    modifiers: int

    @property
    def has_shift(self) -> bool:
        """Whether Shift is pressed"""
        return bool(self.modifiers & key.MOD_SHIFT)

    @property
    def has_ctrl(self) -> bool:
        """Whether Ctrl is pressed"""
        return bool(self.modifiers & key.MOD_CTRL)

    @property
    def has_alt(self) -> bool:
        """Whether Alt is pressed"""
        return bool(self.modifiers & key.MOD_ALT)

    def __repr__(self) -> str:
        mod_str = key.modifiers_string(self.modifiers)
        sym_str = key.symbol_string(self.symbol)
        if mod_str:
            return f"KeyEvent({mod_str}+{sym_str})"
        return f"KeyEvent({sym_str})"


def keyboard_event_generator(
    events: Iterable[KeyEvent],
    animation_running: bool = False
) -> Iterator[Command]:
    """
    Generator that yields commands from keyboard events.

    This is the core of the hybrid generator+command pattern. The generator:
    1. Takes keyboard events (from GUI or tests)
    2. Maps each event to a command (or None)
    3. Yields commands one at a time
    4. Caller executes command and can check state before continuing

    The yield point is where GUI refresh happens in the real application,
    and where tests can assert on state.

    Args:
        events: Iterable of keyboard events (real or simulated)
        animation_running: Whether animation is currently running

    Yields:
        Commands to execute, one at a time

    Example (GUI usage):
        # Real GUI loop
        for event in keyboard_events:
            for cmd in keyboard_event_generator([event], window.animation_running):
                result = cmd.execute(app)
                if result.needs_redraw:
                    window.update_gui_elements()

    Example (Test usage):
        # Test with scripted keys
        test_events = [
            KeyEvent(key.R, 0),
            KeyEvent(key.U, 0),
        ]
        for cmd in keyboard_event_generator(test_events):
            result = cmd.execute(test_app)
            assert result.error is None
            # Check state here!
    """
    for event in events:
        # Skip modifier-only keys
        if key.LSHIFT <= event.symbol <= key.ROPTION:
            continue

        # Get command for this event
        cmd = _map_event_to_command(event, animation_running)

        # Skip if no command mapped
        if cmd is None:
            continue

        # Check if command can run during animation
        if animation_running and not cmd.can_execute_during_animation():
            # Only abort/quit allowed during animation
            if not isinstance(cmd, (QuitCommand, AbortCommand)):
                continue

        # Yield command - this is where caller can execute and check state
        yield cmd


def _map_event_to_command(event: KeyEvent, animation_running: bool) -> Command | None:
    """
    Map a keyboard event to a command.

    This is the "command factory" that translates keys to commands.

    Args:
        event: The keyboard event
        animation_running: Whether animation is running (affects some commands)

    Returns:
        Command to execute, or None if key should be ignored
    """
    symbol = event.symbol
    inv = event.has_shift

    # Helper to get slice algorithm (for future slice support)
    def _slice_alg(alg):
        # For now, just return the algorithm
        # Future: handle slice ranges from app state
        return alg

    match symbol:
        # ===== QUIT =====
        case key.Q:
            return QuitCommand()

        # ===== ANIMATION CONTROL =====
        case key.SPACE:
            if event.has_ctrl:
                return ToggleSingleStepModeCommand()
            else:
                return UnpauseSingleStepCommand()

        case key.S:
            if animation_running:
                return AbortCommand()
            # During normal mode, S doesn't do anything
            return None

        case key.NUM_ADD:
            return AdjustAnimationSpeedCommand(increase=True)

        case key.NUM_SUBTRACT:
            return AdjustAnimationSpeedCommand(increase=False)

        # ===== TOGGLES =====
        case key.O:
            if event.has_ctrl:
                return ToggleSolverDebugCommand()
            elif event.has_alt:
                return ToggleSanityCheckCommand()
            else:
                return ToggleAnimationCommand()

        # ===== CUBE SIZE =====
        case key.EQUAL | key.PLUS:
            return ChangeCubeSizeCommand(delta=+1)

        case key.MINUS:
            return ChangeCubeSizeCommand(delta=-1)

        # ===== FACE ROTATIONS =====
        case key.R:
            if event.has_ctrl:
                return RotateFaceCommand(Algs.Rw, inv)
            else:
                return RotateFaceCommand(_slice_alg(Algs.R), inv)

        case key.L:
            if event.has_ctrl:
                return RotateFaceCommand(Algs.Lw, inv)
            else:
                return RotateFaceCommand(_slice_alg(Algs.L), inv)

        case key.U:
            if event.has_ctrl:
                return RotateFaceCommand(Algs.Uw, inv)
            else:
                return RotateFaceCommand(_slice_alg(Algs.U), inv)

        case key.D:
            if event.has_ctrl:
                return RotateFaceCommand(Algs.Dw, inv)
            else:
                return RotateFaceCommand(_slice_alg(Algs.D), inv)

        case key.F:
            if event.has_ctrl:
                return RotateFaceCommand(Algs.Fw, inv)
            else:
                return RotateFaceCommand(_slice_alg(Algs.F), inv)

        case key.B:
            if event.has_ctrl:
                return RotateFaceCommand(Algs.Bw, inv)
            else:
                return RotateFaceCommand(_slice_alg(Algs.B), inv)

        # ===== SLICES =====
        case key.M:
            return RotateFaceCommand(_slice_alg(Algs.M), inv)

        case key.E:
            return RotateFaceCommand(_slice_alg(Algs.E), inv)

        # S conflicts with abort during animation
        # Handle S for slice only when not animating

        # ===== WHOLE CUBE ROTATIONS =====
        case key.X:
            if event.has_ctrl:
                # Ctrl+X = view rotation (negative)
                from cube.app.app_state import ApplicationAndViewState
                return AdjustViewAngleCommand('x', -ApplicationAndViewState.ALPHA_DELTA)
            elif event.has_alt:
                # Alt+X = view rotation (positive)
                from cube.app.app_state import ApplicationAndViewState
                return AdjustViewAngleCommand('x', ApplicationAndViewState.ALPHA_DELTA)
            else:
                # X = cube rotation
                return RotateFaceCommand(Algs.X, inv)

        case key.Y:
            if event.has_ctrl:
                from cube.app.app_state import ApplicationAndViewState
                return AdjustViewAngleCommand('y', -ApplicationAndViewState.ALPHA_DELTA)
            elif event.has_alt:
                from cube.app.app_state import ApplicationAndViewState
                return AdjustViewAngleCommand('y', ApplicationAndViewState.ALPHA_DELTA)
            else:
                return RotateFaceCommand(Algs.Y, inv)

        case key.Z:
            if event.has_ctrl:
                from cube.app.app_state import ApplicationAndViewState
                return AdjustViewAngleCommand('z', -ApplicationAndViewState.ALPHA_DELTA)
            elif event.has_alt:
                from cube.app.app_state import ApplicationAndViewState
                return AdjustViewAngleCommand('z', ApplicationAndViewState.ALPHA_DELTA)
            else:
                return RotateFaceCommand(Algs.Z, inv)

        # ===== VIEW CONTROL =====
        case key.UP:
            if event.has_ctrl:
                # Zoom in
                return ZoomCommand(zoom_in=True)
            elif event.has_alt:
                # Pan up
                from cube.app.app_state import ApplicationAndViewState
                return PanCommand('y', ApplicationAndViewState.OFFSET_DELTA)
            else:
                # Pan up (no modifier)
                from cube.app.app_state import ApplicationAndViewState
                return PanCommand('y', ApplicationAndViewState.OFFSET_DELTA)

        case key.DOWN:
            if event.has_ctrl:
                # Zoom out
                return ZoomCommand(zoom_in=False)
            elif event.has_alt:
                # Pan down
                from cube.app.app_state import ApplicationAndViewState
                return PanCommand('y', -ApplicationAndViewState.OFFSET_DELTA)
            else:
                # Pan down (no modifier)
                from cube.app.app_state import ApplicationAndViewState
                return PanCommand('y', -ApplicationAndViewState.OFFSET_DELTA)

        case key.LEFT:
            from cube.app.app_state import ApplicationAndViewState
            return PanCommand('x', -ApplicationAndViewState.OFFSET_DELTA)

        case key.RIGHT:
            from cube.app.app_state import ApplicationAndViewState
            return PanCommand('x', ApplicationAndViewState.OFFSET_DELTA)

        # ===== RESET =====
        case key.C:
            if event.has_ctrl:
                # Reset cube and view
                return ResetCubeCommand(reset_view=True)
            elif event.has_alt:
                # Reset view only
                return ResetViewCommand()
            else:
                # Reset cube only
                return ResetCubeCommand(reset_view=False)

        # ===== UNDO =====
        case key.COMMA:
            return UndoCommand()

        # ===== SCRAMBLE =====
        case key._0 | key._1 | key._2 | key._3 | key._4 | key._5 | key._6 | key._7 | key._8 | key._9:
            # Get numeric value (0-9)
            seed = symbol - key._0
            # Only animate scramble for key 0
            animate = (seed == 0)
            return ScrambleCommand(seed=seed, animation=animate)

        # ===== SOLVE =====
        case key.SLASH | key.QUESTION:
            # Force no animation if Shift pressed
            animation = not event.has_shift
            return SolveCommand(animation=animation, step=SolveStep.ALL)

        case key.F1:
            animation = not event.has_shift
            if event.has_ctrl:
                # First layer cross only
                return SolveCommand(animation=animation, step=SolveStep.L1x)
            else:
                # Full first layer
                return SolveCommand(animation=animation, step=SolveStep.L1)

        case key.F2:
            animation = not event.has_shift
            return SolveCommand(animation=animation, step=SolveStep.L2)

        case key.F3:
            animation = not event.has_shift
            if event.has_ctrl:
                # Third layer cross only
                return SolveCommand(animation=animation, step=SolveStep.L3x)
            else:
                # Full third layer
                return SolveCommand(animation=animation, step=SolveStep.L3)

        case key.F4:
            animation = not event.has_shift
            return SolveCommand(animation=animation, step=SolveStep.NxNCenters)

        case key.F5:
            animation = not event.has_shift
            return SolveCommand(animation=animation, step=SolveStep.NxNEdges)

        # ===== RECORDING =====
        case key.P:
            if event.has_ctrl:
                # Toggle recording
                return ToggleRecordingCommand()
            elif event.has_alt:
                # Clear recording
                return ClearRecordingCommand()
            else:
                # Play recording (possibly reversed)
                return PlayRecordingCommand(inverted=event.has_shift)

    # No command for this key
    return None
