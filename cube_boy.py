from collections.abc import Sequence, Collection
from enum import unique, Enum
from typing import Mapping

from app_exceptions import InternalSWError


@unique
class FaceName(Enum):
    U = "U"
    D = "D"
    F = "F"
    B = "B"
    L = "L"
    R = "R"


@unique
class Color(Enum):
    BLUE = "B"
    ORANGE = "O"
    YELLOW = "Y"
    GREEN = "G"
    RED = "R"
    WHITE = "W"


class CubeLayout:
    _opposite: Mapping[FaceName, FaceName] = {FaceName.F: FaceName.B, FaceName.U: FaceName.D, FaceName.L: FaceName.R}

    _rev_opposite: Mapping[FaceName, FaceName] = {v: k for k, v in _opposite.items()}

    _all_opposite: Mapping[FaceName, FaceName] = {**_opposite, **_rev_opposite}

    def __init__(self, read_only: bool, faces: Mapping[FaceName, Color]) -> None:
        super().__init__()
        self._faces: dict[FaceName, Color] = dict(faces)
        self._read_only = read_only

    def colors(self) -> Collection[Color]:
        return [* self._faces.values() ]

    @staticmethod
    def opposite(fn: FaceName) -> FaceName:
        return CubeLayout._all_opposite[fn]

    def opposite_color(self, color: Color) -> Color:
        return self._faces[CubeLayout.opposite(self.find_face(color))]


    def same(self, other: "CubeLayout"):
        """

        :param other:
        :return: true if same layout as other
        """

        this = self.clone()

        # Check opposite colors
        # make sure that opposite colors on this, are the same in other layout
        for f1, f2 in CubeLayout._opposite.items():

            c1 = other._faces[f1]
            c2 = other._faces[f2]

            this_c1_face: FaceName = this.find_face(c1)
            this_c2_face = CubeLayout._all_opposite[this_c1_face]

            this_c2 = this._faces[this_c2_face]
            if c2 != this_c2:
                return False

        # find color of other front
        other_f_color: Color = other._faces[FaceName.F]

        this_f_match = this.find_face(other_f_color)

        this._bring_face_to_front(this_f_match)
        assert this._faces[FaceName.F] == other_f_color

        # find UP color on other
        other_u_color = other._faces[FaceName.U]

        this_u_match = this.find_face(other_u_color)
        if this_u_match == FaceName.B:
            return False  # on this it is on Back, can't match other layout

        this._bring_face_up_preserve_front(this_u_match)  # preserve front
        assert this._faces[FaceName.U] == other_u_color

        other_l_color = other._faces[FaceName.L]

        this_l_color = this._faces[FaceName.L]

        if other_l_color != this_l_color:
            return False

        return True  # same layout

    def clone(self):

        return CubeLayout(False, self._faces)

    def find_face(self, color) -> FaceName:
        for f, c in self._faces.items():

            if c == color:
                return f

        raise InternalSWError(f"No such color {color} in {self}")

    def _bring_face_to_front(self, f: FaceName):

        assert not self._read_only

        if f != FaceName.F:

            match f:

                case FaceName.U:
                    self._rotate_x(-1)

                case FaceName.B:
                    self._rotate_x(-2)

                case FaceName.D:
                    self._rotate_x(1)

                case FaceName.L:
                    self._rotate_y(-1)

                case FaceName.R:
                    self._rotate_y(1)

                case _:
                    raise InternalSWError(f"Unknown face {f}")

    def _bring_face_up_preserve_front(self, face: FaceName):

        if face == FaceName.U:
            return

        if face == FaceName.B:
            raise InternalSWError(f"{face} is not supported")

        match face:

            case FaceName.L:
                self._rotate_z(1)

            case FaceName.D:
                self._rotate_z(2)

            case FaceName.R:
                self._rotate_z(-1)

            case _:
                raise InternalSWError(f" Unknown face {face.name}")

    def _rotate_x(self, n: int):

        """
        Rotate over R
        :param n:
        :return:
        """
        faces = self._faces

        for _ in range(n % 4):
            f = faces[FaceName.F]
            faces[FaceName.F] = faces[FaceName.D]
            faces[FaceName.D] = faces[FaceName.B]
            faces[FaceName.B] = faces[FaceName.U]
            faces[FaceName.U] = f

    def _rotate_y(self, n: int):

        """
        Rotate over U
        :param n:
        :return:
        """
        faces = self._faces

        for _ in range(n % 4):
            f = faces[FaceName.F]
            faces[FaceName.F] = faces[FaceName.R]
            faces[FaceName.R] = faces[FaceName.B]
            faces[FaceName.B] = faces[FaceName.L]
            faces[FaceName.L] = f

    def _rotate_z(self, n: int):

        """
        Rotate over F
        :param n:
        :return:
        """
        faces = self._faces

        for _ in range(n % 4):
            u = faces[FaceName.U]
            faces[FaceName.U] = faces[FaceName.L]
            faces[FaceName.L] = faces[FaceName.D]
            faces[FaceName.D] = faces[FaceName.R]
            faces[FaceName.R] = u

    def __str__(self) -> str:

        faces: dict[FaceName, Color] = self._faces

        s = ""

        s += "-" + faces[FaceName.B].value + "-" + "\n"
        s += "-" + faces[FaceName.U].value + "-" + "\n"
        s += faces[FaceName.L].value + faces[FaceName.F].value + faces[FaceName.R].value + "\n"
        s += "-" + faces[FaceName.D].value + "-" + "\n"

        return s

    def __repr__(self) -> str:
        return self.__str__()


