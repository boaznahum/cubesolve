import math
import pickle
import tempfile
from collections.abc import Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Literal, Any, Tuple, TYPE_CHECKING, Callable

# noinspection PyMethodMayBeStatic
from cube import algs
from cube import config

if TYPE_CHECKING:
    from cube.gui.protocols.Renderer import Renderer
from cube.animation.AnimationText import AnimationText
from cube.model.Cube import Cube
from cube.model.cube_boy import FaceName


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

    def __init__(self, debug_all: bool = False, quiet_all: bool = False) -> None:
        super().__init__()
        # self._animation_speed_delay_between_steps: float = 1/40
        # self._animation_speed_number_of_steps = 30

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

        self._draw_shadows = config.VIEWER_DRAW_SHADOWS
        self.cube_size = config.CUBE_SIZE

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

    def prepare_objects_view(self, renderer: "Renderer") -> None:
        """Set up the model-view transformation for drawing objects.

        Applies offset translation and rotations based on view state.
        Call restore_objects_view() when done drawing.

        Args:
            renderer: Renderer to use for view transformations
        """
        view = renderer.view

        view.push_matrix()
        view.load_identity()

        o = self._offset
        view.translate(float(o[0]), float(o[1]), float(o[2]))

        # Apply initial rotation (base orientation)
        view.rotate(math.degrees(self.alpha_x_0), 1, 0, 0)
        view.rotate(math.degrees(self.alpha_y_0), 0, 1, 0)
        view.rotate(math.degrees(self.alpha_z_0), 0, 0, 1)

        # Apply user-controlled rotation (from mouse drag)
        view.rotate(math.degrees(self.alpha_x), 1, 0, 0)
        view.rotate(math.degrees(self.alpha_y), 0, 1, 0)
        view.rotate(math.degrees(self.alpha_z), 0, 0, 1)

    def restore_objects_view(self, renderer: "Renderer") -> None:
        """Undo prepare_objects_view - restore previous matrix state.

        Args:
            renderer: Renderer to use for view transformations
        """
        renderer.view.pop_matrix()

    def set_projection(self, width: int, height: int, renderer: "Renderer") -> None:
        """Set up the projection matrix for the viewport.

        Args:
            width: Viewport width in pixels
            height: Viewport height in pixels
            renderer: Renderer to use for view transformations
        """
        renderer.view.set_projection(
            width, height,
            fov_y=float(self._fov_y),
            near=1.0,
            far=1000.0
        )

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
        return p / config.LAST_SCRAMBLE_PATH

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
            print("DEBUG:", *args)

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

    def debug_dump_cube_state(self, cube: Cube, label: str = "Cube State") -> None:
        """Dump detailed cube state using the debug infrastructure.

        Includes: size, solved status, modify counter, all slices with their
        colors, colors_id, cache state, match status.

        Args:
            cube: The cube to dump state for.
            label: A label to identify this dump in the output.
        """
        if not self._debug_all:
            return

        self.debug(False, "=" * 70)
        self.debug(False, f"DUMP: {label}")
        self.debug(False, "=" * 70)
        self.debug(False, f"Size: {cube.size}, Solved: {cube.solved}, ModCounter: {cube._modify_counter}")

        # Get full state
        state = cube.cqr.get_sate()
        self.debug(False, f"State entries: {len(state)}")

        # Dump all slices with detailed state
        # Note: get_all_parts() returns PartSlice objects (slices), not Part objects
        self.debug(False, "-" * 70)
        self.debug(False, "SLICES:")
        self.debug(False, "-" * 70)

        all_slices = cube.get_all_parts()
        for s in sorted(all_slices, key=lambda p: str(p.fixed_id)):
            # Check cache state BEFORE accessing (to see if it was initialized)
            colors_cache = getattr(s, '_colors_id_by_colors', None)

            # Get match status
            match_faces = s.match_faces

            # Build edges string
            edges_str = ", ".join(f"{e.face.name.value}:{e.color.name}" for e in s.edges)

            self.debug(False, f"  Slice: {s.fixed_id}")
            self.debug(False, f"    index: {s._index}")
            self.debug(False, f"    edges: [{edges_str}]")
            self.debug(False, f"    colors: {s.colors}")
            self.debug(False, f"    colors_id: {s.colors_id} (cache_was={colors_cache})")
            self.debug(False, f"    match_faces: {match_faces}")

        # Dump full state dictionary
        self.debug(False, "-" * 70)
        self.debug(False, "FULL STATE DICT:")
        self.debug(False, "-" * 70)
        for fixed_id, colors in sorted(state.items(), key=lambda x: str(x[0])):
            self.debug(False, f"  {fixed_id} -> {colors}")

        self.debug(False, "=" * 70)
        self.debug(False, f"END DUMP: {label}")
        self.debug(False, "=" * 70)

