from typing import Sequence

from cube.algs import Algs, Alg, SeqAlg
from cube.app_exceptions import InternalSWError
from cube.model.cube_face import Face
from cube.model import PartColorsID, Part, Edge, Color, Corner
from cube.operator.op_annotation import AnnWhat
from cube.solver.common.solver_element import SolverElement
from cube.solver.common.common_op import CommonOp
from cube.solver.common.base_solver import BaseSolver
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

        # L1-cross will roate if it is the thing that need
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

            cube = self.cube

            for _ in range(4):
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

                n = self.cmn.rotate_and_check(Algs.Y, need_to_work)

                # all ok, so must be  solved
                if n < 0:
                    assert self.solved()
                    return

                self.op.play(Algs.Y * n)

                self._do_corner_edge()

    def _do_corner_edge(self) -> bool:

        # assume white is at bottom
        cube = self.cube

        # the corner and edge we need to fix
        corner: CornerTracker = CornerTracker.of_position(cube.front.corner_bottom_right)
        edge: EdgeTracker = EdgeTracker.of_position(cube.front.edge_right)

        with self.cmn.annotate(([corner.actual, edge.actual], AnnWhat.Moved),
                               ([corner.position, edge.position], AnnWhat.FixedPosition)):

            self.debug(f"Working on {corner.position} {edge.position}")

            up: Face = cube.up
            front: Face = cube.front
            back: Face = cube.back
            right: Face = cube.right

            white = cube.down.color
            r_color = right.color
            f_color = front.color

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

            if self._upload_edge_to_top(corner, edge):
                c = corner.actual
                e = edge.actual

                assert bool(c.on_face(up)) == bool(corner_on_top), "Corner changed layer"
                assert e.on_face(up)

            assert e.on_face(up) or e is front.edge_right

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

                    ################################################################
                    # 4th case: edge at top
                    # NOT All cases implemented - not checked
                    ################################################################
                    alg = self._case_1_easy(corner, edge)

                    if not alg:

                        if not corner.actual.get_face_edge(up).color == white:
                            ################################################################
                            # 4th case: Corner pointing outwards, edge in top layer
                            # NOT All cases implemented - not checked
                            ################################################################
                            alg = self._case_4_corner_outwards(edge, corner)
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
                    # 6th case: Corner in bottom, edge in middle
                    raise NotImplementedError("6th case: Corner in bottom, edge in middle")
                else:
                    raise InternalSWError("No such a case, corner at bottom, not on top nor on middle")

            if alg is None:
                raise InternalSWError(f"Unknown case, corner is {corner.actual.name}, edge is {edge.actual.name}")

            self.debug(f"Case corner is {corner.actual.name}, edge is {edge.actual.name}, Running alg:{alg}")
            play(alg)
            assert corner.match
            assert edge.match

            return True

    def _upload_edge_to_top(self, corner: CornerTracker, edge: EdgeTracker):

        cube = self.cube

        up: Face = cube.up
        front: Face = cube.front
        back: Face = cube.back

        c = corner.actual
        e = edge.actual

        U = Algs.U
        B = Algs.B
        L = Algs.L


        e_uploaded: SeqAlg = Algs.seq_alg(None)

        if e is back.edge_right:
            if c is up.corner_top_left:
                e_uploaded += U  # don't move top down
            e_uploaded += B.prime + U + B
        elif e is back.edge_left:
            if c is up.corner_top_right:
                e_uploaded += U  # don't move top down
            e_uploaded += B + U + B.prime
        elif e is front.edge_left:
            if c is front.corner_bottom_right:
                e_uploaded += U  # don't move top down
            e_uploaded += L.prime + U + L.prime
        if e_uploaded.algs:
            self.debug(f"Before edge uploaded, corner is {c}")
            self.op.play(e_uploaded)
            # both might be moved
            c = corner.actual
            e = edge.actual

            self.debug(f"Brought e to {e.name}, corner is {c.name}, {e_uploaded}")
            # we must not touch top

            return True
        else:
            return False



    def _case_1_easy(self, corner: CornerTracker, edge: EdgeTracker):

        ################################################################
        # 1st: Easy cases: edge at top
        ################################################################

        # Case 1 one just case, when we reach here we are not sure if it is the case
        # so no logging
        cube = self.cube

        up: Face = cube.up
        front: Face = cube.front
        back: Face = cube.back
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

        F = Algs.F
        R = Algs.R
        U = Algs.U
        U2 = U * 2
        B = Algs.B
        L = Algs.L
        d = Algs.D[1:1 + cube.n_slices]
        Y = Algs.Y

        alg = None

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

    def _case_2_cornet_top_edge_top(self, corner: CornerTracker, edge: EdgeTracker) -> Alg:

        self.debug(
            f"Case: 2nd case: Corner in bottom, edge in top layer: {corner.actual.name} {edge.actual.name}")

        cube = self.cube

        up: Face = cube.up
        front: Face = cube.front
        back: Face = cube.back
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
        assert c is front.corner_bottom_right
        assert e.on_face(up)

        F = Algs.F
        R = Algs.R
        U = Algs.U
        U2 = U * 2
        B = Algs.B
        L = Algs.L
        d = Algs.D[1:1 + cube.n_slices]
        Y = Algs.Y

        alg = None

        e_up_cc = e.get_face_edge(up).color
        _pre: Alg = Algs.seq_alg(None)
        e_matches_front = e_up_cc == r_color
        if e_matches_front:
            pre = self.cmn.rotate_face_and_check_get_alg(up, lambda: edge.actual is u_bottom)
        else:
            pre = self.cmn.rotate_face_and_check_get_alg(up, lambda: edge.actual is u_right)
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
                alg = _pre + (-F + U + F) + (-U - F + U + F)
            else:
                # (R U R') (U' R U R')
                alg = _pre + (R + U - R) + (-U + R + U - R)

        elif c_right_color == f_color:
            if e_matches_front:
                # (F' U' F) (U F' U' F)
                alg = _pre + (-F - U + F) + (U - F - U + F)
            else:
                # (R U' R') (U R U' R')
                alg = _pre + (R - U - R) + (U + R - U - R)
        else:
            raise InternalSWError(
                f"Case: Unknown 2nd case: Corner in bottom, edge in top layer: {edge.actual.name}")

        return alg

    def _case_3_corner_in_top_edge_middle(self, corner, edge):

        self.debug(
            f"Case: 3rd case: Corner in top, "
            f"edge in middle: {corner.actual.name} {edge.actual.name}")

        cube = self.cube

        up: Face = cube.up
        front: Face = cube.front
        back: Face = cube.back
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
        assert e is front.edge_right

        F = Algs.F
        R = Algs.R
        U = Algs.U
        U2 = U * 2
        B = Algs.B
        L = Algs.L
        d = Algs.D[1:1 + cube.n_slices]
        Y = Algs.Y

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

    def _case_4_corner_outwards(self, edge: EdgeTracker, corner: CornerTracker):

        self.debug(
            f"Case: 4th case: Corner pointing outwards, edge in top layer: {corner.actual.name} {edge.actual.name}")

        cube = self.cube

        up: Face = cube.up
        front: Face = cube.front
        back: Face = cube.back
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
        assert c_up_cc != white

        e_up_cc = e.get_face_edge(up).color

        F = Algs.F
        R = Algs.R
        U = Algs.U
        U2 = U * 2
        B = Algs.B
        L = Algs.L
        d = Algs.D[1:1 + cube.n_slices]
        Y = Algs.Y

        if e is u_top:
            if front.color == c.get_face_edge(front).color and right.color == e.get_face_edge(
                    up).color:
                # OK !!!
                alg = U - F + U * 2 + F + U - F + U * 2 + F
            else:
                raise InternalSWError(
                    f"4th case: Corner pointing outwards, edge in top layer {corner.actual.name} {edge.actual.name}")

        elif e is u_left:
            if f_color == c_front_color and e.get_face_edge(up).color == r_color:
                # OK !!!
                alg = (U + F.prime + U.prime + F) + (U + F.prime + U * 2 + F)
            elif r_color == c_right_color and e.get_face_edge(up).color == f_color:
                alg = (U.p + R + U2 + R.p) + (U.p + R + U2 + R.p)
            elif f_color == c_front_color == e_up_cc:
                alg = (U.p + R + U + R.p + U) + (R + U + R.p)
            else:
                raise InternalSWError(
                    f"4th case: Corner pointing outwards, "
                    f"edge in top layer {edge.actual.name}")

        else:
            raise NotImplementedError(
                f"4th case: Corner pointing outwards, "
                f"edge in top layer {corner.actual.name} "
                f"{edge.actual.name}")

        return alg

    def _case_5_corner_pointing_upwards(self, edge: EdgeTracker, corner: CornerTracker):

        self.debug(
            f"Case: 5th case: Corner pointing upwards, "
            f"edge in top layer: {corner.actual.name} {edge.actual.name}")

        cube = self.cube

        up: Face = cube.up
        front: Face = cube.front
        back: Face = cube.back
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
        B = Algs.B
        L = Algs.L
        d = Algs.D[1:1 + cube.n_slices]
        Y = Algs.Y


        if e is u_bottom:

            if e_up_cc == c_right_color == f_color:
                # OK !!!
                alg = (R + U + R.prime + U.prime) + U.prime + (R + U + R.prime + U.prime) + (
                        R + U + R.prime)
            elif e_up_cc == c_front_color == r_color:
                alg = (F.prime + U * 2 + F) + (U + F.prime + U.prime + F.prime)
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
