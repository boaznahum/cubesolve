from typing import Optional

from cube.algs import Algs, Alg
from cube.app_exceptions import InternalSWError
from cube.model import Part, Edge, Corner
from cube.model.cube_face import Face
from cube.operator.op_annotation import AnnWhat
from cube.solver.common.base_solver import BaseSolver
from cube.solver.common.solver_element import SolverElement
from cube.solver.common.tracker import EdgeTracker, CornerTracker


def use(_):
    pass


class F2L(SolverElement):
    __slots__: list[str] = []

    def __init__(self, slv: BaseSolver) -> None:
        super().__init__(slv)
        self._set_debug_prefix("F2L")

    def solved(self) -> bool:
        """
        :return: True if 2 first layers solve d(but still L2 need rotation
        """

        return self._l1_l2_solved()

    def is_l1(self):
        return self.cmn.white_face.solved

    def is_l2(self):

        edges = self.cmn.l2_edges()

        return Part.all_match_faces(edges)

    def _l1_l2_solved(self):
        wf = self.cmn.white_face
        if not wf.solved:
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

            self._bring_all_edges_up()

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

            def need_to_work():
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

            if self.cmn.rotate_and_check(Algs.Y, need_to_work) < 0:
                if not self._bring_any_corner_up():
                    # deal with special initial case, no work can be done
                    # no work to be done and no corner can be uploaded because all edges
                    # in up are belong to middle, this can be happened only if no edge is solved(other it is not on top)
                    # all corners that need to solved ar on bottom face, if it was on top then need_to_work would
                    # return non Noe

                    # ok, choose one corner and
                    fixed = self._bring_frb_corner_up_fru_preserve_matching_edge()
                    # now one belong to middle is on bottom, will fix it later
                    assert fixed

                    # now prepare to solve it

                    n = self.cmn.rotate_and_check(Algs.Y, need_to_work)
                    assert n >= 0

                    self.op.play(Algs.Y * n)

                    work_was_done = self._do_corner_edge()
                    assert work_was_done

                    # now we have an edge on middle, i didn't bring it to top again, but still
                    # it works, I don't know why

                    # OK, now one belong to middle is on bottom,need to fix, preserving FRD

            n_done = _n_done()
            after_brought_up = False
            for _ in range(8):

                n = self.cmn.rotate_and_check(Algs.Y, need_to_work)

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
                assert n_done == _n_done()
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

    def _bring_all_edges_up(self):
        cube = self.cube

        def need_to_work():

            """
            Return true if edge at front/right to be moved up
            It need to moved up it belong  to one of middle edges but not already
            in position
            :return:
            """

            e = cube.front.edge_right

            if e.in_position or not self.belong_to_middle(e.required_position):
                # if in position, alg can handle it
                return False
            else:
                return True

        def edge_fb_can_be_moved_to_middle():

            e = cube.up.edge_top

            return not self.belong_to_middle(e.required_position)

        n = self.cmn.rotate_and_check(Algs.Y, need_to_work)

        if n < 0:
            return

        with self.ann.annotate(h2=f"Bring all edges up"):

            while True:
                self.op.play(Algs.Y * n)

                # now make sure edge UB is not also need uploaded
                n = self.cmn.rotate_and_check(Algs.U, edge_fb_can_be_moved_to_middle)

                assert n >= 0  # otherwise we can't do RUR prime

                if n > 0:
                    self.op.play(Algs.U * n)

                with self.ann.annotate((cube.fr, AnnWhat.Moved), h2=f"{cube.fr.name_n_colors}"):
                    self.op.play(Algs.R + Algs.U + Algs.R.p)

                n = self.cmn.rotate_and_check(Algs.Y, need_to_work)

                if n < 0:
                    return


    def _do_corner_edge(self) -> bool:

        """
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
            # corner is on top
            if not corner_on_top:
                if not corner.actual.in_position:
                    # no such a case, we need to handle other that will
                    # move it out
                    return False

            middle = front.edge_right

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
        pre: Alg
        e_matches_front = e_up_cc == r_color
        if e_matches_front:
            pre = self.cmn.rotate_face_and_check_get_alg_deprecated(up, lambda: edge.actual is u_bottom)
        else:
            pre = self.cmn.rotate_face_and_check_get_alg_deprecated(up, lambda: edge.actual is u_right)
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
    def _case_3_corner_in_top_edge_middle(self, corner, edge):

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

    def _bring_any_corner_up_find_alg(self) -> Optional[Alg]:

        """
        Search corner on bottom that belong to bottom and upload it

        And it can be uploaded - there is an edge that can be moved down ,

        Assume white is at down

        :raise
        :return:
        """

        cube = self.cube

        down = cube.down

        def need_bring_up(c: Corner):
            if c.in_position:  # it is already solved, or can be solved !!!
                return False
            return c.required_position.on_face(down)

        def rotate_till_edge_not_belong_to_middle(e: Edge) -> Optional[Alg]:
            # because the algorithm bring it down
            return self.cmn.rotate_face_and_check_get_alg(cube.up,
                                                          lambda: not self.belong_to_middle(
                                                              e.required_position))

        if need_bring_up(cube.front.corner_bottom_left):
            pre = rotate_till_edge_not_belong_to_middle(cube.up.edge_top)

            if pre:  # can be done
                self.debug("Bringing FLD up")
                alg = pre + (Algs.L.p + Algs.U.p + Algs.L)
                return alg

        elif need_bring_up(cube.left.corner_bottom_left):
            pre = rotate_till_edge_not_belong_to_middle(cube.up.edge_bottom)

            if pre:  # can be done
                self.debug("Bringing BLD up")
                alg = pre + (Algs.L + Algs.U + Algs.L.p)
                return alg

        elif need_bring_up(cube.right.corner_bottom_right):
            pre = rotate_till_edge_not_belong_to_middle(cube.up.edge_right)
            if pre:  # can be done
                self.debug("Bringing BRD up")
                alg = pre + Algs.B + Algs.U + Algs.B.p
                return alg

        # All middle edges are up, all corner at bottom not fit position !!!
        # this can happen only if at start that none of edges are solved, because if one is solved
        # then it can't be that all edges at top belong to middle
        return None

    def _bring_any_corner_up(self) -> bool:

        """
        Search corner on bottom that belong to bottom and upload it

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

    def _bring_frb_corner_up_fru_preserve_matching_edge(self):

        """
        And bring frd into FRU
        :return:
        """

        cube = self.cube

        frd = cube.frd
        frd_colors = frd.colors_id_by_color
        # it belongs to down because it needed to be solved
        assert frd.required_position.on_face(cube.down)  #
        # find other two faces (of white)

        # matching edge
        edge_id = frd.colors_id_by_color - {cube.down.color}

        # THE ALGORITHM BELOW DESTROY UB, bring it down
        pre = self.cmn.rotate_face_and_check_get_alg(cube.up,
                                                     lambda: cube.ub.colors_id_by_color != edge_id)

        if not pre:
            return False

        # can be done

        self.debug("Bringing FRD up")
        with self.ann.annotate((frd, AnnWhat.Moved), h2=f"Bring {frd.name_n_colors} up"):
            alg = pre + (Algs.R + Algs.U + Algs.R.p)

            self.op.play(alg)

        # that were the alg move it
        assert cube.flu.colors_id_by_color == frd_colors

        return True
