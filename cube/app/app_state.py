import math
from collections.abc import Sequence
from contextlib import contextmanager
from typing import Literal

from pyglet import gl  # type: ignore

# noinspection PyMethodMayBeStatic
from cube import algs
from cube import config
from cube.animation.main_g_animation_text import AnimationText
from cube.model.cube import Cube
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

    def __init__(self) -> None:
        super().__init__()
        # self._animation_speed_delay_between_steps: float = 1/40
        # self._animation_speed_number_of_steps = 30

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

        self.slice_start: int = 1
        self.slice_stop: int = 3

        self.single_step_mode = False
        self.single_step_mode_stop_pressed = False
        self.paused_on_single_step_mode: algs.Alg | None = None

        self._animation_text = AnimationText()

        self.last_recording: Sequence[algs.Alg] | None = None

        #bool() false indicate next window:on_draw to skip on_draw
        self.skip_next_on_draw = False

    def reset(self, not_view=False):
        self._alpha_x: float = 0
        self._alpha_y: float = 0
        self._alpha_z: float = 0
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

    def prepare_objects_view(self):
        """
        leave matrix mode GL_MODELVIEW
        :return:
        """
        gl.glPushAttrib(gl.GL_MATRIX_MODE)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()

        o = self._offset

        gl.glTranslatef(o[0], o[1], o[2])

        # why rotate (a1 + a2)  is not rotate a1 then rotate a2
        gl.glRotatef(math.degrees(self.alpha_x_0), 1, 0, 0)
        gl.glRotatef(math.degrees(self.alpha_y_0), 0, 1, 0)
        gl.glRotatef(math.degrees(self.alpha_z_0), 0, 0, 1)
        gl.glRotatef(math.degrees(self.alpha_x), 1, 0, 0)
        gl.glRotatef(math.degrees(self.alpha_y), 0, 1, 0)
        gl.glRotatef(math.degrees(self.alpha_z), 0, 0, 1)

    # noinspection PyMethodMayBeStatic
    def restore_objects_view(self):
        """
        Undo prepare_objects_view
        :return:
        """
        # Pop Matrix off stack
        gl.glPopMatrix()
        gl.glPopAttrib()

    def set_projection(self, width: int, height: int):
        gl.glPushAttrib(gl.GL_MATRIX_MODE)
        # using Projection mode
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

        aspect_ratio = width / height
        # gluPerspective( GLdouble ( fovy ) , GLdouble ( aspect ) , GLdouble ( zNear ) , GLdouble ( zFar ) )-> void
        gl.gluPerspective(self._fov_y, aspect_ratio, 1, 1000)

        # gl.glMatrixMode(gl.GL_MODELVIEW)
        # gl.glLoadIdentity()
        # gl.glTranslatef(0, 0, -400)

        gl.glPopAttrib()

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
