from typing import Sequence

from cube.domain.algs import Alg, Algs
from cube.domain.model import Color, Edge, Part, PartColorsID
from cube.domain.model.Face import Face
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.common.SolverElement import SolverElement
from cube.domain.solver.common.Tracker import EdgeTracker


class L2(SolverElement):
    __slots__: list[str] = []

    def __init__(self, slv: BaseSolver) -> None:
        super().__init__(slv)


    @property
    def l2_edges(self) -> Sequence[Edge]:
        return self.cmn.l2_edges()


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

        with self.ann.annotate(h1="Doing L2"):
            self.cmn.bring_face_up(self.white_face.opposite)

            self._do_edges()

    def _do_edges(self) -> None:

        # we use codes because maybe position will be changed during the algorithm
        edges__codes: Sequence[PartColorsID] = Part.parts_id_by_pos(self.l2_edges)

        for code in edges__codes:
            self._solve_edge(code)

    def _solve_edge(self, edge_id: PartColorsID):

        # color tracker
        st: EdgeTracker = EdgeTracker.of_color(self, edge_id)

        if st.match:
            # because we have cross and L1, so if it matches then it is in position
            self.debug(f"L2-C0. {st.position} matches")
            return

        with self.ann.annotate((edge_id, AnnWhat.Moved), (self.cube.front.edge_top, AnnWhat.FixedPosition),
                               h2=lambda: f"Bring {st.actual.name_n_colors} to FU"):
            self.__solve_edge(st)

    def __solve_edge(self, st: EdgeTracker):
        cube = self.cube
        up: Face = self.cube.up
        down: Face = up.opposite

        if st.actual.on_face(down):
            print()

        assert not st.actual.on_face(down)

        if not st.actual.on_face(up):
            self.debug(f"L2-C1. source {st.actual} is not on top")

            self._bring_edge_to_front_right(st.actual)

            assert self.cube.front.edge_right is st.actual

            self.op.play(self._ur_alg)

            assert st.actual.on_face(up)

        else:
            self.debug(f"L2-C2. source {st.actual} is on top")

        # now source is no top

        # find the face of source that is not on top
        target_face_color: Color = st.actual.get_other_face_edge(up).color
        self._bring_face_to_front(target_face_color)
        assert self.cube.front.color == st.actual.get_other_face_edge(up).color

        self._bring_edge_to_front_up(st.actual)
        assert self.cube.front.edge_top is st.actual

        assert st.position.on_face(cube.front) and (st.position.on_face(cube.right) or st.position.on_face(cube.left))

        if st.position.on_face(cube.right):
            alg = self._ur_alg  # U R U' R' U' F' U F
        else:
            alg = self._ul_alg

        self.op.play(alg)

        assert st.match

    @property
    def _ur_alg(self) -> Alg:
        return Algs.alg(None, Algs.U, Algs.R, Algs.U.prime, Algs.R.prime,
                        Algs.U.prime, Algs.F.prime, Algs.U, Algs.F)

    @property
    def _ul_alg(self) -> Alg:
        return Algs.alg(None,
                        Algs.U.prime + Algs.L.prime + Algs.U + Algs.L +
                        Algs.U + Algs.F + Algs.U.prime + Algs.F.prime)

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
            return self.op.play(Algs.Y.prime)

        back: Face = self.cube.back

        if back.edge_left is e:
            return self.op.play(Algs.Y)

        if back.edge_right is e:
            return self.op.play(Algs.Y * 2)

        raise ValueError(f"Edge {e} is not  middle(over U) slice")

    def _bring_face_to_front(self, face_color):

        cube = self.cube

        if cube.front.color == face_color:
            return

        if cube.right.color == face_color:
            return self.op.play(Algs.Y)

        if cube.left.color == face_color:
            return self.op.play(Algs.Y.prime)

        if cube.back.color == face_color:
            return self.op.play(Algs.Y * 2)

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
            return self.op.play(Algs.U.prime)

        if up.edge_right is e:
            return self.op.play(Algs.U)

        if up.edge_top is e:
            return self.op.play(Algs.U * 2)

        raise ValueError(f"Edge {e} is not on {up}")
