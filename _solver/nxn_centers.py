from collections.abc import Iterator, Sequence
from typing import Tuple, Callable

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

FaceTracker = Callable[[], Face]


class FaceLoc:

    def __init__(self, color: Color, tracker: FaceTracker) -> None:
        super().__init__()
        self._tracker = tracker
        self._color = color

    @property
    def face(self):
        return self._tracker()

    @property
    def color(self):
        return self._color


class NxNCenters(SolverElement):
    work_on_b: bool = True

    D_LEVEL = 1

    def __init__(self, slv: ISolver) -> None:
        super().__init__(slv)

    def debug(self, *args, level=3):
        if level <= NxNCenters.D_LEVEL:
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

        f1: FaceLoc = self._track_no_1()

        f2 = self._track_opposite(f1)

        self._do_faces([f1, f2])

        assert f1.face.center.is3x3
        assert f2.face.center.is3x3

        # now colors of f1/f2 can't be on 4 that left, so we can choose any one
        f3 = self._track_no_3([f1.face, f2.face])
        f4 = self._track_opposite(f3)

        self._do_faces([f3, f4])
        assert f3.face.center.is3x3
        assert f4.face.center.is3x3

        f5, f6 = self._track_two_last([f1.face, f2.face, f3.face, f4.face])
        self._do_faces([f5, f6])
        assert f5.face.center.is3x3
        assert f6.face.center.is3x3

        assert self._is_solved()




    def _do_faces(self, faces):
        while True:
            work_done = False
            for f in faces:
                # we must trace faces, because they are moved by algorith
                # we need to locate the face by original_color, b ut on odd cube, the color is of the center
                if self._do_center(f):
                    work_done = True
            if NxNCenters.work_on_b or not work_done:
                break

    def _track_no_1(self) -> FaceLoc:

        cube = self.cube
        if cube.n_slices % 2:
            return self._track_odd(cube.front)
        else:
            return self._track_even(cube.front, (0, 0))

    def _track_no_3(self, two_first: Sequence[Face]) -> FaceLoc:

        cube = self.cube

        left = list({*cube.faces} - set(two_first))

        if cube.n_slices % 2:
            return self._track_odd(left[0])
        else:
            # can be any
            return self._track_even(left[0], (0, 0))

    def _track_two_last(self, four_first: Sequence[Face]) -> Tuple[FaceLoc, FaceLoc]:

        cube = self.cube

        left = list({*cube.faces} - set(four_first))

        assert cube.n_slices % 2
        if cube.n_slices % 2:
            f5: FaceLoc = self._track_odd(left[0])
            f6 = self._track_opposite(f5)

            return f5, f6

        else:
            # can be any
            return self._track_even(left[0], (0, 0))

    def _track_opposite(self, f: FaceLoc):

        f_color = f.color

        second_color=self.boy_opposite(f_color)

        def _pred() -> Face:

            _f : Face
            return CubeQueries.find_face(self.cube, lambda _f : _f.opposite is f.face)

        return FaceLoc(second_color, _pred)

    def _do_center(self, face_loc: FaceLoc) -> bool:

        if self._is_face_solved(face_loc.face, face_loc.color):
            self.debug(f"Face is already done {face_loc.face}",
                       level=1)
            return False

        self.debug(f"Need to work on {face_loc.face}",
                   level=1)

        work_done = self.__do_center(face_loc.face, face_loc.color)

        self.debug(f"After working on {face_loc.face} {work_done=}, "
                   f"solved={self._is_face_solved(face_loc.face, face_loc.color)}",
                   level=1)

        return work_done

    def _track_slice(self, f: Face, rc: Tuple[int, int]) -> FaceLoc:

        """
        Track as specific slice
        :param f:
        :return:
        """

        color = f.center.get_center_slice(rc).color

        def pred(_f: Face):
            return _f.center.get_center_slice(rc).color == color

        t: FaceTracker = lambda: CubeQueries.find_face(self.cube, pred)

        return FaceLoc(color, t)

    def _track_odd(self, f: Face) -> FaceLoc:

        n_slices = self.cube.n_slices
        return self._track_slice(f, (n_slices // 2, n_slices // 2))

    def _track_even(self, f: Face, rc: Tuple[int, int]) -> FaceLoc:

        return self._track_slice(f, rc)

    def __do_center(self, face: Face, color: Color) -> bool:

        """

        :param face:
        :param color:
        :return: if nay work was done
        """

        if self._is_face_solved(face, color):
            self.debug(f"Face is already done {face}",
                   level=1)
            return False

        cmn = self.cmn

        self.debug(f"Working on face {face}",
                   level=1)

        # missing = self.count_missing(face, color)
        # on_back = self.count_color_on_face(face.opposite, color)
        #
        # if missing == on_back:
        #     self.debug(f"On face {face}, required color is {color}, all {missing} missing are no opposite")
        #     return False

        cmn.bring_face_front(face)

        cube = self.cube

        # we loop bringing all adjusted faces up

        work_done = False

        for _ in range(3):  # 3 faces
            # need to optimize ,maybe no sources on this face

            # don't use face - it was moved !!!
            if self._do_center_from_face(cube.front, color, cube.up):
                work_done = True

            if self._is_face_solved(face, color):
                return work_done

            self._bring_face_up_preserve_front(cube.left)

        # on the last face
        # don't use face - it was moved !!!
        if self._do_center_from_face(cube.front, color, cube.up):
            work_done = True

        if self._is_face_solved(face, color):
            return work_done

        if NxNCenters.work_on_b:
            # now from back
            # don't use face - it was moved !!!
            if self._do_center_from_face(cube.front, color, cube.back):
                work_done = True

        return work_done

    def _do_center_from_face(self, face: Face, color: Color, source_face: Face) -> bool:

        """
        The sources are on source_face !!! source face is in its location up /back
        The target face is on front !!!
        :param face:
        :param color:
        :param source_face:
        :return:
        """

        cube = self.cube

        assert face is cube.front
        assert source_face in [cube.up, cube.back]

        if self.count_color_on_face(source_face, color) == 0:
            return False  # nothing can be done here

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

        if not work_done:
            self.debug(f"Internal error, no work was done on face {face} required color {color}, "
                       f"but source face  {source_face} contains {self.count_color_on_face(source_face, color)}")
            for r in range(n):
                for c in range(n):
                    if center.get_center_slice((r, c)).color != color:
                        print(f"Missing: {(r, c)}  {[*self._get_four_center_points(r, c)]}")
            for r in range(n):
                for c in range(n):
                    if source_face.center.get_center_slice((r, c)).color == color:
                        print(f"Found on {source_face}: {(r, c)}  {source_face.center.get_center_slice((r, c))}")

            raise InternalSWError("See error in log")

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

        source_face = source.face

        cube = self.cube
        is_back = source_face is cube.back

        rotate_source: algs.Alg
        target_to_source_conversion: int
        if is_back:
            rotate_source = Algs.B
        else:
            rotate_source = Algs.U

        # Because it was moved, index might be changed
        r, c = cs.index

        inv = cube.inv

        # with self.w_slice_annotate(cs):
        if True:
            new_location_source = self._find_matching_slice(source_face, r, c, required_color)
            assert new_location_source
            source = new_location_source
            assert required_color == source.color

            # the logic here is hard code of the logic in slice rotate
            # it will be broken if cube layout is changed
            # here we assume we work on F, and UP has same coord system as F, and
            # back is mirrored in both direction
            if is_back:
                source_index = (inv(r), inv(c))
            else:
                source_index = (r, c)

            self.debug(f" Source {source} is now on {source.face.name} {source.index} , but assume {source_index}")

            # optimize it, can be done by less rotation, more math
            for _ in range(0, 4):
                if source_face.center.get_center_slice(
                        source_index).color == required_color:  # maybe it will find other :)
                    break
                self.op.op(rotate_source)

            source_slice = source_face.center.get_center_slice(source_index)
            assert source_slice.color == required_color

            if True:
                # with self.w_slice_annotate(source_slice):

                self.debug(f" On  {source.face.name} , {(r, c)} is {source_slice.color}")

                # this can be done, because Front and UP have the same coordinates system !!!

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
                rotate_on_cell = Algs.M[inv(c) + 1:inv(c) + 1]
                rotate_on_second = Algs.M[inv(cc) + 1:inv(cc) + 1]

                if is_back:
                    r1_mul = 2
                else:
                    r1_mul = 1

                self.debug(f"Doing communicator on {(r, c)} using second column {cc}, rotating {on_front_rotate}")

                _algs = [rotate_on_cell.prime * r1_mul,
                         on_front_rotate,
                         rotate_on_second.prime * r1_mul,
                         on_front_rotate.prime,
                         rotate_on_cell * r1_mul,
                         on_front_rotate,
                         rotate_on_second * r1_mul,
                         on_front_rotate.prime]

                for a in _algs:
                    self.op.op(a)  # so I can debug

                if cs.color != required_color:
                    print()
                assert cs.color == required_color, f"Color was not solved, {(r, c)} {cs} " \
                                                   f"color is {cs.color}, {required_color=}"

    @staticmethod
    def _is_face_solved(face: Face, color: Color) -> bool:

        x = face.center.is3x3
        slice__color = face.center.get_center_slice((0, 0)).color

        return x and slice__color == color

    def _bring_face_up_preserve_front(self, face):

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

    def rotate_point_clockwise(self, row: int, column: int, n=1) -> Tuple[int, int]:
        for i in range(0, n % 4):
            row, column = self.cube.inv(column), row

        return row, column

    def rotate_point_counterclockwise(self, row: int, column: int) -> Tuple[int, int]:
        return column, self.cube.inv(row)

    @staticmethod
    def count_missing(face: Face, color: Color) -> int:
        n = 0

        for s in face.center.all_slices:
            if s.color != color:
                n += 1
        return n

    @staticmethod
    def count_color_on_face(face: Face, color: Color) -> int:
        n = 0

        for s in face.center.all_slices:
            if s.color == color:
                n += 1
        return n

    def boy_opposite(self, color: Color) -> Color:

        f: Face = CubeQueries.find_face(self.cube, lambda _f: _f.original_color == color)

        assert f

        # original colors are BOY
        return f.opposite.original_color



