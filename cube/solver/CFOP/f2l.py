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

            corner: Corner = self.cube.front.corner_bottom_right
            edge: Edge = self.cube.front.edge_right

            # rotate

            for _ in range(4):
                n = self.cmn.rotate_and_check(Algs.Y, lambda: not (corner.match_faces and edge.match_faces))

                # all ok, so must be  solved
                if n < 0:
                    assert self.solved()
                    return

                self._do_corner_edge()

    def _do_corner_edge(self) -> bool:

        # assume white is at bottom
        cube = self.cube

        # the corner and edge we need to fix
        corner: CornerTracker = CornerTracker.of_position(cube.front.corner_bottom_right)
        edge: EdgeTracker = EdgeTracker.of_position(cube.front.edge_right)

        with self.cmn.annotate(([corner.actual, edge.position], AnnWhat.Moved),
                               ([edge.actual, edge.position], AnnWhat.FixedPosition)):

            self.debug(f"Working on {corner.position} {edge.position}")

            up: Face = cube.up
            front: Face = cube.front
            back: Face = cube.back


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

            f = Algs.F
            r = Algs.R
            u = Algs.U

            u_bottom = up.edge_bottom
            u_right = up.edge_right
            middle = [front.edge_left, front.edge_right, back.edge_right, back.edge_left]

            alg: Alg | None = None

            # https://ruwix.com/the-rubiks-cube/advanced-cfop-fridrich/first-two-layers-f2l/
            if corner_on_top:
                # if we reach here, then corner is up.corner_bottom_right

                if edge.actual.on_face(up):
                    # 1st: Easy cases: edge at top
                    self.debug(f"Case:1st: Easy cases: edge at top: {corner.actual.name} {edge.actual.name}")
                    if edge.actual is up.edge_top:
                        alg = r + u - r
                    elif edge.actual is up.edge_left:
                        alg = -f - u + f
                    elif edge.actual is u_bottom:
                        alg = -u - f + u + f
                    elif edge.actual is u_right:
                        alg = u + r - u - r

                if edge.actual in middle:
                    # 3rd case: Corner in top, edge in middle
                    self.debug(f"Case: 3rd case: Corner in top, edge in middle: {corner.actual.name} {edge.actual.name}")
                    raise NotImplementedError("3rd case: Corner in top, edge in middle")

                elif not corner.actual.match_face(up):
                    # 4th case: Corner pointing outwards, edge in top layer
                    self.debug(f"Case: 4th case: Corner pointing outwards, edge in top layer: {corner.actual.name} {edge.actual.name}")
                    raise InternalSWError("4th case: Corner pointing outwards, edge in top layer")
                else:
                    # 5th case: Corner pointing upwards, edge in top layer
                    self.debug(f"Case: 5th case: Corner pointing upwards, edge in top layer: {corner.actual.name} {edge.actual.name}")
                    raise InternalSWError("5th case: Corner pointing upwards, edge in top layer")





            else:
                # corner at bottom
                # if we reach here then corner is in position
                assert corner.in_position

                if edge.actual.on_face(up):
                    # 2nd case: Corner in bottom, edge in top layer
                    self.debug(f"Case: 2nd case: Corner in bottom, edge in top layer: {corner.actual.name} {edge.actual.name}")
                    if corner.actual.match_faces:
                        if edge.actual is u_bottom:
                            # (U R U' R') (U' F' U F)
                            alg = (u + r - u - r) + (-u - f + u + f)
                        elif edge.actual is u_right:
                            # (U' F' U F) (U R U' R')
                            alg = (-u - f + u + f) + (u + r - u - r)
                    elif corner.actual.get_face_edge(cube.front).color == cube.right.color:
                        if edge.actual is u_bottom:
                            # (F' U F) (U' F' U F)
                            alg = (-f + u + f) + (-u - f + u + f)
                        elif edge.actual is u_right:
                            # (R U R') (U' R U R')
                            alg = (r + u - r) + (-u + r + u - r)
                    elif corner.actual.get_face_edge(cube.front).color == cube.right.color:
                        if edge.actual is u_bottom:
                            # (F' U' F) (U F' U' F)
                            alg = (-f - u + f) + (u - f - u + f)
                        elif edge.actual is u_right:
                            # (R U' R') (U R U' R')
                            alg = (r - u - r) + (u + r - u - r)
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
