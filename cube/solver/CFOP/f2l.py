from typing import Sequence

from cube.algs import Algs, Alg
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

            corner_on_top: bool
            # corner is on top
            if corner.actual.on_face(up):
                # ok rotate till it is on front/top/right
                def _in_position():
                    return up.corner_bottom_right is corner.actual

                self.cmn.rotate_face_till(up, _in_position)

                assert corner.actual is up.corner_bottom_right

                corner_on_top = True
            else:
                if not corner.actual.in_position:
                    # no such a case, we need to handle other that will
                    # move it out
                    return False

                corner_on_top = False

            F = Algs.F
            R = Algs.R
            U = Algs.U

            u_bottom = up.edge_bottom
            u_right = up.edge_right
            u_left = up.edge_left
            u_top = up.edge_top
            middle = [front.edge_left, front.edge_right, back.edge_right, back.edge_left]

            c = corner.actual
            e = edge.actual

            alg: Alg | None = None

            # https://ruwix.com/the-rubiks-cube/advanced-cfop-fridrich/first-two-layers-f2l/
            if corner_on_top:
                # if we reach here, then corner is up.corner_bottom_right

                c_front_color = c.get_face_edge(front).color
                c_up_color = c.get_face_edge(up).color
                c_right_color = c.get_face_edge(right).color

                if edge.actual.on_face(up):
                    # 1st: Easy cases: edge at top
                    if edge.actual is u_top:
                        if front.color == c.get_face_edge(front).color == e.get_face_edge(up).color:
                            alg = R + U - R
                    elif edge.actual is u_left:
                        if right.color == c.get_face_edge(right).color == e.get_face_edge(up).color:
                            alg = -F - U + F
                    elif edge.actual is u_bottom:
                        if front.color == e.get_face_edge(front).color == c.get_face_edge(front).color:
                            alg = -U - F + U + F
                    elif edge.actual is u_right:
                        if right.color == c.get_face_edge(right).color == e.get_face_edge(right).color:
                            alg = U + R - U - R

                    if alg:
                        self.debug(f"Case:1st: Easy cases: edge at top: {corner.actual.name} {edge.actual.name}")

                if not alg:
                    if edge.actual in middle:
                        # 3rd case: Corner in top, edge in middle
                        self.debug(
                            f"Case: 3rd case: Corner in top, edge in middle: {corner.actual.name} {edge.actual.name}")
                        raise NotImplementedError("3rd case: Corner in top, edge in middle")

                    elif not corner.actual.get_face_edge(up).color == white:
                        # 4th case: Corner pointing outwards, edge in top layer
                        self.debug(
                            f"Case: 4th case: Corner pointing outwards, edge in top layer: {corner.actual.name} {edge.actual.name}")

                        if e is u_top:
                            if front.color == c.get_face_edge(front).color and right.color == e.get_face_edge(up).color:
                                # OK !!!
                                alg = U - F + U * 2 + F + U - F + U * 2 + F
                        else:
                            raise InternalSWError("4th case: Corner pointing outwards, edge in top layer")
                    else:
                        # 5th case: Corner pointing upwards, edge in top layer
                        self.debug(
                            f"Case: 5th case: Corner pointing upwards, edge in top layer: {corner.actual.name} {edge.actual.name}")

                        if e is u_bottom:
                            if e.get_face_edge(front).color == c_front_color == r_color:
                                # OK !!!
                                alg = (R + U + R.prime + U.prime) + U.prime + (R + U + R.prime + U.prime) + (R + U + R.prime)
                            elif e.get_face_edge(front) == f_color and c_front_color == r_color:
                                alg = (F.prime + U * 2 + F) + (U + F.prime + U.prime + F.prime)
                            else:
                                raise InternalSWError(
                                    "5th case: Corner pointing upwards, edge in top layer, unknown case")
                        else:
                            raise NotImplementedError("5th case: Corner pointing upwards, edge in top layer")





            else:
                # corner at bottom
                # if we reach here then corner is in position
                assert corner.in_position

                if edge.actual.on_face(up):
                    # 2nd case: Corner in bottom, edge in top layer
                    self.debug(
                        f"Case: 2nd case: Corner in bottom, edge in top layer: {corner.actual.name} {edge.actual.name}")
                    if corner.actual.match_faces:
                        if edge.actual is u_bottom:
                            # (U R U' R') (U' F' U F)
                            alg = (U + R - U - R) + (-U - F + U + F)
                        elif edge.actual is u_right:
                            # (U' F' U F) (U R U' R')
                            alg = (-U - F + U + F) + (U + R - U - R)
                    elif corner.actual.get_face_edge(cube.front).color == cube.right.color:
                        if edge.actual is u_bottom:
                            # (F' U F) (U' F' U F)
                            alg = (-F + U + F) + (-U - F + U + F)
                        elif edge.actual is u_right:
                            # (R U R') (U' R U R')
                            alg = (R + U - R) + (-U + R + U - R)
                    elif corner.actual.get_face_edge(cube.front).color == cube.right.color:
                        if edge.actual is u_bottom:
                            # (F' U' F) (U F' U' F)
                            alg = (-F - U + F) + (U - F - U + F)
                        elif edge.actual is u_right:
                            # (R U' R') (U R U' R')
                            alg = (R - U - R) + (U + R - U - R)
                elif edge.actual in middle:
                    # 6th case: Corner in bottom, edge in middle
                    raise NotImplementedError("6th case: Corner in bottom, edge in middle")
                else:
                    raise InternalSWError("No such a case, corner at bottom, not on top nor on middle")

            if alg is None:
                raise InternalSWError(f"Unknown case, corner is {corner.actual.name}, edge is {edge.actual.name}")

            self.debug(f"Case corner is {corner.actual.name}, edge is {edge.actual.name}, Running alg:{alg}")
            self.op.play(alg)
            assert corner.match
            assert edge.match

            return True
