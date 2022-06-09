import math
from contextlib import contextmanager

from pyglet.gl import *  # type: ignore

# noinspection PyMethodMayBeStatic
import algs.algs as algs
from model.cube import Cube


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

    _AnimationSpeed(1/40, 20),
    _AnimationSpeed(1/40, 10),
    _AnimationSpeed(1/60, 10),
    _AnimationSpeed(1/100, 10),
    _AnimationSpeed(1/100, 5),
    _AnimationSpeed(1/100, 3)  # 3000 d/s
]

class ViewState:
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
        self.tx = 0
        self.ty = 0
        self.tz = 0
        self._speed = 0
        self._alpha_x_0: float = 0.3
        self._alpha_y_0: float = -0.4
        self._alpha_z_0: float = 0

        self._alpha_x: float = 0
        self._alpha_y: float = 0
        self._alpha_z: float = 0
        self._alpha_delta = 0.1

        self._draw_shadows = ""  # "LDB"
        self.cube_size = 5

        self.slice_start: int = 0
        self.slice_stop: int = 0

    def reset(self):
        self._alpha_x: float = 0
        self._alpha_y: float = 0
        self._alpha_z: float = 0

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

    def prepare_objects_view(self):
        """
        leave matrix mode GL_MODELVIEW
        :return:
        """
        glPushAttrib(GL_MATRIX_MODE)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(0, 0, -400)

        # why rotate (a1 + a2)  is not rotate a1 then rotate a2
        glRotatef(math.degrees(self.alpha_x_0), 1, 0, 0)
        glRotatef(math.degrees(self.alpha_y_0), 0, 1, 0)
        glRotatef(math.degrees(self.alpha_z_0), 0, 0, 1)
        glRotatef(math.degrees(self.alpha_x), 1, 0, 0)
        glRotatef(math.degrees(self.alpha_y), 0, 1, 0)
        glRotatef(math.degrees(self.alpha_z), 0, 0, 1)

    def restore_objects_view(self):
        """
        Undo prepare_objects_view
        :return:
        """
        # Pop Matrix off stack
        glPopMatrix()
        glPopAttrib()


    @property
    def get_speed_index(self):
        return self._speed

    def inc_speed(self):
        self._speed = min(len(speeds) -1, self._speed + 1)

    def dec_speed(self):
        self._speed = max(0, self._speed - 1)


    @property
    def get_speed(self) -> _AnimationSpeed:
        return speeds[self._speed]

    @property
    def draw_shadows(self):
        return self._draw_shadows

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

        cube = cube

        if start < 1:
            start = 1
        if stop > mx:
            stop = mx

        r = r[start:stop]
        return r

    @contextmanager
    def w_animation_speed(self, animation_speed :int):

        assert animation_speed in range(len(speeds))
        saved = self._speed
        self._speed = animation_speed

        try:
            yield None
        finally:
            self._speed = saved

