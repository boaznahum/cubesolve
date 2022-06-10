from collections.abc import Iterator, Sequence
from typing import Tuple, Callable, Collection, Any

import config
from _solver.base_solver import SolverElement, ISolver
from _solver.common_op import CommonOp
from algs import algs
from algs.algs import Algs
from app_exceptions import InternalSWError
from model.cube import Cube
from model.cube_boy import CubeLayout, Color
from model.cube_face import Face
from model.cube_queries import CubeQueries, Pred
from model.elements import FaceName, Color, CenterSlice


def use(_):
    pass


_status = None

FaceTracker = Callable[[], Face]

IS_FIRST = "is_first"
TWO_LAST = "two last"

_tracer_unique_id: int = 0


class FaceLoc:

    def __init__(self, color: Color, tracker: FaceTracker) -> None:
        super().__init__()
        self._tracker = tracker
        self._color = color
        self._attributes: dict[Any, Any] = {}

    @property
    def face(self):
        return self._tracker()

    @property
    def color(self):
        return self._color

    def set_attribute(self, att: Any):
        self._attributes[att] = att

    def has_attribute(self, att: Any):
        return att in self._attributes


class NxNCenters(SolverElement):
    work_on_b: bool = True

    D_LEVEL = 3

    def __init__(self, slv: ISolver) -> None:
        super().__init__(slv)

    def debug(self, *args, level=3):
        if level <= NxNCenters.D_LEVEL:
            super().debug("NxX Centers:", args)

    @property
    def cmn(self) -> CommonOp:
        return self._cmn

    def _is_solved(self):
        return all((f.center.is3x3 for f in self.cube.faces)) and self.cube.is_boy

    def solved(self) -> bool:
        """

        :return: if all centers have unique colors, and it is a boy
        """

        return self._is_solved()

    def solve(self):

        if self._is_solved():
            return  # avoid rotating cube

        f1: FaceLoc = self._track_no_1()

        f1.set_attribute(IS_FIRST)

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

        f5, f6 = self._track_two_last([f1, f2, f3, f4])
        self._do_faces([f5, f6])
        assert f5.face.center.is3x3
        assert f6.face.center.is3x3

        f5.set_attribute(TWO_LAST)
        f6.set_attribute(TWO_LAST)

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
            f, c = self._find_face_with_max_colors()
            _slice = CubeQueries.find_slice_in_face_center(f, lambda s: s.color == c)
            assert _slice
            # todo: see bug _track_even
            return self._track_even(f, _slice.index)

    def _track_no_3(self, two_first: Sequence[Face]) -> FaceLoc:

        cube = self.cube

        left = list({*cube.faces} - set(two_first))

        if cube.n_slices % 2:
            return self._track_odd(left[0])
        else:
            # can be any
            return self._track_even(left[0], (0, 0))

    def _track_two_last(self, four_first: Sequence[FaceLoc]) -> Tuple[FaceLoc, FaceLoc]:

        cube = self.cube

        left_two_faces: list[Face] = list({*cube.faces} - {f.face for f in four_first})

        assert len(left_two_faces) == 2

        f5: Face = left_two_faces[0]

        if cube.n_slices % 2:
            f5_track: FaceLoc = self._track_odd(f5)
            f6_track = self._track_opposite(f5_track)

            return f5_track, f6_track

        else:
            colors: set[Color] = set((f.color for f in four_first))

            left_two_colors: set[Color] = set(self.cube.original_layout.colors()) - colors

            c1: Color = left_two_colors.pop()
            c2: Color = left_two_colors.pop()

            f6: Face = left_two_faces[1]

            try1 = {f.face.name: f.color for f in four_first}
            try1[f5.name] = c1
            try1[f6.name] = c2
            cl: CubeLayout = CubeLayout(False, try1)

            if not cl.same(self.cube.original_layout):
                f5, f6 = (f6, f5)
                try1 = {f.face.name: f.color for f in four_first}
                try1[f5.name] = c1
                try1[f6.name] = c2
                cl = CubeLayout(False, try1)
                assert cl.same(self.cube.original_layout)

                # now find in f5 a slice with this color

            def _s_pred(s: CenterSlice):
                return s.color == c1

            _slice = CubeQueries.find_slice_in_face_center(f5, _s_pred)

            if _slice is None:
                raise InternalSWError("Un supported case, f5, f6 are all 3x3 but with wrong color")
            # in rare case

            # see bug in _track_even
            f5_track = self._track_even(f5, _slice.index)
            f6_track = self._track_opposite(f5_track)

            return f5_track, f6_track

    def _track_opposite(self, f: FaceLoc):

        f_color = f.color

        second_color = self.boy_opposite(f_color)

        def _pred() -> Face:
            _f: Face
            return CubeQueries.find_face(self.cube, lambda _f: _f.opposite is f.face)

        return FaceLoc(second_color, _pred)

    def _do_center(self, face_loc: FaceLoc) -> bool:

        if self._is_face_solved(face_loc.face, face_loc.color):
            self.debug(f"Face is already done {face_loc.face}",
                       level=1)
            return False

        self.debug(f"Need to work on {face_loc.face}",
                   level=1)

        work_done = self.__do_center(face_loc)

        self.debug(f"After working on {face_loc.face} {work_done=}, "
                   f"solved={self._is_face_solved(face_loc.face, face_loc.color)}",
                   level=1)

        return work_done

    def _track_face(self, color: Color, pred: Pred[Face]) -> FaceLoc:

        t: FaceTracker = lambda: CubeQueries.find_face(self.cube, pred)

        return FaceLoc(color, t)

    def _track_odd(self, f: Face) -> FaceLoc:

        n_slices = self.cube.n_slices
        rc = (n_slices // 2, n_slices // 2)

        # only middle in odd, doesn't change index when moving from face to face

        #        return self._track_slice(f, rc)
        color = f.center.get_center_slice(rc).color

        def pred(_f: Face):
            return _f.center.get_center_slice(rc).color == color

        # actually it is bug, on even, when moving from face to face slice coordinate smay be changed
        t: FaceTracker = lambda: CubeQueries.find_face(self.cube, pred)

        return FaceLoc(color, t)

    def _track_even(self, f: Face, rc: Tuple[int, int]) -> FaceLoc:

        # Why can't we track by slice index ? because when moving from face to face
        #  index may be changed
        _slice = f.center.get_center_slice(rc)
        return self._trace_face_by_slice(_slice)

    def _trace_face_by_slice(self, _slice) -> FaceLoc:

        global _tracer_unique_id
        _tracer_unique_id += 1

        key = "track:" + str(_slice.color) + str(_tracer_unique_id)
        _slice.edge.c_attributes[key] = True

        def _slice_pred(s: CenterSlice):
            return key in s.edge.c_attributes

        def _face_pred(_f: Face):
            return CubeQueries.find_slice_in_face_center(_f, _slice_pred) is not None

        color = _slice.color
        return self._track_face(color, _face_pred)

    def _trace_face_by_slice_color(self, face: Face, color: Color):
        """
        Find slice on face and trace it
        :param face:
        :param color:
        :return:
        """

        _slice = CubeQueries.find_slice_in_face_center(face, lambda s: s.color == color)
        assert _slice

        return self._trace_face_by_slice(_slice)

    def __do_center(self, face_loc: FaceLoc) -> bool:

        """

        :param face:
        :param color:
        :return: if nay work was done


        """

        face: Face = face_loc.face
        color: Color = face_loc.color

        if self._is_face_solved(face, color):
            self.debug(f"Face is already done {face}",
                       level=1)
            return False

        cmn = self.cmn

        self.debug(f"Working on face {face}",
                   level=1)

        cube = self.cube

        nn = face.n_slices
        if nn % 2 and config.OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS:
            ok_on_this = self.count_color_on_face(face, color)
            if not (ok_on_this > nn * nn / 2):
                other = CubeQueries.is_face(cube, lambda f: self.count_color_on_face(f, color) > ok_on_this)
                if other:
                    self._optimize_by_moving_centres(face_loc, other)

                    if face_loc.face.is3x3:
                        return True

        # we loop bringing all adjusted faces up
        cmn.bring_face_front(face_loc.face)
        # from here face is no longer valid

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

    def _optimize_by_moving_centres(self, face_loc: FaceLoc, other: Face):

        """
        We reach here becuase we neet to do face_loc, but most of its pieces or on other
        :param cmn:
        :param color:
        :param cube:
        :param face_loc:
        :param nn:
        :param other:
        :return:
        """

        color: Color = face_loc.color
        cube: Cube = self.cube
        nn: int = cube.n_slices
        cmn = self.cmn

        other_tracer = self._trace_face_by_slice_color(other, color)

        self.debug(f"Found most of {face_loc.face} color {color} on {other_tracer.face}")

        # we want to bring the other to front

        # [2:2]E [2:2]M [2:2]E' [2:2]M'
        #   back -> up, up -> right, right->front
        mid = 1 + nn // 2
        _center_move_alg = Algs.E[mid] + Algs.M[mid] + Algs.E[mid].prime + Algs.M[mid].prime

        self.debug(f"Bringing center piece {color} from {face_loc.face} into {other_tracer.face}")

        others_un_resolved = [f for f in set(cube.faces) - {face_loc.face} - {face_loc.face.opposite} if
                              not f.is3x3]
        self.debug(f"Found others unsolved {others_un_resolved}")

        op = self.op
        if len(others_un_resolved) >= 4:

            self.debug("Bringing without preserving any face")

            cmn.bring_face_front(other_tracer.face)
            assert other_tracer.face is cube.front

            self.debug(f"Out face is now on {face_loc.face}")

            if cube.back is not face_loc.face:
                self._bring_face_up_preserve_front(face_loc.face)
                # todo: optimize it, find alg to bring face from up to front, it should be easy
                op.op(Algs.B[1:nn + 1])
                # now other is on right
                op.op(_center_move_alg)
            else:
                # it is on back
                # todo: Optimize !!!
                self.debug("Switching back/front up/down not affecting left/right centers")

                # this algorith switch front<->back up<->sown
                op.op(Algs.Y)

                # now these 3 switch right and left
                op.op(_center_move_alg)
                op.op(Algs.Y)
                op.op(_center_move_alg)

                # so no it switches front/back
                op.op(Algs.Y.prime)

        elif len(others_un_resolved) >= 2:

            self.debug("Bringing , but need to preserve two")

            if other_tracer.face is face_loc.face.opposite:
                self.debug(f"Face {face_loc.face} is opposite of  {other_tracer.face}")

                cmn.bring_face_front(other_tracer.face)
                assert other_tracer.face is cube.front
                self.debug(f"Now {other_tracer.face} on front, center piece {color} is  on {face_loc.face}")

                # we are going to switch front and back, not affecting left/right
                # sw we must be sure up/down are not solved

                if not cube.right.is3x3:
                    # moving up to right, making sure not to harm it
                    op.op(Algs.Z)

                assert not cube.up.is3x3 and not cube.down.is3x3

                op.op(Algs.Y)

                # now these 3 switch right and left
                op.op(_center_move_alg)
                op.op(Algs.Y)
                op.op(_center_move_alg)

                # so no it switches front/back
                op.op(Algs.Y.prime)

                # self.debug(f"Inspect cube now, {face_loc.face} should be on front with color {color}")
                # op.op(Algs.Y + Algs.Y.prime)
            else:
                # to reproduce: simply [mid]E
                # two others are unsolved, so in total we have 4 (me my opposite) + two others
                cmn.bring_face_front(other_tracer.face)
                assert other_tracer.face is cube.front

                self._bring_face_up_preserve_front(face_loc.face)
                assert face_loc.face is cube.up

                # noy we need to bring up centerpiece into front preserving left and right
                # we can destroy back and down
                #   back -> up, up -> right, right->front
                assert False

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

        with self.w_center_slice_annotate(cs):
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

            with self.w_center_slice_annotate(source_slice):

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

                _alg_s = [rotate_on_cell.prime * r1_mul,
                          on_front_rotate,
                          rotate_on_second.prime * r1_mul,
                          on_front_rotate.prime,
                          rotate_on_cell * r1_mul,
                          on_front_rotate,
                          rotate_on_second * r1_mul,
                          on_front_rotate.prime]

                for a in _alg_s:
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

        if face.name == FaceName.B or face.name == FaceName.F:
            raise InternalSWError(f"{face.name} is not supported, can't bring them to up preserving front")

        self.debug(f"Need to bring {face} to up")

        # rotate back with all slices clockwise
        rotate = Algs.B[1:self.cube.n_slices + 1]

        match face.name:

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
        return self.cube.original_layout.opposite_color(color)

    def _find_face_with_max_colors(self) -> Tuple[Face, Color]:
        n_max = -1
        f_max: Face | None = None
        c_max: Color | None = None
        cube = self.cube
        colors: Collection[Color] = cube.original_layout.colors()
        for f in cube.faces:
            for c in colors:
                n = self.count_color_on_face(f, c)
                if n > n_max:
                    n_max = n
                    f_max = f
                    c_max = c

        assert f_max and c_max  # mypy
        return f_max, c_max
