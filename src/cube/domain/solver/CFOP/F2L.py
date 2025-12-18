from enum import Enum
from typing import FrozenSet

from cube.domain.algs import Algs, Alg
from cube.domain.exceptions import InternalSWError
from cube.domain.model import Part, Edge, Corner, Color
from cube.domain.model.Face import Face
from cube.domain.model.CubeQueries2 import Pred0
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.common.SolverElement import SolverElement
from cube.domain.solver.common.Tracker import EdgeTracker, CornerTracker


class EdgePreserveMode(Enum):
    """
         mode 1 preserve all mathing edges
         mode 2 - preserve matching edge
         mode 3 - preserve none
    """
    PreserveAny = "1"
    PreserveMatching = "2"
    PreserveNone = "3"


def use(_):
    pass


class F2L(SolverElement):
    """
    Credits to https://ruwix.com/the-rubiks-cube/advanced-cfop-fridrich/first-two-layers-f2l/

    """
    __slots__: list[str] = ["_ignore_center_check"]

    def __init__(self, slv: BaseSolver, *, ignore_center_check: bool = False) -> None:
        super().__init__(slv)
        self._set_debug_prefix("F2L")
        self._ignore_center_check = ignore_center_check

    def solved(self) -> bool:
        """
        :return: True if 2 first layers solve d(but still L2 need rotation
        """

        return self._l1_l2_solved()

    def is_l1(self):
        wf = self.cmn.white_face
        if self._ignore_center_check:
            # Check edges and corners directly, bypassing is3x3 check
            return Part.all_match_faces([*wf.edges, *wf.corners])
        return wf.solved

    def is_l2(self):

        edges = self.cmn.l2_edges()

        return Part.all_match_faces(edges)

    def _l1_l2_solved(self):
        wf = self.cmn.white_face

        if self._ignore_center_check:
            # Check edges and corners directly, bypassing is3x3 check
            l1_parts = [*wf.edges, *wf.corners]
            if not Part.all_match_faces(l1_parts):
                return False
        elif not wf.solved:
            return False

        edges = [*self.cmn.l2_edges(), *wf.edges]

        l2_edges_solved = Part.all_match_faces(edges)
        return l2_edges_solved

    def solve(self):
        """
        Must be called after L1 Cross is solved
        :return:
        """

        # L1-cross will rotate if it is the thing that need
        if self.solved():
            return

        with self.cmn.ann.annotate(h1="Doing F2L"):
            wf = self.cmn.white_face

            if self.is_l1() and self.is_l2():
                # OK, need only to rotate

                l1_edges = wf.edges
                self.cmn.rotate_face_till(wf, lambda: Part.all_match_faces(l1_edges))
                return

            # bring white to bottom
            self.cmn.bring_face_up(self.white_face.opposite)

            #            self._bring_all_edges_up()

            cube = self.cube

            def _n_done():

                f = cube.front
                b = cube.back
                return sum([
                    f.corner_bottom_right.match_faces and f.edge_right.match_faces,
                    f.corner_bottom_left.match_faces and f.edge_left.match_faces,

                    b.corner_bottom_right.match_faces and b.edge_right.match_faces,
                    b.corner_bottom_left.match_faces and b.edge_left.match_faces,

                ])

            def need_n_can_work() -> bool:
                corner: CornerTracker = CornerTracker.of_position(cube.front.corner_bottom_right)
                edge: EdgeTracker = EdgeTracker.of_position(cube.front.edge_right)

                if corner.match and edge.match:
                    return False  # in place, nothing to do

                if corner.actual.on_face(cube.up):
                    return True

                if corner.in_position:
                    # case corner on bottom
                    return True

                return False  # corner on bottom but not FRB

            n_done = _n_done()
            after_brought_up = False
            for _ in range(8):

                n = self.cqr.rotate_and_check(Algs.Y, need_n_can_work)

                if n < 0:
                    assert not after_brought_up
                    # Didn't find simple case, so need to bring bottom up
                    brought_up = self._bring_any_corner_up()
                    assert brought_up
                    after_brought_up = True
                    assert _n_done() == n_done  # didn't break solved cases
                    continue

                after_brought_up = False
                self.op.play(Algs.Y * n)

                assert n_done == _n_done()
                work_was_done = self._do_corner_edge()
                assert work_was_done
                n_done += 1
                _done = _n_done()
                assert n_done <= _done  # in some rare cases, when we bring edge up, it solves
                n_done = _done  # because of the rare condition above
                if n_done == 4:
                    break

        assert self.solved()

    def belong_to_middle(self, e: Edge):
        cube = self.cube
        front = cube.front
        back = cube.back

        return e in [front.edge_right,
                     front.edge_left,
                     back.edge_left, back.edge_right]

    def _bring_edge_up(self, edge: Edge, preserve_corner: Corner):

        """
        Bring FL, LB or RB up, preserve FRD and FR

        :param edge:
        :return:
        """
        cube = self.cube

        x: Alg

        if edge is cube.fl:
            x = Algs.F
            destroying_edge = cube.flu
        elif edge is cube.bl:
            x = Algs.L
            destroying_edge = cube.blu
        elif edge is cube.br:
            x = Algs.B
            destroying_edge = cube.bru
        else:
            raise InternalSWError(f"Unsupported case {edge}")

        _id = preserve_corner.colors_id

        if destroying_edge.colors_id == _id:
            pre = Algs.U.p
        else:
            pre = Algs.no_op()

        with self.annotate(h2=f"Bringing up  {edge.name_n_colors}"):

            self.op.play(pre + x + Algs.U + x.p)

    def _do_corner_edge(self) -> bool:

        """

        Assume corner is on top

        Return False if no work was done, corner nor at top nor at required position (FRD)
        These are the only cases I know to solve
        :return:
        """

        # assume white is at bottom
        cube = self.cube

        # the corner and edge we need to fix
        corner: CornerTracker = CornerTracker.of_position(cube.front.corner_bottom_right)
        edge: EdgeTracker = EdgeTracker.of_position(cube.front.edge_right)

        with self.cmn.annotate(([corner.actual, edge.actual], AnnWhat.Moved),
                               ([corner.position, edge.position], AnnWhat.FixedPosition)):

            self.debug(f"Working on {corner.position.name} {edge.position.name} actual {corner.actual} {edge.actual} ")

            up: Face = cube.up
            front: Face = cube.front

            white = cube.down.color

            corner_on_top = corner.actual.on_face(up)
            # corner is on top or in position - handled by caller
            assert corner_on_top or corner.actual.in_position
            # if not corner.actual.in_position:
            #     # no such a case, we need to handle other that will
            #     # move it out
            #     return False

            middle = front.edge_right

            if not (edge.actual.on_face(up) or edge.actual is middle):
                self._bring_edge_up(edge.actual, corner.actual)
                assert edge.actual.on_face(up)
                if corner_on_top:
                    assert corner.actual.on_face(up)

            alg: Alg | None

            play = self.op.play

            e = edge.actual
            assert e is middle or e.on_face(up)  # we brought all up

            if corner_on_top:
                # ok rotate till it is on front/top/right
                def _in_position():
                    return up.corner_bottom_right is corner.actual

                self.cmn.rotate_face_till(up, _in_position)

                assert corner.actual is up.corner_bottom_right

            # https://ruwix.com/the-rubiks-cube/advanced-cfop-fridrich/first-two-layers-f2l/

            if corner_on_top:
                # if we reach here, then corner is up.corner_bottom_right

                if edge.actual is middle:
                    # 3rd case: Corner in top, edge in middle
                    alg = self._case_3_corner_in_top_edge_middle(corner, edge)
                else:

                    if not corner.actual.get_face_edge(up).color == white:
                        ################################################################
                        # 4th case: Corner pointing outwards, edge in top layer
                        # NOT All cases implemented - not checked
                        ################################################################
                        alg = self._case_1_easy_and_case_4_corner_outwards(edge, corner)
                    else:
                        ################################################################
                        # 5th case: Corner pointing upwards, edge in top layer
                        # All cases implemented - not checked
                        ################################################################

                        alg = self._case_5_corner_pointing_upwards(edge, corner)

            else:
                # corner at bottom
                # if we reach here then corner is in position
                assert corner.in_position

                if edge.actual.on_face(up):
                    ################################################################
                    # 2nd case: Corner in bottom, edge in top layer
                    # All cases implemented - not checked
                    ################################################################

                    alg = self._case_2_cornet_top_edge_top(corner, edge)

                elif edge.actual is middle:
                    ################################################################
                    # 6th case: Corner in bottom, edge in middle
                    ################################################################
                    alg = self._case_6_corner_in_bottom_edge_in_middle(edge, corner)
                else:
                    raise InternalSWError("No such a case, corner at bottom, but edge not on top nor middle")

            if alg is None:
                raise InternalSWError(f"Unknown case, corner is {corner.actual.name}, edge is {edge.actual.name}")

            self.debug(f"Case corner is {corner.actual.name}, edge is {edge.actual.name}, Running alg:{alg}")
            play(alg)
            assert corner.match
            assert edge.match

            return True

    # noinspection PyPep8Naming
    def _case_1_easy_and_case_4_corner_outwards(self, edge: EdgeTracker, corner: CornerTracker):

        """
        Case 1 + Case 4, Edge on top, Corner pointing outwards

        Number of cases = 4 + 12 = 16 = 2(corner orientation) * 4(edge position) * 2 edge(orientation)

        in https://ruwix.com/the-rubiks-cube/advanced-cfop-fridrich/first-two-layers-f2l/

        Case 4:
        1       2
        3       4
        5       6
        7       8
        9       10
        11      12
        :param edge:
        :param corner:
        :return:
        """

        self.debug(
            f"Case: 1 Easy or 4th case: Corner pointing outwards, "
            f"edge in top layer: "
            f"{corner.actual.name} {edge.actual.name}")

        cube = self.cube

        up: Face = cube.up
        front: Face = cube.front
        right: Face = cube.right

        u_bottom = up.edge_bottom
        u_right = up.edge_right
        u_left = up.edge_left
        u_top = up.edge_top

        white = cube.down.color
        r_color = right.color
        f_color = front.color

        c = corner.actual
        e = edge.actual

        c_front_color = c.get_face_edge(front).color
        c_right_color = c.get_face_edge(right).color
        c_up_color = c.get_face_edge(up).color

        # verify case
        assert c.on_face(up)
        assert e.on_face(up)
        assert c_up_color != white

        e_up_cc = e.get_face_edge(up).color

        F = Algs.F
        R = Algs.R
        U = Algs.U
        U2 = U * 2
        d = Algs.D[1:1 + cube.n_slices]

        ################################################################
        # 1st: Easy cases: edge at top
        ################################################################

        # Case 1 one just case, when we reach here we are not sure if it is the case
        # so no logging

        alg: Alg | None = None

        if edge.actual is u_top:
            if front.color == c_front_color == e.get_face_edge(up).color:
                alg = R + U - R
        elif edge.actual is u_left:
            if right.color == c_right_color == e.get_face_edge(up).color:
                alg = -F - U + F
        elif edge.actual is u_bottom:
            if front.color == e.get_face_edge(front).color == c_front_color:
                alg = -U - F + U + F
        elif edge.actual is u_right:
            if right.color == e.get_face_edge(right).color == c_right_color:
                alg = U + R - U - R

        if alg:
            self.debug(f"Case:1st: Easy cases: edge at top: {corner.actual.name} {edge.actual.name}")
            return alg

        self.debug(
            f"Case: 4th case: Corner pointing outwards, edge in top layer: {corner.actual.name} {edge.actual.name}")

        ################################################################
        # 4th case: Corner pointing outwards, edge in top layer
        # NOT All cases implemented - not checked
        ################################################################

        e_up_matches_front = e_up_cc == f_color
        e_up_matches_right = e_up_cc == r_color

        c_front_matches_front = c_front_color == f_color
        c_up_matches_front = c_up_color == f_color
        c_up_matches_right = c_up_color == r_color

        case4: str

        if e is u_top:
            if c_front_matches_front and e_up_matches_right:
                # OK !!!
                alg = U - F + U * 2 + F + U - F + U * 2 + F
                case4 = "3"
            elif c_up_matches_front and e_up_matches_front:
                alg = (U.p + R + U + R.p) + (U.p + R + U2 + R.p)
                case4 = "6"
            elif c_up_matches_front and e_up_matches_right:
                alg = (U + F.p + U.p + F + U.p) + (F.p + U.p + F)
                case4 = "10"

            else:
                raise InternalSWError(
                    f"4th case: Corner pointing outwards, "
                    f"edge up top {corner.actual.name} {edge.actual.name}")

        elif e is u_left:
            if c_up_matches_right and e_up_matches_right:
                # OK !!!
                alg = (U + F.p + U.p + F) + (U + F.p + U * 2 + F)
                case4 = "5"
            elif c_up_matches_front and e_up_matches_front:
                alg = (U.p + R + U2 + R.p) + (U.p + R + U2 + R.p)
                case4 = "4"
            elif c_front_matches_front and e_up_matches_front:
                alg = (U.p + R + U + R.p + U) + (R + U + R.p)
                case4 = "7"
            else:
                raise InternalSWError(
                    f"4th case: Corner pointing outwards, "
                    f"edge up left  {c} {e}")

        elif e is u_right:
            if c_up_matches_right and e_up_matches_right:
                alg = (R + U.p + R.p + U) + (d + R.p + U.p + R)
                case4 = "1"
            elif c_up_matches_right and e_up_matches_front:
                alg = (U.p + R + U.p + R.p + U) + (R + U + R.p)
                case4 = "7"
            elif c_up_matches_front and e_up_matches_right:
                alg = (U.p + R + U2 + R.p + U) + (F.p + U.p + F)
                case4 = "12"
            else:
                raise InternalSWError(
                    f"4th case: Corner pointing outwards, "
                    f"edge up right  {c} {e}")

        elif e is u_bottom:
            if c_up_matches_front and e_up_matches_front:
                alg = (F.p + U + F + U.p) + (d.p + F + U + F.p)
                case4 = "2"
            elif c_up_matches_front and e_up_matches_right:
                alg = (U + F.p + U + F + U.p) + (F.p + U.p + F)
                case4 = "8"
            elif c_up_matches_right and e_up_matches_front:
                alg = (U + F.p + U2 + F + U.p) + (R + U + R.p)
                case4 = "11"
            else:
                raise InternalSWError(
                    f"4th case: Corner pointing outwards, "
                    f"edge up right  {c} {e}")

        else:
            raise NotImplementedError(
                f"4th case: Corner pointing outwards, "
                f"edge in top layer {corner.actual.name} "
                f"{edge.actual.name}")

        self.debug(
            f"Case: 4th case: sub case {case4}: {corner.actual.name} {edge.actual.name}")

        return alg

    # noinspection PyPep8Naming
    def _case_2_cornet_top_edge_top(self, corner: CornerTracker, edge: EdgeTracker) -> Alg:

        """
        NUmber of cases = 6 = 3(Corner orientation) * 2 (edge match front or right)

        Actually it covers 24 = 3 * 4 * 2, but pre alg bring it to the above
        :param corner:
        :param edge:
        :return:
        """

        self.debug(
            f"Case: 2nd case: Corner in bottom, edge in top layer: {corner.actual.name} {edge.actual.name}")

        cube = self.cube

        up: Face = cube.up
        front: Face = cube.front
        right: Face = cube.right

        u_bottom = up.edge_bottom
        u_right = up.edge_right

        r_color = right.color
        f_color = front.color

        c = corner.actual
        e = edge.actual

        c_front_color = c.get_face_edge(front).color
        c_right_color = c.get_face_edge(right).color

        # verify case
        assert c is front.corner_bottom_right
        assert e.on_face(up)

        F = Algs.F
        R = Algs.R
        U = Algs.U

        e_up_cc = e.get_face_edge(up).color
        pre: Alg | None

        e_matches_front = e_up_cc == r_color
        if e_matches_front:
            pre = self.cqr.rotate_face_and_check_get_alg(up, lambda: edge.actual is u_bottom)
        else:
            pre = self.cqr.rotate_face_and_check_get_alg(up, lambda: edge.actual is u_right)

        assert pre

        if c.match_faces:

            if e_matches_front:
                # (U R U' R') (U' F' U F)
                alg = pre + (U + R - U - R) + (-U - F + U + F)
            else:
                # (U' F' U F) (U R U' R')
                alg = pre + (-U - F + U + F) + (U + R - U - R)

        elif c_front_color == r_color:
            if e_matches_front:
                # (F' U F) (U' F' U F)
                alg = pre + (-F + U + F) + (-U - F + U + F)
            else:
                # (R U R') (U' R U R')
                alg = pre + (R + U - R) + (-U + R + U - R)

        elif c_right_color == f_color:
            if e_matches_front:
                # (F' U' F) (U F' U' F)
                alg = pre + (-F - U + F) + (U - F - U + F)
            else:
                # (R U' R') (U R U' R')
                alg = pre + (R - U - R) + (U + R - U - R)
        else:
            raise InternalSWError(
                f"Case: Unknown 2nd case: Corner in bottom, edge in top layer: {edge.actual.name}")

        return alg

    # noinspection PyPep8Naming
    def _case_3_corner_in_top_edge_middle(self, corner, edge) -> Alg:

        """"
        Number of cases = 6 = 3(corner orientation) * 2(edge orientation)
        """

        self.debug(
            f"Case: 3rd case: Corner in top, "
            f"edge in middle: {corner.actual.name} {edge.actual.name}")

        cube = self.cube

        up: Face = cube.up
        front: Face = cube.front
        right: Face = cube.right

        r_color = right.color
        f_color = front.color

        c = corner.actual
        e = edge.actual

        c_front_color = c.get_face_edge(front).color
        c_right_color = c.get_face_edge(right).color
        c_up_color = c.get_face_edge(up).color

        # verify case
        assert c.on_face(up)
        assert e is front.edge_right

        F = Algs.F
        R = Algs.R
        U = Algs.U
        U2 = U * 2
        d = Algs.D[1:1 + cube.n_slices]

        e_front_c = e.get_face_edge(front).color

        if c_front_color == r_color and c_right_color == f_color:  # white up

            if e_front_c == f_color:
                alg = (R + U + R.p + U.p) + (R + U + R.p + U.p) + (R + U + R.p)
            else:
                alg = (R + U.p + R.p) + (d + R.p + U + R)

        elif c_front_color == f_color and c_up_color == r_color:  # white right
            if e_front_c == f_color:
                alg = (U + F.p + U + F) + (U + F.p + U2 + F)
            else:
                alg = (U + F.p + U.p + F) + (d.p + F + U + F.p)
        elif c_up_color == f_color and c_right_color == r_color:  # white front
            if e_front_c == f_color:
                alg = (U.p + R + U.p + R.p) + (U.p + R + U2 + R.p)
            else:
                alg = (U.p + R + U + R.p) + (d + R.p + U.p + R)
        else:
            raise NotImplementedError(
                f"Unknown 3rd case: Corner in top, edge in middle {c.name} {e.name}")
        return alg

    # noinspection PyPep8Naming
    def _case_5_corner_pointing_upwards(self, edge: EdgeTracker, corner: CornerTracker):

        """
        Number of cases: 8 = 1(corner orientation) * 2 (edge orientation) * 4 (edge position)
        :param edge:
        :param corner:
        :return:
        """

        self.debug(
            f"Case: 5th case: Corner pointing upwards, "
            f"edge in top layer: {corner.actual.name} {edge.actual.name}")

        cube = self.cube

        up: Face = cube.up
        front: Face = cube.front
        right: Face = cube.right

        u_bottom = up.edge_bottom
        u_right = up.edge_right
        u_left = up.edge_left
        u_top = up.edge_top

        white = cube.down.color
        r_color = right.color
        f_color = front.color

        c = corner.actual
        e = edge.actual

        c_front_color = c.get_face_edge(front).color
        c_right_color = c.get_face_edge(right).color

        # verify case
        assert c.on_face(up)
        assert e.on_face(up)
        c_up_cc = c.get_face_edge(up).color
        assert c_up_cc == white

        e_up_cc = e.get_face_edge(up).color

        F = Algs.F
        R = Algs.R
        U = Algs.U
        U2 = U * 2
        Y = Algs.Y

        if e is u_bottom:

            if e_up_cc == c_right_color == f_color:
                # OK !!!
                alg = (R + U + R.p + U.p) + U.p + (R + U + R.p + U.p) + (
                        R + U + R.p)
            elif e_up_cc == c_front_color == r_color:
                alg = (F.p + U * 2 + F) + (U + F.p + U.p + F)
            else:
                raise InternalSWError(
                    "5th case: Unknown case Corner pointing upwards, edge in top layer,"
                    " unknown case")
        elif e is u_left:
            if e_up_cc == c_right_color == f_color:
                alg = (U2 + R + U + R.p) + (U + R + U.p + R.p)
            elif e_up_cc == c_front_color == r_color:
                alg = (U.p + F.p + U2 + F) + (U.p + F.p + U + F)
            else:
                raise InternalSWError(
                    "5th case: Unknown case Corner pointing upwards, edge in top layer, unknown case")
        elif e is u_right:
            if e_up_cc == c_front_color == r_color:
                alg = Y.p + (R.p + U.p + R + U) + U + (R.p + U.p + R + U) + (R.p + U.p + R)
            elif e_up_cc == c_right_color == f_color:
                alg = (R + U2 + R.p) + (U.p + R + U + R.p)
            else:
                raise InternalSWError(
                    "5th case: Unknown case Corner pointing upwards, edge in top layer, unknown case")
        elif e is u_top:
            if e_up_cc == c_front_color == r_color:

                alg = (U2 + F.p + U.p + F) + (U.p + F.p + U + F)
            elif e_up_cc == c_right_color == f_color:
                alg = (U + R + U2 + R.p) + (U + R + U.p + R.p)
            else:
                raise InternalSWError(
                    "5th case: Unknown case Corner pointing upwards, edge in top layer, unknown case")

        else:
            raise InternalSWError("Unknown error")

        return alg

    # noinspection PyPep8Naming
    def _case_6_corner_in_bottom_edge_in_middle(self, edge: EdgeTracker, corner: CornerTracker):

        """
        Number of cases: 8 = 3(corner orientation) * 2 (edge orientation)
        But one is solved, so it is 5
        :param edge:
        :param corner:
        :return:
        """

        self.debug(
            f"Case: 6th case: Corner in bottom, "
            f"edge in middle: {corner.actual.name} {edge.actual.name}")

        cube = self.cube

        front: Face = cube.front
        right: Face = cube.right

        r_color = right.color
        f_color = front.color

        c = corner.actual
        e = edge.actual

        # verify case
        assert c.on_face(cube.down)
        assert e is front.edge_right

        R = Algs.R
        U = Algs.U
        U2 = U * 2
        d = Algs.D[1:1 + cube.n_slices]

        c_front_color = c.get_face_edge(front).color
        c_right_color = c.get_face_edge(right).color
        e_front_c = e.get_face_edge(front).color

        e_front_matches_front = e_front_c == f_color
        e_front_matches_right = e_front_c == r_color

        c_front_matches_front = c_front_color == f_color
        c_front_matches_right = c_front_color == r_color
        c_right_matches_front = c_right_color == f_color

        # Cases in https://ruwix.com/the-rubiks-cube/advanced-cfop-fridrich/first-two-layers-f2l/
        #  1
        #  2  3
        #  4  5

        alg: Alg
        if c_front_matches_front and e_front_matches_right:
            case6 = "1"
            alg = (R + U.p + R.p + d + R.p + U2 + R) + (U + R.p + U2 + R)
        elif c_front_matches_right and e_front_matches_front:
            case6 = "2"
            alg = (R + U.p + R.p + U + R + U2 + R.p) + (U + R + U.p + R.p)
        elif c_right_matches_front and e_front_matches_front:
            case6 = "3"
            alg = (R + U.p + R.p + U.p + R + U + R.p) + (U.p + R + U2 + R.p)
        elif c_front_matches_right and e_front_matches_right:
            case6 = "4"
            alg = (R + U + R.p + U.p + R + U.p + R.p) + (U + d + R.p + U.p + R)
        elif c_right_matches_front and e_front_matches_right:
            case6 = "5"
            alg = (R + U.p + R.p + d + R.p + U.p + R) + (U.p + R.p + U.p + R)

        else:
            raise InternalSWError(f"6th case: Unknown case, Corner in bottom, edge in middle, {c}, {e}")

        self.debug(
            f"Case: 6th case: sub case {case6}: {corner.actual.name} {edge.actual.name}")

        return alg

    def _bring_corner_up_find_alg(self, corner: Corner,
                                  edge_to_preserve: Edge,
                                  mode: EdgePreserveMode) -> Alg | None:

        """
        Check if corner belong to bottom

        And it can be uploaded -
         mode 1 - preserve all mathing edges
         mode 2 - preserve matching edge
         mode 3 - preserve none

        Assume white is at down


        :return: return the alg the preserve
        """

        # according to code coverage, "2" and "3" never happens
        cube = self.cube

        preserve_cond: Pred0

        if mode == EdgePreserveMode.PreserveAny:
            preserve_cond = lambda: not self.belong_to_middle(edge_to_preserve.required_position)

        elif mode == EdgePreserveMode.PreserveMatching:  # only preservers matching edge

            matching_edge = self._matching_edge(corner).colors_id

            preserve_cond = lambda: edge_to_preserve.colors_id != matching_edge
        else:
            preserve_cond = lambda: True

        pre = self.cqr.rotate_face_and_check_get_alg(cube.up, preserve_cond)

        return pre

    def _bring_any_corner_up_find_alg(self) -> Alg | None:

        """
        Search corner on bottom that belong to bottom and upload it

        And it can be uploaded - there is an edge that can be moved down ,

        Assume white is at down

        # first try to not bring any(middle) edge down
        # then try not bring matching edge down
        # then do any

        :raise
        :return:
        """

        cube = self.cube

        down = cube.down

        def need_bring_up(c: Corner):
            if c.in_position:  # it is already solved, or can be solved !!!
                return False
            return c.required_position.on_face(down)

        def _check_corner(c: Corner, edge_to_preserve: Edge, mode: EdgePreserveMode) -> Alg | None:

            if not need_bring_up(c):
                return None

            preserve_alg = self._bring_corner_up_find_alg(c, edge_to_preserve, mode)

            return preserve_alg

        for mod in EdgePreserveMode:

            pre = _check_corner(cube.front.corner_bottom_left, cube.up.edge_top, mod)

            if pre:  # can be done
                self.debug("Bringing FLD up")
                alg = pre + (Algs.L.p + Algs.U.p + Algs.L)
                return alg

            pre = _check_corner(cube.left.corner_bottom_left, cube.up.edge_bottom, mod)

            if pre:  # can be done
                self.debug("Bringing BLD up")
                alg = pre + (Algs.L + Algs.U + Algs.L.p)
                return alg

            pre = _check_corner(cube.right.corner_bottom_right, cube.up.edge_right, mod)
            if pre:  # can be done
                self.debug("Bringing BRD up")
                alg = pre + Algs.B + Algs.U + Algs.B.p
                return alg

        raise InternalSWError("Can't happen")

    def _bring_any_corner_up(self) -> bool:

        """
        Search corner on bottom that belong to bottom and upload it

        Try to preserve the matching edge

        And it can be uploaded - there is an edge that can be moved down ,

        Assume white is at down
        :raise
        :return:
        """

        alg = self._bring_any_corner_up_find_alg()

        if alg:
            self.op.play(alg)
            return True

        return False

    def _matching_edge(self, corner: Corner) -> Edge:
        """
        Given a corner, find the matching edge
        :param corner:
        :return:
        """

        cube = self.cube
        white = cube.down.color

        corner_id: frozenset[Color] = corner.colors_id
        assert white in corner_id

        # pyright doesn't understand frozenset - ?
        edge_id = corner_id - white  # type: ignore[reportOperatorIssue]

        return cube.find_edge_by_color(edge_id)
