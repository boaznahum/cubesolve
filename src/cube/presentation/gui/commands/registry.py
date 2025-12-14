"""
Commands registry - central access point for all command instances.

Provides convenient access to commands like Commands.ROTATE_R
while maintaining type safety.
"""
from cube.domain.algs.Algs import Algs
from cube.domain.model.cube_boy import FaceName
from cube.domain.solver import SolveStep

from .base import Command
from .concrete import (
    # Rotation
    RotateCommand,
    RotateWideCommand,
    CubeRotateCommand,
    # Scramble
    ScrambleCommand,
    ScrambleF9Command,
    # Solve
    SolveStepCommand,
    SolveAllCommand,
    SolveAllNoAnimationCommand,
    SolveEdgesCommand,
    # View
    ViewRotateCommand,
    PanCommand,
    ZoomInCommand,
    ZoomOutCommand,
    ViewResetCommand,
    # Animation
    SpeedUpCommand,
    SpeedDownCommand,
    PauseToggleCommand,
    SingleStepToggleCommand,
    StopAnimationCommand,
    ToggleAnimationCommand,
    # Lighting
    BrightnessUpCommand,
    BrightnessDownCommand,
    BackgroundUpCommand,
    BackgroundDownCommand,
    TextureSetCycleCommand,
    # Shadow
    ShadowToggleCommand,
    # Size
    SizeIncCommand,
    SizeDecCommand,
    # Slice
    SliceStartIncCommand,
    SliceStartDecCommand,
    SliceStopIncCommand,
    SliceStopDecCommand,
    SliceResetCommand,
    # Recording
    RecordingPlayCommand,
    RecordingToggleCommand,
    RecordingClearCommand,
    # Debug
    ToggleDebugCommand,
    ToggleSanityCheckCommand,
    DebugInfoCommand,
    # Testing
    TestRunCommand,
    TestRunLastCommand,
    TestScrambleLastCommand,
    # Application
    QuitCommand,
    ResetCubeCommand,
    ResetCubeAndViewCommand,
    UndoCommand,
    SwitchSolverCommand,
    # Special
    AnnotateCommand,
    SpecialAlgCommand,
)


