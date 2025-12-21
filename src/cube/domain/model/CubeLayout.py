"""Cube layout management."""

from __future__ import annotations

from collections.abc import Collection
from typing import Mapping, TYPE_CHECKING

from cube.domain.exceptions import InternalSWError
from cube.utils.config_protocol import IServiceProvider, ConfigProtocol
from .FaceName import FaceName
from .Color import Color


class CubeLayout:
    _opposite: Mapping[FaceName, FaceName] = {FaceName.F: FaceName.B, FaceName.U: FaceName.D, FaceName.L: FaceName.R}

    _rev_opposite: Mapping[FaceName, FaceName] = {v: k for k, v in _opposite.items()}

    _all_opposite: Mapping[FaceName, FaceName] = {**_opposite, **_rev_opposite}

    def __init__(self, read_only: bool, faces: Mapping[FaceName, Color],
                 sp: IServiceProvider) -> None:
        super().__init__()
        self._faces: dict[FaceName, Color] = dict(faces)
        self._read_only = read_only
        self._sp = sp
        self._edge_colors: Collection[frozenset[Color]] | None = None

    @property
    def config(self) -> ConfigProtocol:
        """Get configuration via service provider."""
        return self._sp.config

    def __getitem__(self, face: FaceName) -> Color:
        """Get the color for a specific face."""
        return self._faces[face]

    def colors(self) -> Collection[Color]:
        return [*self._faces.values()]

    def edge_colors(self) -> Collection[frozenset[Color]]:

        if self._edge_colors is not None:
            return self._edge_colors

        colors: set[frozenset[Color]] = set()

        for f1, c1 in self._faces.items():
            for f2, c2 in self._faces.items():
                if f1 is not f2:
                    if f2 is not CubeLayout._all_opposite[f1]:
                        c = frozenset((c1, c2))
                        colors.add(c)

        self._edge_colors = colors

        return self._edge_colors

    @staticmethod
    def opposite(fn: FaceName) -> FaceName:
        return CubeLayout._all_opposite[fn]

    def opposite_color(self, color: Color) -> Color:
        return self._faces[CubeLayout.opposite(self._find_face(color))]

    def same(self, other: "CubeLayout"):
        """

        :param other:
        :return: true if same layout as other
        """

        # becuase this might bin NxN in which center color have no meaning
        # we need to check
        for c in other.colors():
            if not self._is_face(c):
                return False

        # so it safe to continue !!!

        this = self.clone()

        # Check opposite colors
        # make sure that opposite colors on this, are the same in other layout
        for f1, f2 in CubeLayout._opposite.items():

            c1 = other._faces[f1]
            c2 = other._faces[f2]

            this_c1_face: FaceName = this._find_face(c1)
            this_c2_face = CubeLayout._all_opposite[this_c1_face]

            this_c2 = this._faces[this_c2_face]
            if c2 != this_c2:
                return False

        # find color of other front
        other_f_color: Color = other._faces[FaceName.F]

        this_f_match = this._find_face(other_f_color)

        this._bring_face_to_front(this_f_match)
        assert this._faces[FaceName.F] == other_f_color

        # find UP color on other
        other_u_color = other._faces[FaceName.U]

        this_u_match = this._find_face(other_u_color)
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

        return CubeLayout(False, self._faces, self._sp)

    def _is_face(self, color) -> FaceName | None:
        for f, c in self._faces.items():

            if c == color:
                return f

        return None

    def _find_face(self, color) -> FaceName:

        fn = self._is_face(color)

        if fn:
            return fn

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
            self._check()
            f = faces[FaceName.F]
            faces[FaceName.F] = faces[FaceName.D]
            faces[FaceName.D] = faces[FaceName.B]
            faces[FaceName.B] = faces[FaceName.U]
            faces[FaceName.U] = f
            self._check()

    def _rotate_y(self, n: int):

        """
        Rotate over U
        :param n:
        :return:
        """
        faces = self._faces

        for _ in range(n % 4):
            self._check()
            f = faces[FaceName.F]
            faces[FaceName.F] = faces[FaceName.R]
            faces[FaceName.R] = faces[FaceName.B]
            faces[FaceName.B] = faces[FaceName.L]
            faces[FaceName.L] = f
            self._check()

    def _rotate_z(self, n: int):

        """
        Rotate over F
        :param n:
        :return:
        """
        faces = self._faces

        for _ in range(n % 4):
            self._check()
            u = faces[FaceName.U]
            faces[FaceName.U] = faces[FaceName.L]
            faces[FaceName.L] = faces[FaceName.D]
            faces[FaceName.D] = faces[FaceName.R]
            faces[FaceName.R] = u
            self._check()

    def __str__(self) -> str:

        faces: dict[FaceName, Color] = self._faces

        s = ""

        s += "-" + str(faces[FaceName.B].value) + "-" + "\n"
        s += "-" + str(faces[FaceName.U].value) + "-" + "\n"
        s += str(faces[FaceName.L].value) + str(faces[FaceName.F].value) + str(faces[FaceName.R].value) + "\n"
        s += "-" + str(faces[FaceName.D].value) + "-" + "\n"

        return s

    def __repr__(self) -> str:
        return self.__str__()

    def _check(self):
        if not self.config.check_cube_sanity:
            return

        for c in Color:
            assert self._find_face(c)
