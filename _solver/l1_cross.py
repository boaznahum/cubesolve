from typing import Sequence

import config
import viewer
from _solver.base_solver import SolverElement, ISolver
from _solver.common_op import CommonOp
from algs.algs import Algs, Alg
from model.cube import Cube
from model.cube_face import Face
from model.elements import FaceName, Edge, PartColorsID, PartEdge, Part


def use(_):
    pass


_status = None


class L1Cross(SolverElement):

    def __init__(self, slv: ISolver) -> None:
        super().__init__(slv)

    @property
    def cmn(self) -> CommonOp:
        return self._cmn

    def _is_cross(self):
        return Part.all_match_faces(self.white_face.edges)

    def is_cross(self) -> bool:
        """

        :return: true if all edges matches ignoring cross orientation.
        so you must call solve even if this return true
        """

        wf: Face = self.white_face
        return self.cmn.rotate_and_check(wf, self._is_cross) >= 0

    def solve_l0_cross(self):

        if self._is_cross():  #
            return  # avoid rotating cube

        # before rotating
        n = self.cmn.rotate_and_check(self.white_face, self._is_cross)
        if n >= 0:
            if n > 0:
                # the query solves by rotate  n, so we need
                self.op.op(self.cmn.face_rotate(self.white_face) * n)
            return

        self._bring_white_up()

        self._do_cross()

    def _bring_white_up(self):

        self.cmn.bring_face_up(self.white_face)

    def __print_cross_status(self):

        return

        # noinspection PyUnreachableCode
        wf = self.white_face
        es: Sequence[Edge] = wf.edges
        color_codes = [e.colors_id_by_pos for e in es]
        status = [self.cube.find_edge_by_color(c).match_faces for c in color_codes]

        print("Cross Status:", status)

        global _status
        _status = status

        return status

    def _do_cross(self):

        wf: Face = self.white_face
        assert wf.name == FaceName.U

        wf: Face = self.white_face

        color_codes: Sequence[PartColorsID] = Part.parts_id_by_pos(wf.edges)
        for color_id in color_codes:
            st = self.__print_cross_status()
            use(st)
            # we can't use edge, alg change them
            self._fix_edge(wf, color_id)
            st = self.__print_cross_status()
            use(st)
            # assert e.match_faces

    def _fix_edge(self, wf: Face, target_colors_id: PartColorsID):
        with self.w_annotate(
                (target_colors_id, False),
                (target_colors_id, True)
        ):
            self.__fix_edge(wf, target_colors_id)

    def __fix_edge(self, wf: Face, target_colors_id: PartColorsID):
        """
        Bring edge to correct place in the cross
        :param wf:
        :param target_colors_id: we use color code because this alg move edges
        :return:
        """

        cube: Cube = self.cube

        if config.PRINT_CUBE_AS_TEXT_DURING_SOLVE:
            def _debug():
                viewer.plot(cube)
        else:
            def _debug():
                pass

        _debug()

        target_edge: Edge = cube.find_edge_by_pos_colors(target_colors_id)

        if target_edge.match_faces:
            self.debug("L1-X C1.0", target_edge, "is on place")
            return

        assert wf.name == FaceName.U

        from .common_op import CommonOp  # type: ignore
        cmn: CommonOp = self.cmn

        # the required colors
        target_colors_id = target_edge.colors_id_by_pos

        source_edge: Edge = cube.find_edge_by_color(target_colors_id)

        self.debug("L1-X", "Need to bring ", source_edge, "to", target_edge)

        # Is it on white face
        edge_on_face: PartEdge | None = source_edge.on_face(wf)
        if edge_on_face:
            self.debug("L1-X. C1", source_edge, "is on required", wf, "@", edge_on_face)

            if edge_on_face.face is wf:
                self.debug("??L1-X. C1.1", source_edge, "is on required", wf, "@", edge_on_face, "color matches")
            else:
                self.debug("??L1-X. C1.2", source_edge, "is on required", wf, "@", edge_on_face, "color doesn't match")

            # Now bring it to adjusted face
            if wf.edge_right is source_edge:
                self.op.op(Algs.R)  # move it R-B
            elif wf.edge_bottom is source_edge:
                self.op.op(Algs.F)  # move it F-R
            elif wf.edge_left is source_edge:
                self.op.op(Algs.L)  # move it F-L
            elif wf.edge_top is source_edge:
                self.op.op(Algs.B)  # move it R-B
            else:
                raise ValueError(f"{source_edge} is not U-R, U-F, U-L, nor U-B")

            _debug()

            # continue with C2
            source_edge = cube.find_edge_by_color(target_colors_id)

        adjusted_face: Face
        target_face: Face
        for adjusted_face in wf.adjusted_faces():

            if adjusted_face.is_left_or_right(source_edge):
                self.debug("L0X. C2", source_edge, "is left/right on adjusted ", adjusted_face)

                # target_edge is where we want to bring
                target_face = target_edge.get_other_face(wf)

                st = self.__print_cross_status()
                use(st)

                # bring target face to front by rotating all cube
                cmn.bring_face_to_front_by_y_rotate(target_face)
                assert target_colors_id == cube.front.edge_top.colors_id_by_pos

                st = self.__print_cross_status()
                use(st)

                source_edge = cube.find_edge_by_color(target_colors_id)
                e_alg: Alg = cmn.bring_edge_to_front_by_e_rotate(source_edge)  # type: ignore

                st = self.__print_cross_status()
                use(st)

                # was moved
                source_edge = cube.find_edge_by_color(target_colors_id)
                # now source is on front so the target , and the target doesn't match, so we can rotate

                if cube.front.edge_right is source_edge:
                    self.op.op(Algs.F)
                    st = self.__print_cross_status()
                    use(st)
                elif cube.front.edge_left is source_edge:
                    self.op.op(-Algs.F)
                    st = self.__print_cross_status()
                    use(st)
                else:
                    raise ValueError(f"{source_edge} is not L-F nor R-F")

                if e_alg:
                    # bring centers to match the cross
                    self.op.op(-e_alg)
                st = self.__print_cross_status()
                use(st)

                # now it is on bottom, so we can continue with case C3
                return self._fix_edge(wf, target_colors_id)

        bottom: Face = wf.opposite
        self.debug("L0X. C3", source_edge, "is on bottom", bottom)

        # target_edge is where we want to bring
        target_face = target_edge.get_other_face(wf)

        # bring target face to front by rotating all cube
        cmn.bring_face_to_front_by_y_rotate(target_face)
        assert target_colors_id == cube.front.edge_top.colors_id_by_pos

        # it was moved
        source_edge = cube.find_edge_by_color(target_colors_id)
        cmn.bring_bottom_edge_to_front_by_d_rotate(source_edge)
        # make sure the source matches
        assert target_colors_id == cube.front.edge_bottom.colors_id_by_color

        # it was moved
        source_edge = cube.find_edge_by_color(target_colors_id)
        # now target and source on front top/bottom
        white_color = wf.color
        source_face_on_edge = source_edge.face_of_actual_color(white_color)

        if source_face_on_edge.is_down:
            self.debug("L0X. C3.1", source_edge, "is on bottom", source_face_on_edge)
            return self.op.op(Algs.F * 2)
        else:
            assert source_face_on_edge.is_front
            self.debug("L0X. C3.2", source_edge, "is on front", source_face_on_edge)
            return self.op.op(-Algs.F + - Algs.R + -Algs.D + Algs.R + Algs.F * 2)
