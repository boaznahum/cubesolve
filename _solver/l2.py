from typing import Sequence

from _solver.base_solver import SolverElement, ISolver
from _solver.common_op import CommonOp
from algs.algs import Algs, Alg
from model.cube_face import Face
from model.elements import PartColorsID, Part, Edge, Color


def use(_):
    pass


class L2(SolverElement):
    __slots__ = []

    def __init__(self, slv: ISolver) -> None:
        super().__init__(slv)

    @property
    def cmn(self) -> CommonOp:
        return self._cmn

    @property
    def l2_edges(self) -> Sequence[Edge]:

        edges: list[Edge] = []

        wf: Face = self.white_face
        d: Face = wf.opposite

        for f in self.white_face.adjusted_faces():
            for e in f.edges:
                # all edges that do not touch up and down faces
                if not e.on_face(wf) and not e.on_face(d):
                    if e not in edges:  # by id ?
                        edges.append(e)
                        if len(edges) == 4:  # optimize
                            return edges

        return edges

    def solved(self) -> bool:
        """
        :return: true if 4 middle slice match faces, don't try to rotate
        """

        edges = self.l2_edges

        return Part.all_match_faces(edges)

        # wf: Face = self.white_face
        #
        # adjusted: Sequence[Face] = wf.adjusted_faces()
        #
        # def pred(): return Part.all_match_faces(wf.corners)
        #
        # return self.cmn.rotate_and_check(wf, pred) >= 0

    def solve(self):
        """
        Must be called after L1 is solved
        :return:
        """

        if self.solved():
            return  # avoid rotating cube

        self.cmn.bring_face_up(self.white_face.opposite)

        self._do_edges()

    def _do_edges(self):

        # we use codes because maybe position will be changed during the algorithm
        edges__codes: Sequence[PartColorsID] = Part.parts_id_by_pos(self.l2_edges)

        for code in edges__codes:
            self._solve_edge(code)

    def _solve_edge(self, edge_id: PartColorsID):

        _source_corner: Edge | None = None

        _target_corner: Edge | None = None

        # source edge
        def se() -> Edge:
            nonlocal _source_corner
            if not _source_corner or _source_corner.colors_id_by_color != edge_id:
                _source_corner = self.cube.find_edge_by_color(edge_id)
            return _source_corner

        # target edge
        def te() -> Edge:
            nonlocal _target_corner
            if not _target_corner or _target_corner.colors_id_by_pos != edge_id:
                _target_corner = self.cube.find_edge_by_pos_colors(edge_id)
            return _target_corner

        if se().match_faces:
            # because we have cross and L1, so if it matches then it is in position
            self.debug(f"L2-C0. {te()} matches")
            return

        cube = self.cube
        up: Face = self.cube.up
        down: Face = up.opposite

        if se().on_face(down):
            print()

        assert not se().on_face(down)

        if not se().on_face(up):
            self.debug(f"L2-C1. source {se()} is not on top")

            self._bring_edge_to_front_right(se())

            assert self.cube.front.edge_right is se()

            # replace it with something on top  todo: optimize, try to bring yellow edge
            self.op.op(self._ur_alg)

            assert se().on_face(up)

        else:
            self.debug(f"L2-C2. source {se()} is on top")

        # now source is no top

        # find the face of source that is not on top
        target_face_color: Color = se().get_other_face_edge(up).color
        self._bring_face_to_front(target_face_color)
        assert self.cube.front.color == se().get_other_face_edge(up).color

        self._bring_edge_to_front_up(se())
        assert self.cube.front.edge_top is se()

        assert te().on_face(cube.front) and (te().on_face(cube.right) or te().on_face(cube.left))

        _te = te()  # don't track
        _se = se()  # don't track
        _te_id = _te.colors_id_by_color
        _se_id = _se.colors_id_by_color

        with self.w_annotate((_se, False), (_te, True)):

            if te().on_face(cube.right):
                self.op.op(self._ur_alg)
            else:
                self.op.op(self._ul_alg)

        assert se().match_faces

    @property
    def _ur_alg(self) -> Alg:
        return Algs.alg("L2-UR", Algs.U, Algs.R, Algs.U.prime, Algs.R.prime, Algs.U.prime, Algs.F.prime, Algs.U, Algs.F)

    @property
    def _ul_alg(self) -> Alg:
        return Algs.alg("L2-UL",
                        Algs.U.prime + Algs.L.prime + Algs.U + Algs.L + Algs.U + Algs.F + Algs.U.prime + Algs.F.prime)

    def _bring_edge_to_front_right(self, e: Edge):
        """
        Whole movement
        :param e:
        :return:
        """

        front: Face = self.cube.front
        if front.edge_right is e:
            return

        if front.edge_left is e:
            return self.op.op(Algs.Y.prime)

        back: Face = self.cube.back

        if back.edge_left is e:
            return self.op.op(Algs.Y)

        if back.edge_right is e:
            return self.op.op(Algs.Y * 2)

        raise ValueError(f"Edge {e} is not  middle(over U) slice")

    def _bring_face_to_front(self, face_color):

        cube = self.cube

        if cube.front.color == face_color:
            return

        if cube.right.color == face_color:
            return self.op.op(Algs.Y)

        if cube.left.color == face_color:
            return self.op.op(Algs.Y.prime)

        if cube.back.color == face_color:
            return self.op.op(Algs.Y * 2)

        raise ValueError(f"Color {face_color} is not on F/R/L/B")

    def _bring_edge_to_front_up(self, e: Edge):
        """
        U Movement, edge must be on up
        :param  e:
        :return:
        """

        up: Face = self.cube.up

        if up.edge_bottom is e:
            return

        if up.edge_left is e:
            return self.op.op(Algs.U.prime)

        if up.edge_right is e:
            return self.op.op(Algs.U)

        if up.edge_top is e:
            return self.op.op(Algs.U * 2)

        raise ValueError(f"Edge {e} is not on {up}")
