import math

from pyglet.gl import *  # type: ignore


# noinspection PyMethodMayBeStatic
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
        self._animation_speed_delay_between_steps: float = 1 / 10  # 1/50
        self._animation_speed_number_of_steps = 20
        self._alpha_x_0: float = 0.3
        self._alpha_y_0: float = -0.4
        self._alpha_z_0: float = 0

        self._alpha_x: float = 0
        self._alpha_y: float = 0
        self._alpha_z: float = 0
        self._alpha_delta = 0.1

        self._draw_shadows = True
        self.cube_size = 7

        self.slice_start: int = 1
        self.slice_stop: int = 3

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
    def animation_speed_number_of_steps(self):
        return self._animation_speed_number_of_steps

    @property
    def animation_speed_delay_between_steps(self) -> float:
        """

        :return: delay (seconds) between steps
        """
        return self._animation_speed_delay_between_steps

    @property
    def draw_shadows(self):
        return self._draw_shadows
