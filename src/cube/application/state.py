import pickle
import tempfile
from collections.abc import Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Literal, Tuple

from cube.application.animation.AnimationText import AnimationText

# noinspection PyMethodMayBeStatic
from cube.domain import algs
from cube.domain.model.Cube import Cube
from cube.domain.model.cube_boy import FaceName
from cube.utils.config_protocol import ConfigProtocol


class _AnimationSpeed:
    """

    """

    def __init__(self, delay_between_steps: float, number_of_steps_in_90_degree: int) -> None:
        super().__init__()
        self._delay_between_steps: float = delay_between_steps  # 1 / 25  # 1/50
        self._number_of_steps = number_of_steps_in_90_degree

    @property
    def number_of_steps(self):
        """
        Number of steps in 90 degree
        Speed is 90 / animation_speed_number_of_steps / animation_speed_delay_between_steps
        :return:
        """
        return self._number_of_steps

    @property
    def delay_between_steps(self) -> float:
        """

        :return: delay (seconds) between steps
        """
        return self._delay_between_steps

    def get_speed(self) -> str:
        """

        :return:  Degree/S "Deg/S"
        """
        return str(90 / self._number_of_steps / self._delay_between_steps) + " Deg/S"


speeds = [
    # delay in seconds, number of steps
    _AnimationSpeed(1 / 10, 20),
    _AnimationSpeed(1 / 20, 20),
    _AnimationSpeed(1 / 40, 20),  # default
    _AnimationSpeed(1 / 40, 10),
    _AnimationSpeed(1 / 60, 10),
    _AnimationSpeed(1 / 100, 10),
    _AnimationSpeed(1 / 100, 5),
    _AnimationSpeed(1 / 100, 3)  # 3000 d/s
]


