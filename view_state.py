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

    def __init__(self, ax0, ay0, az0, a_delta) -> None:
        super().__init__()
        self._alpha_x_0: float = ax0
        self._alpha_y_0: float = ay0
        self._alpha_z_0: float = az0

        self._alpha_x: float = 0
        self._alpha_y: float = 0
        self._alpha_z: float = 0
        self._alpha_delta = a_delta

    def reset(self, ax0, ay0, az0, a_delta):
        self._alpha_x_0: float = ax0
        self._alpha_y_0: float = ay0
        self._alpha_z_0: float = az0

        self._alpha_x: float = 0
        self._alpha_y: float = 0
        self._alpha_z: float = 0
        self._alpha_delta = a_delta

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
