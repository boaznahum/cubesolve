from typing import Sequence

from cube._solver.base_solver import SolverElement, ISolver
from cube._solver.common_op import CommonOp
from cube.algs import Algs
from cube.model.cube_face import Face
from cube.model.elements import PartColorsID, Part, Corner
from cube.operator.op_annotation import AnnWhat


def use(_):
    pass


class L1Corners(SolverElement):
    __slots__: list[str] = []

    def __init__(self, slv: ISolver) -> None:
        super().__init__(slv)

    @property
    def cmn(self) -> CommonOp:
        return self._cmn

    def _is_corners(self) -> bool:
        return Part.all_match_faces(self.white_face.corners)

    def is_corners(self) -> bool:
        """
        :return: true if 4 corners are in right place ignoring cross orientation
        So you must call solve even if this return true
        """

        wf: Face = self.white_face

        return self.cmn.rotate_and_check(wf, self._is_corners) >= 0

    def solve(self):
        """
        Must be called after cross is solved
        :return:
        """

        if self.is_corners():
            return  # avoid rotating cube

        with self.ann.annotate(h1="Doing L1 Corners"):
            self.cmn.bring_face_up(self.white_face)

            self._do_corners()

    def _do_corners(self):

        wf: Face = self.white_face

        # the colors ID of 4 corners

        # we use codes because maybe position will be changed during the algorithm
        color_codes: Sequence[PartColorsID] = Part.parts_id_by_pos(wf.corners)

        for code in color_codes:
            self._solve_corner(code)

    def _solve_corner(self, corner_id: PartColorsID):

        with self.ann.annotate(
                (corner_id, AnnWhat.Moved), (self.cube.front.corner_top_right, AnnWhat.FixedPosition),
                h2=lambda: f"Bringing {self.cube.find_corner_by_colors(corner_id).name_n_colors} to "
                           f"{self.cube.front.corner_top_right.name} "):
            self.__solve_corner(corner_id)

    def __solve_corner(self, corner_id: PartColorsID):

        _source_corner: Corner | None = None

        _target_corner: Corner | None = None

        # source corner
        def sc() -> Corner:
            nonlocal _source_corner
            if not _source_corner or _source_corner.colors_id_by_color != corner_id:
                _source_corner = self.cube.find_corner_by_colors(corner_id)
            return _source_corner

        # target corner
        def tc() -> Corner:
            nonlocal _target_corner
            if not _target_corner or _target_corner.colors_id_by_pos != corner_id:
                _target_corner = self.cube.find_corner_by_pos_colors(corner_id)
            return _target_corner

        if sc().match_faces:
            # because we have cross, so if it matches then it is in position
            return

        wf: Face = self.cube.up

        self._bring_top_corner_to_front_right_up(tc())

        if sc().on_face(wf):
            self.debug(f"LO-Corners C1. source {sc()} is on top")
            self._bring_top_corner_to_f_r_d(sc())
        else:
            self.debug(f"LO-Corners C2. source {sc()} is on bottom")
            self._bring_bottom_corner_to_f_r_d(sc())

        assert self.cube.front.corner_bottom_right is sc()

        # is the white is on the down
        if sc().f_color(wf.opposite) == wf.color:
            self.debug(f"LO-Corners C3.  {wf.color} is on bottom")
            self.op.op(Algs.R.prime + Algs.D.prime * 2 + Algs.R + Algs.D)
            assert self.cube.front.corner_bottom_right is sc()
            assert sc().f_color(wf.opposite) != wf.color

        if sc().f_color(wf.cube.front) == wf.color:
            self.op.op(Algs.D.prime + Algs.R.prime + Algs.D + Algs.R)
        else:
            self.op.op(Algs.D + Algs.F + Algs.D.prime + Algs.F.prime)

        assert sc().match_faces

    def _bring_top_corner_to_front_right_up(self, c: Corner):
        """
        Preservers top layer cross

        :param c:
        :return:
        """

        wf: Face = self.cube.up
        assert c.on_face(wf)

        if wf.corner_bottom_right is c:
            return

        if wf.corner_top_right is c:
            return self.op.op(Algs.Y)

        if wf.corner_top_left is c:
            return self.op.op(Algs.Y * 2)

        if wf.corner_bottom_left is c:
            return self.op.op(-Algs.Y)

        raise ValueError(f"{c} is not on {wf}")

    def _bring_top_corner_to_f_r_d(self, c: Corner):
        """
        Preservers top layer cross
        doesn't preserve bottom layer

        :param c:
        :return:
        """

        wf: Face = self.cube.up
        assert c.on_face(wf)

        saved_id = c.colors_id_by_color

        if wf.corner_bottom_right is c:
            self.op.op(-Algs.R + -Algs.D + Algs.R)

        elif wf.corner_top_right is c:
            self.op.op(-Algs.B + -Algs.D + Algs.B)

        elif wf.corner_top_left is c:
            self.op.op(Algs.B + -Algs.D + - Algs.B)

        elif wf.corner_bottom_left is c:
            self.op.op(-Algs.F + -Algs.D + Algs.F)

        else:
            raise ValueError(f"{c} is not on {wf}")

        c = self.cube.find_corner_by_colors(saved_id)
        self._bring_bottom_corner_to_f_r_d(c)

    def _bring_bottom_corner_to_f_r_d(self, c: Corner):
        """
        doesn't preserve bottom layer

        :param c:
        :return:
        """

        f: Face = self.cube.down
        assert c.on_face(f)

        if f.corner_top_right is c:
            pass  # nothing to do

        elif f.corner_bottom_right is c:
            self.op.op(-Algs.D)

        elif f.corner_bottom_left is c:
            self.op.op(-Algs.D * 2)

        elif f.corner_top_left is c:
            self.op.op(Algs.D)

        else:
            raise ValueError(f"{c} is not on {f}")