class ApplicationAndViewState:
    # __slots__ = [
    #     "_alpha_x_0",
    #     "_alpha_y_0",
    #     "_alpha_z_0",
    #     "_alpha_x",
    #     "_alpha_y",
    #     "_alpha_z",
    #     "_alpha_delta",
    # ]

    def __init__(self, config: ConfigProtocol, debug_all: bool = False, quiet_all: bool = False) -> None:
        super().__init__()
        # Store config reference for access throughout the class
        self._config = config

        self._debug_all = debug_all
        self._quiet_all = quiet_all
        self._speed = 3

        # self._alpha_x_0: float = 0.3
        # self._alpha_y_0: float = -0.4
        # self._alpha_z_0: float = 0

        self._alpha_x_0: float = 0.45707963267948953
        self._alpha_y_0: float = -0.6792526803190928
        self._alpha_z_0: float = 0

        self._alpha_x: float = 0
        self._alpha_y: float = 0
        self._alpha_z: float = 0
        self._alpha_delta = 0.1

        self._fov_y_0 = 35
        self._fov_y = self._fov_y_0

        self._offset_0 = [0, 0, -400]
        # must copy, we modify it
        self._offset = [*self._offset_0]

        self._draw_shadows = config.viewer_draw_shadows
        self.cube_size = config.cube_size

        self.slice_start: int = 0
        self.slice_stop: int = 0

        self.single_step_mode = False
        self.single_step_mode_stop_pressed = False
        self.paused_on_single_step_mode: algs.Alg | None = None

        self._animation_text = AnimationText()

        self.last_recording: Sequence[algs.Alg] | None = None

        #bool() false indicate next window:on_draw to skip on_draw
        self.skip_next_on_draw = False

        self._last_scramble_key_size: Tuple[Any, int | None] | None = None

        # Celebration effect settings (from config)
        self._celebration_effect: str = config.celebration_effect
        self._celebration_enabled: bool = config.celebration_enabled
        self._celebration_duration: float = config.celebration_duration

        # Lighting settings (pyglet2 backend only)
        self._brightness: float = config.lighting_brightness
        self._background_gray: float = config.lighting_background

    @property
    def config(self) -> ConfigProtocol:
        """Access the configuration."""
        return self._config

    def reset(self, not_view=False) -> None:
        self._alpha_x = 0
        self._alpha_y = 0
        self._alpha_z = 0
        self._fov_y = self._fov_y_0
        # must copy, we modify it
        self._offset[:] = self._offset_0

    @property
    def alpha_x_0(self):
        return self._alpha_x_0

    @property
    def alpha_y_0(self):
        return self._alpha_y_0

    @property
    def alpha_z_0(self):
        return self._alpha_z_0

    @property
    def alpha_x(self):
        return self._alpha_x

    @alpha_x.setter
    def alpha_x(self, value):
        self._alpha_x = value

    @property
    def alpha_y(self):
        return self._alpha_y

    @alpha_y.setter
    def alpha_y(self, value):
        self._alpha_y = value

    @property
    def alpha_z(self):
        return self._alpha_z

    @alpha_z.setter
    def alpha_z(self, value):
        self._alpha_z = value

    @property
    def alpha_delta(self):
        return self._alpha_delta

    @property
    def fov_y(self) -> float:
        """Get current field of view Y angle."""
        return self._fov_y

    def inc_fov_y(self):
        self._fov_y += 1

    def dec_fov_y(self):
        self._fov_y -= 1

    def change_fov_y(self, delta: int):
        self._fov_y += delta

    def change_offset(self, dx, dy, dz):
        o = self._offset

        o[0] += dx
        o[1] += dy
        o[2] += dz

    @property
    def offset(self) -> Sequence[int]:
        return self._offset

    @property
    def brightness(self) -> float:
        """Get current brightness level (0.1-1.5)."""
        return self._brightness

    @brightness.setter
    def brightness(self, value: float) -> None:
        """Set brightness level (clamped to 0.1-1.5)."""
        self._brightness = max(0.1, min(1.5, value))

    @property
    def background_gray(self) -> float:
        """Get current background gray level (0.0-0.5)."""
        return self._background_gray

    @background_gray.setter
    def background_gray(self, value: float) -> None:
        """Set background gray level (clamped to 0.0-0.5)."""
        self._background_gray = max(0.0, min(0.5, value))

    @property
    def get_speed_index(self):
        return self._speed

    def inc_speed(self):
        self._speed = min(len(speeds) - 1, self._speed + 1)

    def dec_speed(self):
        self._speed = max(0, self._speed - 1)

    @property
    def get_speed(self) -> _AnimationSpeed:
        return speeds[self._speed]

    def get_draw_shadows_mode(self, face: FaceName) -> bool:

        """

        :return: string that might contains "L", "D", "B"
        """
        return str(face.value).upper() in self._draw_shadows

    def toggle_shadows_mode(self, face: Literal[FaceName.D, FaceName.B, FaceName.L]):
        self._change_shadows_mode(face, not self.get_draw_shadows_mode(face))

    def _change_shadows_mode(self, face: Literal[FaceName.D, FaceName.B, FaceName.L], add: bool):

        s = str(face.value)

        s = s.upper()

        if add:
            if s not in self._draw_shadows:
                self._draw_shadows += s
        else:
            self._draw_shadows = self._draw_shadows.replace(s.upper(), "")

    def slice_alg(self, cube: Cube, r: algs.SliceAbleAlg):

        mx: int

        if isinstance(r, algs.FaceAlg):
            mx = cube.n_slices + 1  # face + slices
        else:
            mx = cube.n_slices

        start = self.slice_start
        stop = self.slice_stop

        if not (start or stop):
            return r

        if start < 1:
            start = 1
        if stop > mx:
            stop = mx

        r = r[start:stop]
        return r

    @contextmanager
    def w_animation_speed(self, animation_speed: int):

        assert animation_speed in range(len(speeds))
        saved = self._speed
        self._speed = animation_speed

        try:
            yield None
        finally:
            self._speed = saved

    @property
    def animation_text(self) -> AnimationText:
        return self._animation_text


    def _get_root_path(self) -> Path:

        t = Path(tempfile.gettempdir())

        return t / "cube"


    def _get_last_test_path(self):
        p = self._get_root_path()
        return p / self._config.last_scramble_path

    def set_last_scramble_test(self, scramble_key: Any, scramble_size: int | None):

        file_path = self._get_last_test_path()

        file_path.parent.mkdir(parents=True, exist_ok=True)

        #print(file_path.absolute())

        data = (scramble_key, scramble_size)
        with open(file_path, 'wb') as file:



            pickle.dump(data, file)

            #print(f"{data} Data was written to {file_path}")

        self._last_scramble_key_size = data

    def get_last_scramble_test(self) -> Tuple[Any, int | None]:

        if self._last_scramble_key_size is not None:
            return self._last_scramble_key_size

        file_path = self._get_last_test_path()

        try:
            with open(file_path, 'rb') as file:
                # Step 3
                (scramble_key, scramble_size) = pickle.load(file)

            self._last_scramble_key_size = (scramble_key, scramble_size)
        except IOError:
            self._last_scramble_key_size = (None, None)

        return self._last_scramble_key_size

    @property
    def is_debug_all(self) -> bool:
        """Return True if debug_all mode is enabled."""
        return self._debug_all

    @property
    def quiet_all(self) -> bool:
        """Return True if quiet_all mode is enabled (suppresses all debug output)."""
        return self._quiet_all

    @quiet_all.setter
    def quiet_all(self, value: bool) -> None:
        """Set quiet_all mode."""
        self._quiet_all = value

    def is_debug(self, debug_on: bool = False) -> bool:
        """Check if debug output should happen.

        Args:
            debug_on: Local flag to enable debug for this specific call.

        Returns:
            True if debug output should happen:
            - quiet_all is False AND (debug_all is True OR debug_on is True)
        """
        if self._quiet_all:
            return False
        return self._debug_all or debug_on

    def debug_prefix(self) -> str:
        """Return the standard debug prefix."""
        return "DEBUG:"

    def debug(self, debug_on: bool, *args) -> None:
        """Print debug information if allowed by flags.

        Args:
            debug_on: Local flag to enable debug for this specific call.
            *args: Arguments to print, same as print() function.

        Logic:
            - If quiet_all is True → never print
            - If debug_all is True OR debug_on is True → print
        """
        if self._quiet_all:
            return
        if self._debug_all or debug_on:
            print("DEBUG:", *args, flush=True)

    def debug_lazy(self, debug_on: bool, func: Callable[[], Any]) -> None:
        """Print debug information with lazy evaluation.

        The func is only called if we're actually going to print,
        avoiding expensive computation when debug is disabled.

        Args:
            debug_on: Local flag to enable debug for this specific call.
            func: Callable that returns the message to print.

        Logic:
            - If quiet_all is True → never print, func not called
            - If debug_all is True OR debug_on is True → call func and print
        """
        if self._quiet_all:
            return
        if self._debug_all or debug_on:
            print("DEBUG:", func())

    def debug_dump(
        self,
        cube: Cube,
        label: str = "Application State",
        opengl_info: str | None = None,
        backend_name: str | None = None,
    ) -> None:
        """Unified dump of OpenGL info, application state, config, and cube state.

        Debug levels:
        - Backend/OpenGL info: always printed (if provided, unless quiet)
        - State/config values: debug(True) - shows in normal debug mode
        - Cube slices/details: debug(False) - only shows with --debug-all

        Args:
            cube: The cube to dump state for.
            label: A label to identify this dump in the output.
            opengl_info: Optional OpenGL version string to include.
            backend_name: Optional backend name (e.g., "pyglet2", "tkinter").
        """

        return

        # Backend and OpenGL info - always print if provided (unless quiet)
        if (backend_name or opengl_info) and not self._quiet_all:
            print("=" * 60)
            if backend_name:
                print(f"Backend: {backend_name}")
            if opengl_info:
                print("OpenGL Information:")
                print(opengl_info)
            print("=" * 60)

        # State and config - debug(True) = shows without --debug-all
        self.debug(True, "=" * 60)
        self.debug(True, f"DUMP: {label}")
        self.debug(True, "=" * 60)

        # View state
        self.debug(True, "View State:")
        self.debug(True, f"  Initial rotation: alpha_x_0={self._alpha_x_0:.4f}, "
                   f"alpha_y_0={self._alpha_y_0:.4f}, alpha_z_0={self._alpha_z_0:.4f}")
        self.debug(True, f"  User rotation:    alpha_x={self._alpha_x:.4f}, "
                   f"alpha_y={self._alpha_y:.4f}, alpha_z={self._alpha_z:.4f}")
        self.debug(True, f"  Alpha delta: {self._alpha_delta}")
        self.debug(True, f"  FOV: {self._fov_y} (initial: {self._fov_y_0})")
        self.debug(True, f"  Offset: {self._offset} (initial: {self._offset_0})")

        # Config values
        self.debug(True, "Config:")
        self.debug(True, f"  Cube size: {self.cube_size}")
        self.debug(True, f"  Slice range: [{self.slice_start}, {self.slice_stop}]")
        self.debug(True, f"  Shadow faces: '{self._draw_shadows}'")
        self.debug(True, f"  Speed index: {self._speed} ({self.get_speed.get_speed()})")
        self.debug(True, f"  Single step mode: {self.single_step_mode}")
        self.debug(True, f"  Debug all: {self._debug_all}, Quiet all: {self._quiet_all}")

        # Cube summary - debug(True)
        self.debug(True, "Cube:")
        self.debug(True, f"  Size: {cube.size}, Solved: {cube.solved}, "
                   f"ModCounter: {cube._modify_counter}")

        # Recording
        if self.last_recording:
            self.debug(True, f"  Last recording: {len(self.last_recording)} moves")

        self.debug(True, "-" * 60)

        # Cube slices detail - debug(False) = only with --debug-all
        # Early return if not debug_all to avoid expensive computation
        if not self._debug_all:
            self.debug(True, "(Use --debug-all for verbose cube slice details)")
            self.debug(True, "=" * 60)
            self.debug(True, f"END DUMP: {label}")
            self.debug(True, "=" * 60)
            return

        state = cube.cqr.get_sate()
        self.debug(False, f"State entries: {len(state)}")
        self.debug(False, "-" * 60)
        self.debug(False, "SLICES (verbose):")

        all_slices = cube.get_all_parts()
        for s in sorted(all_slices, key=lambda p: str(p.fixed_id)):
            # _colors_id_by_colors is initialized in PartSlice.__init__
            colors_cache = s._colors_id_by_colors
            match_faces = s.match_faces
            edges_str = ", ".join(f"{e.face.name.value}:{e.color.name}" for e in s.edges)

            self.debug(False, f"  Slice: {s.fixed_id}")
            self.debug(False, f"    index: {s._index}")
            self.debug(False, f"    edges: [{edges_str}]")
            self.debug(False, f"    colors: {s.colors}")
            self.debug(False, f"    colors_id: {s.colors_id} (cache_was={colors_cache})")
            self.debug(False, f"    match_faces: {match_faces}")

        # Full state dictionary - debug(False)
        self.debug(False, "-" * 60)
        self.debug(False, "FULL STATE DICT:")
        for fixed_id, colors in sorted(state.items(), key=lambda x: str(x[0])):
            self.debug(False, f"  {fixed_id} -> {colors}")

        self.debug(True, "=" * 60)
        self.debug(True, f"END DUMP: {label}")
        self.debug(True, "=" * 60)

    # Celebration effect properties
    @property
    def celebration_effect(self) -> str:
        """Get the current celebration effect name."""
        return self._celebration_effect

    @celebration_effect.setter
    def celebration_effect(self, value: str) -> None:
        """Set the celebration effect name."""
        self._celebration_effect = value

    @property
    def celebration_enabled(self) -> bool:
        """Check if celebration effects are enabled."""
        return self._celebration_enabled

    @celebration_enabled.setter
    def celebration_enabled(self, value: bool) -> None:
        """Enable or disable celebration effects."""
        self._celebration_enabled = value

    @property
    def celebration_duration(self) -> float:
        """Get the celebration effect duration in seconds."""
        return self._celebration_duration

    @celebration_duration.setter
    def celebration_duration(self, value: float) -> None:
        """Set the celebration effect duration in seconds."""
        self._celebration_duration = value