class Commands:
    """
    Central registry of all command instances.

    Provides convenient access to commands like Commands.ROTATE_R
    while maintaining type safety.

    Commands are singleton-like - identical commands return the same instance.
    """

    # =========================================================================
    # FACE ROTATIONS
    # =========================================================================
    ROTATE_R = RotateCommand(Algs.R, False)
    ROTATE_R_PRIME = RotateCommand(Algs.R, True)
    ROTATE_L = RotateCommand(Algs.L, False)
    ROTATE_L_PRIME = RotateCommand(Algs.L, True)
    ROTATE_U = RotateCommand(Algs.U, False)
    ROTATE_U_PRIME = RotateCommand(Algs.U, True)
    ROTATE_D = RotateCommand(Algs.D, False)
    ROTATE_D_PRIME = RotateCommand(Algs.D, True)
    ROTATE_F = RotateCommand(Algs.F, False)
    ROTATE_F_PRIME = RotateCommand(Algs.F, True)
    ROTATE_B = RotateCommand(Algs.B, False)
    ROTATE_B_PRIME = RotateCommand(Algs.B, True)

    # =========================================================================
    # WIDE ROTATIONS
    # =========================================================================
    ROTATE_RW = RotateWideCommand(Algs.Rw, False)
    ROTATE_RW_PRIME = RotateWideCommand(Algs.Rw, True)
    ROTATE_LW = RotateWideCommand(Algs.Lw, False)
    ROTATE_LW_PRIME = RotateWideCommand(Algs.Lw, True)
    ROTATE_UW = RotateWideCommand(Algs.Uw, False)
    ROTATE_UW_PRIME = RotateWideCommand(Algs.Uw, True)
    ROTATE_DW = RotateWideCommand(Algs.Dw, False)
    ROTATE_DW_PRIME = RotateWideCommand(Algs.Dw, True)
    ROTATE_FW = RotateWideCommand(Algs.Fw, False)
    ROTATE_FW_PRIME = RotateWideCommand(Algs.Fw, True)
    ROTATE_BW = RotateWideCommand(Algs.Bw, False)
    ROTATE_BW_PRIME = RotateWideCommand(Algs.Bw, True)

    # =========================================================================
    # SLICE MOVES
    # =========================================================================
    SLICE_M = RotateCommand(Algs.M, False)
    SLICE_M_PRIME = RotateCommand(Algs.M, True)
    SLICE_E = RotateCommand(Algs.E, False)
    SLICE_E_PRIME = RotateCommand(Algs.E, True)
    SLICE_S = RotateCommand(Algs.S, False)
    SLICE_S_PRIME = RotateCommand(Algs.S, True)

    # =========================================================================
    # CUBE ROTATIONS
    # =========================================================================
    CUBE_X = CubeRotateCommand(Algs.X, False)
    CUBE_X_PRIME = CubeRotateCommand(Algs.X, True)
    CUBE_Y = CubeRotateCommand(Algs.Y, False)
    CUBE_Y_PRIME = CubeRotateCommand(Algs.Y, True)
    CUBE_Z = CubeRotateCommand(Algs.Z, False)
    CUBE_Z_PRIME = CubeRotateCommand(Algs.Z, True)

    # =========================================================================
    # SCRAMBLES
    # =========================================================================
    SCRAMBLE_0 = ScrambleCommand(0)
    SCRAMBLE_1 = ScrambleCommand(1)
    SCRAMBLE_2 = ScrambleCommand(2)
    SCRAMBLE_3 = ScrambleCommand(3)
    SCRAMBLE_4 = ScrambleCommand(4)
    SCRAMBLE_5 = ScrambleCommand(5)
    SCRAMBLE_6 = ScrambleCommand(6)
    SCRAMBLE_7 = ScrambleCommand(7)
    SCRAMBLE_8 = ScrambleCommand(8)
    SCRAMBLE_9 = ScrambleCommand(9)
    SCRAMBLE_F9 = ScrambleF9Command()

    # =========================================================================
    # SOLVE COMMANDS
    # =========================================================================
    SOLVE_ALL = SolveAllCommand()
    SOLVE_ALL_NO_ANIMATION = SolveAllNoAnimationCommand()
    SOLVE_L1 = SolveStepCommand(SolveStep.L1)
    SOLVE_L1X = SolveStepCommand(SolveStep.L1x)
    SOLVE_L2 = SolveStepCommand(SolveStep.L2)
    SOLVE_L3 = SolveStepCommand(SolveStep.L3)
    SOLVE_L3X = SolveStepCommand(SolveStep.L3x)
    SOLVE_CENTERS = SolveStepCommand(SolveStep.NxNCenters)
    SOLVE_EDGES = SolveEdgesCommand()

    # =========================================================================
    # VIEW CONTROL
    # =========================================================================
    VIEW_ALPHA_X_DEC = ViewRotateCommand('x', -1)
    VIEW_ALPHA_X_INC = ViewRotateCommand('x', 1)
    VIEW_ALPHA_Y_DEC = ViewRotateCommand('y', -1)
    VIEW_ALPHA_Y_INC = ViewRotateCommand('y', 1)
    VIEW_ALPHA_Z_DEC = ViewRotateCommand('z', -1)
    VIEW_ALPHA_Z_INC = ViewRotateCommand('z', 1)
    PAN_UP = PanCommand(0, 1, 0)
    PAN_DOWN = PanCommand(0, -1, 0)
    PAN_LEFT = PanCommand(-1, 0, 0)
    PAN_RIGHT = PanCommand(1, 0, 0)
    ZOOM_IN = ZoomInCommand()
    ZOOM_OUT = ZoomOutCommand()
    VIEW_RESET = ViewResetCommand()

    # =========================================================================
    # ANIMATION CONTROL
    # =========================================================================
    SPEED_UP = SpeedUpCommand()
    SPEED_DOWN = SpeedDownCommand()
    PAUSE_TOGGLE = PauseToggleCommand()
    SINGLE_STEP_TOGGLE = SingleStepToggleCommand()
    STOP_ANIMATION = StopAnimationCommand()
    TOGGLE_ANIMATION = ToggleAnimationCommand()

    # =========================================================================
    # LIGHTING CONTROL (pyglet2 backend only)
    # =========================================================================
    BRIGHTNESS_UP = BrightnessUpCommand()
    BRIGHTNESS_DOWN = BrightnessDownCommand()
    BACKGROUND_UP = BackgroundUpCommand()
    BACKGROUND_DOWN = BackgroundDownCommand()

    # =========================================================================
    # TEXTURE SET CYCLING (pyglet2 backend only)
    # =========================================================================
    TEXTURE_SET_CYCLE = TextureSetCycleCommand()

    # =========================================================================
    # SHADOW TOGGLES
    # =========================================================================
    SHADOW_TOGGLE_L = ShadowToggleCommand(FaceName.L)
    SHADOW_TOGGLE_D = ShadowToggleCommand(FaceName.D)
    SHADOW_TOGGLE_B = ShadowToggleCommand(FaceName.B)

    # =========================================================================
    # CUBE SIZE
    # =========================================================================
    SIZE_INC = SizeIncCommand()
    SIZE_DEC = SizeDecCommand()

    # =========================================================================
    # SLICE SELECTION
    # =========================================================================
    SLICE_START_INC = SliceStartIncCommand()
    SLICE_START_DEC = SliceStartDecCommand()
    SLICE_STOP_INC = SliceStopIncCommand()
    SLICE_STOP_DEC = SliceStopDecCommand()
    SLICE_RESET = SliceResetCommand()

    # =========================================================================
    # RECORDING
    # =========================================================================
    RECORDING_PLAY = RecordingPlayCommand(False)
    RECORDING_PLAY_PRIME = RecordingPlayCommand(True)
    RECORDING_TOGGLE = RecordingToggleCommand()
    RECORDING_CLEAR = RecordingClearCommand()

    # =========================================================================
    # DEBUG/CONFIG
    # =========================================================================
    TOGGLE_DEBUG = ToggleDebugCommand()
    TOGGLE_SANITY_CHECK = ToggleSanityCheckCommand()
    DEBUG_INFO = DebugInfoCommand()

    # =========================================================================
    # TESTING
    # =========================================================================
    TEST_RUN = TestRunCommand()
    TEST_RUN_LAST = TestRunLastCommand()
    TEST_SCRAMBLE_LAST = TestScrambleLastCommand()

    # =========================================================================
    # APPLICATION
    # =========================================================================
    QUIT = QuitCommand()
    RESET_CUBE = ResetCubeCommand()
    RESET_CUBE_AND_VIEW = ResetCubeAndViewCommand()
    UNDO = UndoCommand()
    SWITCH_SOLVER = SwitchSolverCommand()

    # =========================================================================
    # SPECIAL
    # =========================================================================
    ANNOTATE = AnnotateCommand()
    SPECIAL_ALG = SpecialAlgCommand()

    @classmethod
    def get_by_name(cls, name: str) -> "Command":
        """Get a command by its name.

        Args:
            name: Command name (e.g., "ROTATE_R", "SCRAMBLE_1")

        Returns:
            The command instance

        Raises:
            KeyError: If no command with that name exists
        """
        try:
            return getattr(cls, name)
        except AttributeError:
            raise KeyError(f"Unknown command: {name}")

    @classmethod
    def list_names(cls) -> list[str]:
        """List all command names."""
        from .base import Command
        return [name for name in dir(cls)
                if not name.startswith('_') and isinstance(getattr(cls, name), Command)]
