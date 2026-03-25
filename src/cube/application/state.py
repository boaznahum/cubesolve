import pickle
import tempfile
from collections.abc import Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Literal, Tuple

from cube.application.animation.AnimationText import AnimationText
import logging

from cube.application.Logger import CubeLogger, setup_root_logger
from cube.utils.std_logging import DEBUG_ALL_ONLY

# noinspection PyMethodMayBeStatic
from cube.domain import algs
from cube.domain.model.Cube import Cube
from cube.domain.model.FaceName import FaceName
from cube.utils.config_protocol import ConfigProtocol


class _AnimationSpeed:
    """Animation speed computed from config, storing total duration in seconds.

    Uses same exponential formula as WebGL: duration = d0 * (dn/d0)^(i/7).
    Animation progress is time-based (elapsed/duration) with cubic ease-in-out.
    """

    def __init__(self, duration_s: float) -> None:
        super().__init__()
        self._duration_s: float = duration_s

    @property
    def duration_s(self) -> float:
        """Total animation duration in seconds for a 90-degree rotation."""
        return self._duration_s

    @property
    def delay_between_steps(self) -> float:
        """Fixed frame interval (~60 FPS) for event loop scheduling."""
        return 1.0 / 60.0

    def get_speed(self) -> str:
        """Return speed as degrees per second string."""
        if self._duration_s > 0:
            return str(round(90 / self._duration_s)) + " Deg/S"
        return "Instant"

    @staticmethod
    def from_config(d0: float, dn: float, index: float) -> '_AnimationSpeed':
        """Compute animation duration from AnimationSpeedConfig parameters.

        Uses same exponential formula as WebGL: duration = d0 * (dn/d0)^(i/7)
        """
        duration_s = (d0 * (dn / d0) ** (index / 7.0)) / 1000.0
        return _AnimationSpeed(duration_s)


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

        # Root cube logger — all solver loggers are children of this.
        self._logger: CubeLogger = setup_root_logger(debug_all=debug_all, quiet_all=quiet_all)
        self._speed: float = config.animation_speed_config.default_index

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

        # Full mode - hides toolbar and status text
        self.full_mode: bool = config.full_mode

    @property
    def config(self) -> ConfigProtocol:
        """Access the configuration."""
        return self._config

    def reset(self) -> None:
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
    def get_speed_index(self) -> float:
        return self._speed

    def inc_speed(self):
        step = self._config.animation_speed_config.step
        self._speed = min(7.0, self._speed + step)

    def dec_speed(self):
        step = self._config.animation_speed_config.step
        self._speed = max(0.0, self._speed - step)

    @property
    def get_speed(self) -> _AnimationSpeed:
        sc = self._config.animation_speed_config
        return _AnimationSpeed.from_config(sc.d0, sc.dn, self._speed)

    def get_draw_shadows_mode(self, face: FaceName) -> bool:

        """

        :return: string that might contains "L", "D", "B"
        """
        return str(face.value).upper() in self._draw_shadows

    def toggle_shadows_mode(self, face: Literal[FaceName.D, FaceName.B, FaceName.L]):
        self._change_shadows_mode(face, not self.get_draw_shadows_mode(face))

    def toggle_all_shadows_mode(self) -> None:
        """Toggle all face shadows on/off."""
        # If any shadow is on, turn all off; otherwise turn all on
        if self.any_shadow_on:
            self._draw_shadows = ""
        else:
            self._draw_shadows = "LDB"

    @property
    def any_shadow_on(self) -> bool:
        """Check if any face shadow is enabled."""
        return bool(self._draw_shadows)

    def _change_shadows_mode(self, face: Literal[FaceName.D, FaceName.B, FaceName.L], add: bool):

        s = str(face.value)

        s = s.upper()

        if add:
            if s not in self._draw_shadows:
                self._draw_shadows += s
        else:
            self._draw_shadows = self._draw_shadows.replace(s.upper(), "")

    def slice_alg(self, cube: Cube, r: algs.SliceAbleAlg) -> algs.Alg:

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

        sliced = r[start:stop]
        return sliced

    @contextmanager
    def w_animation_speed(self, animation_speed: float):

        assert 0 <= animation_speed <= 7
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
    def logger(self) -> CubeLogger:
        """Return the root cube logger."""
        return self._logger

    @property
    def is_debug_all(self) -> bool:
        """Return True if debug_all mode is enabled."""
        return self._logger.debug_all

    @property
    def quiet_all(self) -> bool:
        """Return True if quiet_all mode is enabled (suppresses all debug output)."""
        return self._logger.quiet_all

    @quiet_all.setter
    def quiet_all(self, value: bool) -> None:
        """Set quiet_all mode."""
        self._logger.quiet_all = value

    def is_debug(self, debug_on: bool = False) -> bool:
        """Check if debug output should happen.

        Args:
            debug_on: If True, checks at DEBUG level.
                      If False, checks at DEBUG_ALL_ONLY level.
        """
        if debug_on:
            return self._logger.isEnabledFor(logging.DEBUG)
        else:
            return self._logger.isEnabledFor(DEBUG_ALL_ONLY)

    def debug(self, debug_on: bool, *args: Any) -> None:
        """Print debug information if allowed by flags.

        Args:
            debug_on: True → log at DEBUG (normal debug).
                      False → log at DEBUG_ALL_ONLY (only with --debug-all).
        """
        level = logging.DEBUG if debug_on else DEBUG_ALL_ONLY
        if not self._logger.isEnabledFor(level):
            return
        resolved = [a() if callable(a) else a for a in args]
        message = " ".join(str(a) for a in resolved)
        self._logger.log(level, message)

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

        pass

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

