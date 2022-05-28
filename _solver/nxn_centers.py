from collections.abc import Iterator
from typing import Tuple

import algs
from _solver.base_solver import SolverElement, ISolver
from _solver.common_op import CommonOp
from algs import Algs
from app_exceptions import InternalSWError
from cube_face import Face
from cube_queries import CubeQueries
from elements import FaceName, Color, CenterSlice


def use(_):
    pass


_status = None


class NxNCenters(SolverElement):

    def __init__(self, slv: ISolver) -> None:
        super().__init__(slv)

    def debug(self, *args):
        super().debug("NxX Centers:", args)

    @property
    def cmn(self) -> CommonOp:
        return self._cmn

    def _is_solved(self):

        # todo: check BOY
        return all((f.center.is3x3 for f in self.cube.faces))

    def solved(self) -> bool:
        """

        :return: if all centers have uniqe colors and it is a boy
        """

        return self._is_solved()

    def solve(self):

        if self._is_solved():
            return  # avoid rotating cube

        cube = self.cube
        n_slices = cube.n_slices

        # currently supports only odd
        assert n_slices % 2

        work_done = True
        while True:
            work_done = False
            for f in self.cube.faces:
                # we must trace faces, because they are moved by algorith
                # we need to locate the face by original_color, b ut on odd cube, the color is of the center
                _f: Face = CubeQueries.find_face(self.cube, lambda _x: _x.original_color == f.original_color)
                if self._do_center(_f, _f.color):
                    work_done = True
            if not work_done:
                break

    def _do_center(self, face: Face, color: Color) -> bool:

        """

        :param face:
        :param color:
        :return: if nay work was done
        """

        if self._is_face_solved(face, color):
            self.debug(f"Face is already done {face}")
            return False

        cmn = self.cmn

        self.debug(f"Working on face {face}")

        missing = self.count_missing(face, color)
        on_back = self.count_color_on_face(face.opposite, color)

        if missing == on_back:
            self.debug(f"On face {face}, required color is {color}, all {missing} missing are no opposite")
            return False

        cmn.bring_face_front(face)

        cube = self.cube

        # we loop bringing all adjusted faces up

        work_done = False

        for _ in range(4):  # 4 faces
            # need to optimize ,maybe no sources on this face

            if self._do_center_from_face(face, color, cube.up):
                work_done = True

            if self._is_face_solved(face, color):
                break

            self._bring_face_up_preserve_Front(cube.left)

        return work_done

    def _do_center_from_face(self, face: Face, color: Color, source_face: Face) -> bool:

        """
        The sources are on source_face !!!
        The target face is on front !!!
        :param face:
        :param color:
        :param source_face:
        :return:
        """

        cube = self.cube

        assert source_face in [cube.up, cube.back]

        n = cube.n_slices

        center = face.center

        work_done = False

        for r in range(0, n):  # 5: 3..4

            for j in range(n):
                cs: CenterSlice = center.get_center_slice((r, j))

                if cs.color != color:
                    self.debug(f"Need to fix slice {r}, {j}, {cs.color} to {color}")

                    if self._fix_center_slice(cs, color, source_face):
                        work_done = True

        return work_done

    def _fix_center_slice(self, cs: CenterSlice, required_color, source_face: Face) -> bool:
        """
        Assume center slice is in front
        this is not optimized because it rotates faces
        :param cs:
        :return:
        """

        r, j = cs.index
        self.debug(f"Fixing slice {r}, {j}, {cs.color} --> {required_color}")

        source = self._find_matching_slice(source_face, r, j, required_color)

        if source:
            self.debug(f"  Found matching piece {source} on {source.face}")
            self._fix_center_slice_from_source(cs, required_color, source)
            return True
        else:
            return False

    def _fix_center_slice_from_source(self, cs: CenterSlice, required_color, source: CenterSlice):

        # before the rotation
        assert required_color == source.color

        self._bring_face_up_preserve_Front(source.face)

        # Because it was moved, index might be changed
        r, c = cs.index

        with self.w_slice_annotate(cs):
            up = self.cube.up
            new_location_source = self._find_matching_slice(up, r, c, required_color)
            assert new_location_source
            source = new_location_source
            assert required_color == source.color

            self.debug(f" Source {source} is now on {source.face.name} {source.index}")

            # optimize it, can be done by less rotation, more math
            for _ in range(0, 4):
                if up.center.get_center_slice((r, c)).color == required_color:  # maybe it will find other :)
                    break
                self.op.op(Algs.U)

            source_slice = up.center.get_center_slice((r, c))
            assert source_slice.color == required_color

            with self.w_slice_annotate(source_slice):

                self.debug(f" On  {source.face.name} , {(r, c)} is {source_slice.color}")

                # this can be done, because Front and UP have the same coordinates system !!!

                inv = self.cube.inv

                on_front_rotate: algs.Alg

                # assume we rotate F clockwise
                rr, cc = self.rotate_point_clockwise(r, c)

                # new cc mus not be same as c !!!
                if c == cc:
                    on_front_rotate = Algs.F.prime
                    rr, cc = self.rotate_point_counterclockwise(r, c)
                    if cc == c:
                        print("xxx")
                    assert cc != c
                else:
                    # clockwise is OK
                    on_front_rotate = Algs.F

                # center indexes are in opposite direction of R
                #   index is from left to right, R is from right to left
                R1 = Algs.M[inv(c) + 1:inv(c) + 1]
                R2 = Algs.M[inv(cc) + 1:inv(cc) + 1]

                self.debug(f"Doing communicator on {(r, c)} using second column {cc}, rotating {on_front_rotate}")

                _algs = [R1.prime,
                         on_front_rotate,
                         R2.prime,
                         on_front_rotate.prime,
                         R1,
                         on_front_rotate,
                         R2,
                         on_front_rotate.prime]

                for a in _algs:
                    self.op.op(a)  # so I can debug

                #       raise RuntimeError("Stopped")

    def _is_face_solved(self, face: Face, color: Color) -> bool:

        x = face.center.is3x3
        slice__color = face.center.get_center_slice((0, 0)).color

        return x and slice__color == color

    def _bring_face_up_preserve_Front(self, face):

        if face.name == FaceName.U:
            return

        if face.name == FaceName.B:
            raise InternalSWError(f"{face.name} is not supported")

        self.debug(f"Need to bring {face} to up")

        # rotate back with all slices clockwise
        rotate = Algs.B[1:self.cube.n_slices + 1]

        match face.name:

            case FaceName.B:
                raise InternalSWError(f"{face.name} is not supported")

            case FaceName.L:
                # todo open range should be supported by slicing
                self.op.op(rotate.prime)

            case FaceName.D:
                # todo open range should be supported by slicing
                self.op.op(rotate.prime * 2)

            case FaceName.R:
                # todo open range should be supported by slicing
                self.op.op(rotate)

            case _:
                raise InternalSWError(f" Unknown face {face.name}")

    def _find_matching_slice(self, f: Face, r: int, c: int, required_color: Color) -> CenterSlice | None:

        for i in self._get_four_center_points(r, c):

            cs = f.center.get_center_slice(i)

            if cs.color == required_color:
                return cs

        return None

    def _get_four_center_points(self, r, c) -> Iterator[Tuple[int, int]]:

        inv = self.cube.inv

        for _ in range(4):
            yield r, c
            (r, c) = (c, inv(r))

    def rotate_point_clockwise(self, row: int, column: int) -> Tuple[int, int]:
        return self.cube.inv(column), row

    def rotate_point_counterclockwise(self, row: int, column: int) -> Tuple[int, int]:
        return column, self.cube.inv(row)

    def count_missing(self, face: Face, color: Color) -> int:
        n = 0

        for s in face.center.all_slices:
            if s.color != color:
                n += 1
        return n

    def count_color_on_face(self, face: Face, color: Color) -> int:
        n = 0

        for s in face.center.all_slices:
            if s.color == color:
                n += 1
        return n
