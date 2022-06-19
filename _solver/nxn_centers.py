from collections.abc import Iterator, Sequence
from enum import Enum, unique
from typing import Tuple, Callable, Collection, Any, TypeAlias

import config
from _solver.base_solver import SolverElement, ISolver
from _solver.common_op import CommonOp
from algs import algs
from algs.algs import Algs
from app_exceptions import InternalSWError
from model.cube import Cube
from model.cube_boy import CubeLayout
from model.cube_face import Face
from model.cube_queries import CubeQueries, Pred
from model.elements import FaceName, Color, CenterSlice


def use(_):
    pass


_status = None

FaceTracker = Callable[[], Face]

Point: TypeAlias = Tuple[int, int]
Block: TypeAlias = Tuple[Point, Point]

_tracer_unique_id: int = 0


@unique
class _SearchBlockMode(Enum):
    CompleteBlock = 1
    BigThanSource = 2
    ExactMatch = 3  # required on source match source


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

    def __str__(self) -> str:
        return f"{self.color.name}@{self.face}"


class NxNCenters(SolverElement):
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

        cube = self.cube

        faces: list[FaceLoc]

        if cube.n_slices % 2:
            # odd cube

            # do without back as long as there is work to do
            faces = [self._track_odd(f) for f in cube.faces]



        else:

            f1: FaceLoc = self._track_no_1()

            f2 = self._track_opposite(f1)

            # becuase we find f1 by max colors, then it is clear that it has a least one of scuh a color
            # and oposite doesnot need color for tracing
            # self._do_faces([f1, f2], True, True)

            # now colors of f1/f2 can't be on 4 that left, so we can choose any one
            f3 = self._track_no_3([f1, f2])
            f4 = self._track_opposite(f3)

            # f3 contains at least one color that is not in f1, f2, so no need to bring at leas one
            # but there is a question if such f3 always exists
            self._do_faces([f3, f4], True, True)

            f5, f6 = self._track_two_last([f1, f2, f3, f4])

            # so we don't need this also, otherwise _track_two_last should crash
            # self._do_faces([f5, f6], True, True)

            faces = [f1, f2, f3, f4, f5, f6]

            # now each face has at least one color, so

        while True:
            if not self._do_faces(faces, False, False):
                break

        self._do_faces(faces, False, True)

        assert self._is_solved()

    def _do_faces(self, faces, minimal_bring_one_color, use_back_too: bool) -> bool:
        # while True:
        work_done = False
        for f in faces:
            # we must trace faces, because they are moved by algorith
            # we need to locate the face by original_color, b ut on odd cube, the color is of the center
            if self._do_center(f, minimal_bring_one_color, use_back_too):
                work_done = True
            # if NxNCenters.work_on_b or not work_done:
            #     break

        return work_done

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

    def _track_no_3(self, two_first: Sequence[FaceLoc]) -> FaceLoc:

        cube = self.cube

        assert len(two_first) == 2

        left = list({*cube.faces} - {two_first[0].face, two_first[1].face})

        assert not cube.n_slices % 2

        c12 = {two_first[0].color, two_first[1].color}

        left_colors = set(cube.original_layout.colors()) - c12

        # # can be any, still doesn't prevent BOY
        # There will always a face that contains a color that is not included in f1, f2
        # because f1, f2 contains only 1/3 of all pieces
        f3, f3_color = self._find_face_with_max_colors(left, left_colors)

        return self._trace_face_by_slice_color(f3, f3_color)

    def _track_two_last(self, four_first: Sequence[FaceLoc]) -> Tuple[FaceLoc, FaceLoc]:

        cube = self.cube

        assert cube.n_slices % 2 == 0

        left_two_faces: list[Face] = list({*cube.faces} - {f.face for f in four_first})

        assert len(left_two_faces) == 2

        colors: set[Color] = set((f.color for f in four_first))

        left_two_colors: set[Color] = set(self.cube.original_layout.colors()) - colors

        c5: Color = left_two_colors.pop()
        c6: Color = left_two_colors.pop()

        f5: Face = left_two_faces[0]
        f6: Face = left_two_faces[1]

        try1 = {f.face.name: f.color for f in four_first}
        try1[f5.name] = c5
        try1[f6.name] = c6
        cl: CubeLayout = CubeLayout(False, try1)

        if not cl.same(self.cube.original_layout):
            f5, f6 = (f6, f5)
            try1 = {f.face.name: f.color for f in four_first}
            try1[f5.name] = c5
            try1[f6.name] = c6
            cl = CubeLayout(False, try1)
            assert cl.same(self.cube.original_layout)

            # now find in f5 a slice with this color

        def _s_pred(s: CenterSlice):
            return s.color == c5

        _slice = CubeQueries.find_slice_in_face_center(f5, _s_pred)

        # can be a case that f1,f2,f3,f4 contains all the left c5, c6 ?
        # yes it can.
        # but we can improve by tracking by the relation between then faces (BOY)
        # track: not in f1,,f4 and make it a BOY
        if _slice is None:
            raise InternalSWError(f"Un supported case, f5, didn't find a color {c5}")
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

    def _do_center(self, face_loc: FaceLoc, minimal_bring_one_color, use_back_too: bool) -> bool:

        if self._is_face_solved(face_loc.face, face_loc.color):
            self.debug(f"Face is already done {face_loc.face}",
                       level=1)
            return False

        color = face_loc.color

        if minimal_bring_one_color and self._has_color_on_face(face_loc.face, color):
            self.debug(f"{face_loc.face} already has at least one {color}")
            return False

        sources = set(self.cube.faces) - {face_loc.face}
        if not use_back_too:
            sources -= {face_loc.face.opposite}

        if all(not self._has_color_on_face(f, color) for f in sources):
            self.debug(f"For face {face_loc.face}, No color {color} available on  {sources}",
                       level=1)
            return False

        self.debug(f"Need to work on {face_loc.face}",
                   level=1)

        work_done = self.__do_center(face_loc, minimal_bring_one_color, use_back_too)

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

    def __do_center(self, face_loc: FaceLoc, minimal_bring_one_color: bool, use_back_too: bool) -> bool:

        """

        :return: if nay work was done


        """

        face: Face = face_loc.face
        color: Color = face_loc.color

        if self._is_face_solved(face, color):
            self.debug(f"Face is already done {face}",
                       level=1)
            return False

        if minimal_bring_one_color and self._has_color_on_face(face_loc.face, color):
            self.debug(f"{face_loc.face} already has at least one {color}")
            return False

        cmn = self.cmn

        self.debug(f"Working on face {face}",
                   level=1)

        cube = self.cube

        # we loop bringing all adjusted faces up
        cmn.bring_face_front(face_loc.face)
        # from here face is no longer valid
        # so

        work_done = False

        if any(self._has_color_on_face(f, color) for f in cube.front.adjusted_faces()):
            for _ in range(3):  # 3 faces
                # need to optimize ,maybe no sources on this face

                # don't use face - it was moved !!!
                if self._do_center_from_face(cube.front, minimal_bring_one_color, color, cube.up):
                    work_done = True
                    if minimal_bring_one_color:
                        return work_done

                if self._is_face_solved(face_loc.face, color):
                    return work_done

                self._bring_face_up_preserve_front(cube.left)

            # on the last face
            # don't use face - it was moved !!!
            if self._do_center_from_face(cube.front, minimal_bring_one_color, color, cube.up):
                work_done = True
                if minimal_bring_one_color:
                    return work_done

            if self._is_face_solved(face_loc.face, color):
                return work_done

        if use_back_too:
            # now from back
            # don't use face - it was moved !!!
            if self._do_center_from_face(cube.front, minimal_bring_one_color, color, cube.back):
                work_done = True

        return work_done

    def _do_center_from_face(self, face: Face, minimal_bring_one_color, color: Color, source_face: Face) -> bool:

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

        work_done = False

        center = face.center

        n = cube.n_slices

        if n % 2 and config.OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS:

            ok_on_this = self.count_color_on_face(face, color)

            on_source = self.count_color_on_face(source_face, color)

            if on_source - ok_on_this > 2:  # swap two faces is about two communicators
                self._swap_entire_face_odd_cube(color, face, source_face)
                work_done = True

        if config.OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_BLOCKS:
            # should move minimal_bring_one_color into _do_blocks, becuas ein case of back, it can do too much
            if self._do_blocks(color, cube, face, source_face):
                work_done = True
                if minimal_bring_one_color:
                    return work_done

        else:

            # the above also did a 1 size block
            for rc in self._2d_center_iter():

                if self._block_communicator(color,
                                            face,
                                            source_face,
                                            rc, rc,
                                            _SearchBlockMode.CompleteBlock):

                    after_fixed_color = center.get_center_slice(rc).color

                    if after_fixed_color != color:
                        raise InternalSWError(f"Slice was not fixed {rc}, " +
                                              f"required={color}, " +
                                              f"actual={after_fixed_color}")

                    self.debug(f"Fixed slice {rc}")

                    work_done = True
                    if minimal_bring_one_color:
                        return work_done

        if not work_done:
            self.debug(f"Internal error, no work was done on face {face} required color {color}, "
                       f"but source face  {source_face} contains {self.count_color_on_face(source_face, color)}")
            for rc in self._2d_center_iter():
                if center.get_center_slice(rc).color != color:
                    print(f"Missing: {rc}  {[*self._get_four_center_points(rc[0], rc[1])]}")
            for rc in self._2d_center_iter():
                if source_face.center.get_center_slice(rc).color == color:
                    print(f"Found on {source_face}: {rc}  {source_face.center.get_center_slice(rc)}")

            raise InternalSWError("See error in log")

        return work_done

    def _do_blocks(self, color, cube, face, source_face):

        work_done = False

        big_blocks = self._search_big_block(source_face, color)

        if not big_blocks:
            return False

        # because we do exact match, there is no risk that that new blocks will be constructed,
        # so we try all

        for _, big_block in big_blocks:
            # print(f"@@@@@@@@@@@ Found big block: {big_block}")

            rc1 = big_block[0]
            rc2 = big_block[1]

            rc1_on_target = self._point_on_source(source_face is cube.back, rc1)
            rc2_on_target = self._point_on_source(source_face is cube.back, rc2)

            for _ in range(4):
                if self._block_communicator(color,
                                            face,
                                            source_face,
                                            rc1_on_target, rc2_on_target,
                                            # actually we want big-than, but for this we need to find best match
                                            # it still doesn't work, we need another mode, Source and Target Match
                                            # but for this we need to search source only
                                            _SearchBlockMode.ExactMatch):
                    # this is much far then true, we need to search new block
                    work_done = True
                    break

                rc1_on_target = CubeQueries.rotate_point_clockwise(cube, rc1_on_target)
                rc2_on_target = CubeQueries.rotate_point_clockwise(cube, rc2_on_target)

        return work_done

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

        return CubeQueries.rotate_point_clockwise(self.cube, (row, column), n)

    def rotate_point_counterclockwise(self, row: int, column: int, n=1) -> Tuple[int, int]:
        return CubeQueries.rotate_point_counterclockwise(self.cube, (row, column), n)

    def boy_opposite(self, color: Color) -> Color:
        return self.cube.original_layout.opposite_color(color)

    def _find_face_with_max_colors(self, faces: Sequence[Face] = None, colors: Collection[Color] = None) -> Tuple[
        Face, Color]:
        n_max = -1
        f_max: Face | None = None
        c_max: Color | None = None
        cube = self.cube

        if colors is None:
            colors = cube.original_layout.colors()

        if faces is None:
            faces = cube.faces

        for f in faces:
            for c in colors:
                n = self.count_color_on_face(f, c)
                if n > n_max:
                    n_max = n
                    f_max = f
                    c_max = c

        assert f_max and c_max  # mypy
        return f_max, c_max

    def _swap_entire_face_odd_cube(self, required_color: Color, face: Face, source: Face):

        cube = self.cube
        nn = cube.n_slices

        assert nn % 2, "Cube must be odd"

        assert face is cube.front
        assert source is cube.up or source is cube.back

        op = self.op

        mid = nn // 2
        mid_pls_1 = 1 + nn // 2  # == 3 on 5

        end = nn

        rotate_mul = 1
        if source is cube.back:
            rotate_mul = 2

        # on odd cube
        # todo: replace with self._get_slice_m_alg()
        swap_faces = [Algs.M[1:mid_pls_1 - 1].prime * rotate_mul, Algs.F.prime * 2,
                      Algs.M[1:mid_pls_1 - 1] * rotate_mul,
                      Algs.M[mid_pls_1 + 1:end].prime * rotate_mul,
                      Algs.F * 2 + Algs.M[mid_pls_1 + 1:end] * rotate_mul
                      ]
        op.op(Algs.bigAlg(None, *swap_faces))

        # communicator 1, upper block about center
        self._block_communicator(required_color, face, source,
                                 (mid + 1, mid), (nn - 1, mid),
                                 _SearchBlockMode.BigThanSource)

        # communicator 2, lower block below center
        self._block_communicator(required_color, face, source,
                                 (0, mid), (mid - 1, mid),
                                 _SearchBlockMode.BigThanSource)

        # communicator 3, left to center
        self._block_communicator(required_color, face, source,
                                 (mid, 0), (mid, mid - 1),
                                 _SearchBlockMode.BigThanSource)

        # communicator 4, right ot center
        self._block_communicator(required_color, face, source,
                                 (mid, mid + 1), (mid, nn - 1),
                                 _SearchBlockMode.BigThanSource)

    def _block_communicator(self,
                            required_color: Color,
                            face: Face, source_face: Face, rc1: Tuple[int, int], rc2: Tuple[int, int],
                            mode: _SearchBlockMode) -> bool:
        """

        :param face:
        :param source_face:
        :param rc1: one corner of block, center slices indexes [0..n)
        :param rc2: other corner of block, center slices indexes [0..n)
        :param mode: to search complete block or with colors more than mine
        :return: False if block not found (or no work need to be done), no communicator was done
        """
        cube: Cube = face.cube
        assert face is cube.front
        assert source_face is cube.up or source_face is cube.back

        is_back = source_face is cube.back

        # normalize block
        r1 = rc1[0]
        c1 = rc1[1]

        r2 = rc2[0]
        c2 = rc2[1]

        if r1 > r2:
            r1, r2 = r2, r1
        if c1 > c2:
            c1, c2 = c2, c1

        rc1 = (r1, c1)
        rc2 = (r2, c2)

        # in case of odd nd (mid, mid), search will fail, nothing to do
        # if we change the order, then block validation below will fail,
        #  so we need to check for case odd (mid, mid) somewhere else
        # now search block
        n_rotate = self._search_block(face, source_face, required_color, mode, rc1, rc2)

        if n_rotate is None:
            return False

        on_front_rotate: algs.Alg

        # assume we rotate F clockwise
        rc1_f_rotated = self.rotate_point_clockwise(r1, c1)
        rc2_f_rotated = self.rotate_point_clockwise(r2, c2)

        # the columns ranges must not intersect
        if self._1_d_intersect((c1, c2), (rc1_f_rotated[1], rc2_f_rotated[1])):
            on_front_rotate = Algs.F.prime
            rc1_f_rotated = self.rotate_point_counterclockwise(r1, c1)
            rc2_f_rotated = self.rotate_point_counterclockwise(r2, c2)

            if self._1_d_intersect((c1, c2), (rc1_f_rotated[1], rc2_f_rotated[1])):
                print("xxx")
            assert not self._1_d_intersect((c1, c2), (rc1_f_rotated[1], rc2_f_rotated[1]))
        else:
            # clockwise is OK
            on_front_rotate = Algs.F

        # center indexes are in opposite direction of R
        #   index is from left to right, R is from right to left
        rotate_on_cell = self._get_slice_m_alg(rc1[1], rc2[1])
        rotate_on_second = self._get_slice_m_alg(rc1_f_rotated[1], rc2_f_rotated[1])

        if is_back:
            rotate_mul = 2
        else:
            rotate_mul = 1

        cum = [rotate_on_cell.prime * rotate_mul,
               on_front_rotate,
               rotate_on_second.prime * rotate_mul,
               on_front_rotate.prime,
               rotate_on_cell * rotate_mul,
               on_front_rotate,
               rotate_on_second * rotate_mul,
               on_front_rotate.prime]

        source_slices: list[CenterSlice] = []
        target_slices: list[CenterSlice] = []

        if self.animation_on:
            _on_src1_1 = self._point_on_source(is_back, rc1)
            _on_src1_2 = self._point_on_source(is_back, rc2)
            # why - ? because we didn't yet rotate it
            _on_src1_1 = CubeQueries.rotate_point_clockwise(cube, _on_src1_1, -n_rotate)
            _on_src1_2 = CubeQueries.rotate_point_clockwise(cube, _on_src1_2, -n_rotate)
            source_slices = [source_face.center.get_center_slice(rc) for rc in self._2d_range(_on_src1_1, _on_src1_2)]

            target_slices = [face.center.get_center_slice(rc) for rc in self._2d_range_on_source(False, rc1, rc2)]

        with self.w_center_slice_annotate(*source_slices, *target_slices):
            if n_rotate:
                self.op.op(Algs.of_face(source_face.name) * n_rotate)
            self.op.op(Algs.bigAlg(None, *cum))

        return True

    def _is_valid_and_block_for_search(self, face: Face, color: Color, rc1: Point, rc2: Point):

        is_valid_block = self._is_valid_block(rc1, rc2)

        if not is_valid_block:
            return False

        is_block = self._is_block(face, color, None, rc1, rc2, dont_convert_coordinates=True)

        return is_block

    def _search_big_block(self, face: Face, color: Color) -> Sequence[Tuple[int, Block]] | None:

        """
        Rerun all possible blocks, 1 size too, sorted from big to small
        :param face:
        :param color:
        :return:
        """

        center = face.center

        res: list[Tuple[int, Block]] = []

        n = self.cube.n_slices

        for rc in self._2d_center_iter():

            if center.get_center_slice(rc).color == color:

                # collect also 1 size blocks
                res.append((1, (rc, rc)))

                # now try to extend it over r
                r_max = None
                for r in range(rc[0] + 1, n):

                    if not self._is_valid_and_block_for_search(face, color, rc, (r, rc[1])):
                        break
                    else:
                        r_max = r

                if not r_max:
                    r_max = rc[0]

                # now try to extend it over c
                c_max = None
                for c in range(rc[1] + 1, n):
                    if not self._is_valid_and_block_for_search(face, color, rc, (r_max, c)):
                        break
                    else:
                        c_max = c

                if not c_max:
                    c_max = rc[1]

                size = self._block_size(rc, (r_max, c_max))

                # if size > 1:
                res.append((size, (rc, (r_max, c_max))))

        res = sorted(res, key=lambda s: s[0], reverse=True)
        return res

    def _is_valid_block(self, rc1: Point, rc2: Point):

        r1 = rc1[0]
        c1 = rc1[1]

        r2 = rc2[0]
        c2 = rc2[1]

        rc1_f_rotated = self.rotate_point_clockwise(r1, c1)
        rc2_f_rotated = self.rotate_point_clockwise(r2, c2)

        # the columns ranges must not intersect
        if self._1_d_intersect((c1, c2), (rc1_f_rotated[1], rc2_f_rotated[1])):
            rc1_f_rotated = self.rotate_point_counterclockwise(r1, c1)
            rc2_f_rotated = self.rotate_point_counterclockwise(r2, c2)

            if self._1_d_intersect((c1, c2), (rc1_f_rotated[1], rc2_f_rotated[1])):
                return False

        return True

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

    @staticmethod
    def _has_color_on_face(face: Face, color: Color) -> int:
        for s in face.center.all_slices:
            if s.color == color:
                return True
        return False

    @staticmethod
    def _count_colors_on_block(color: Color, source_face: Face, rc1: Tuple[int, int], rc2: Tuple[int, int]):

        """
        Count number of centerpieces on center that match color
        :param source_face: front up or back
        :param rc1: one corner of block, front coords, center slice indexes
        :param rc2: other corner of block, front coords, center slice indexes
        :return:
        """

        cube = source_face.cube
        is_back = source_face is cube.back

        if is_back:
            # the logic here is hard code of the logic in slice rotate
            # it will be broken if cube layout is changed
            # here we assume we work on F, and UP has same coord system as F, and
            # back is mirrored in both direction
            inv = cube.inv
            rc1 = (inv(rc1[0]), inv(rc1[1]))
            rc2 = (inv(rc2[0]), inv(rc2[1]))

        r1 = rc1[0]
        c1 = rc1[1]

        r2 = rc2[0]
        c2 = rc2[1]

        if r1 > r2:
            r1, r2 = r2, r1

        if c1 > c2:
            c1, c2 = c2, c1

        _count = 0
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if color == source_face.center.get_center_slice((r, c)).color:
                    _count += 1

        return _count

    @staticmethod
    def _1_d_intersect(range_1: Tuple[int, int], range_2: Tuple[int, int]):

        """
                 x3--------------x4
           x1--------x2
        :param range_1:  x1, x2
        :param range_2:  x3, x4
        :return:  not ( x3  > x2 or x4 < x1 )
        """

        x1 = range_1[0]
        x2 = range_1[1]
        x3 = range_2[0]
        x4 = range_2[1]

        # after rotation points swap coordinates
        if x1 > x2:
            x1, x2 = x2, x1

        if x3 > x4:
            x3, x4 = x4, x3

        if x3 > x2:
            return False

        if x4 < x1:
            return False

        return True

    def _point_on_source(self, is_back: bool, rc: Tuple[int, int]) -> Point:

        inv = self.cube.inv

        # the logic here is hard code of the logic in slice rotate
        # it will be broken if cube layout is changed
        # here we assume we work on F, and UP has same coord system as F, and
        # back is mirrored in both direction
        if is_back:
            return inv(rc[0]), inv(rc[1])
        else:
            # on up
            return rc

    def _point_on_target(self, source_is_back: bool, rc: Tuple[int, int]) -> Point:

        inv = self.cube.inv

        # the logic here is hard code of the logic in slice rotate
        # it will be broken if cube layout is changed
        # here we assume we work on F, and UP has same coord system as F, and
        # back is mirrored in both direction
        if source_is_back:
            return inv(rc[0]), inv(rc[1])
        else:
            # on up
            return rc

    def _block_on_source(self, is_back: bool, rc1: Point, rc2: Point) -> Block:

        return self._point_on_source(is_back, rc1), self._point_on_source(is_back, rc2)

    def _2d_range_on_source(self, is_back: bool, rc1: Point, rc2: Point) -> Iterator[Point]:

        """
        Iterator over 2d block columns advanced faster
        Convert block to source coordinates
        :param rc1: one corner of block, front coords, center slice indexes
        :param rc2: other corner of block, front coords, center slice indexes
        :return:
        """

        rc1 = self._point_on_source(is_back, rc1)
        rc2 = self._point_on_source(is_back, rc2)

        yield from self._2d_range(rc1, rc2)

    @staticmethod
    def _2d_range(rc1: Point, rc2: Point) -> Iterator[Point]:

        """
        Iterator over 2d block columns advanced faster
        :param rc1: one corner of block, front coords, center slice indexes
        :param rc2: other corner of block, front coords, center slice indexes
        :return:
        """

        r1 = rc1[0]
        c1 = rc1[1]

        r2 = rc2[0]
        c2 = rc2[1]

        if r1 > r2:
            r1, r2 = r2, r1

        if c1 > c2:
            c1, c2 = c2, c1

        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                yield r, c

    def _2d_center_iter(self) -> Iterator[Point]:

        """
        Walk on all points in center of size n_slices
        """

        n = self.cube.n_slices

        for r in range(n):
            for c in range(n):
                yield r, c

    @staticmethod
    def _block_size(rc1: Tuple[int, int], rc2: Tuple[int, int]) -> int:
        return (abs(rc2[0] - rc1[0]) + 1) * (abs(rc2[1] - rc1[1]) + 1)

    def _is_block(self,
                  source_face: Face,
                  required_color: Color,
                  min_points: int | None,
                  rc1: Tuple[int, int], rc2: Tuple[int, int],
                  dont_convert_coordinates: bool = False) -> bool:

        """

        :param source_face:
        :param required_color:
        :param min_points: If None that all block , min = block size
        :param rc1:
        :param rc2:
        :param dont_convert_coordinates if True then don't convert coordinates according to source face
        :return:
        """

        # Number of points in block
        _max = self._block_size(rc1, rc2)

        if min_points is None:
            min_points = _max

        max_allowed_not_match = _max - min_points  # 0 in cas emin is max

        center = source_face.center
        miss_count = 0

        if dont_convert_coordinates:
            _range = self._2d_range(rc1, rc2)
        else:
            _range = self._2d_range_on_source(source_face is source_face.cube.back, rc1, rc2)

        for rc in _range:

            if center.get_center_slice(rc).color != required_color:

                miss_count += 1
                if miss_count > max_allowed_not_match:
                    return False

        return True

    def _search_block(self,
                      target_face: Face,
                      source_face: Face,
                      required_color: Color,
                      mode: _SearchBlockMode,
                      rc1: Tuple[int, int], rc2: Tuple[int, int]) -> int | None:

        """
        Search block according to mode, if target is already satisfied, then return not found
        :param source_face:
        :param required_color:
        :param mode:
        :param rc1:
        :param rc2:
        :return: How many source clockwise rotate in order to match the block to source
        """

        block_size = self._block_size(rc1, rc2)

        n_ok = self._count_colors_on_block(required_color, target_face, rc1, rc2)

        if n_ok == block_size:
            return None  # nothing to do

        if mode == _SearchBlockMode.CompleteBlock:
            min_required = block_size
        elif mode == _SearchBlockMode.BigThanSource:
            # The number of communicators before > after
            # before = size - n_ok
            # after  = n_ok  - because the need somehow to get back
            # size-n_ok > n_ok
            min_required = n_ok + 1
        elif mode == _SearchBlockMode.ExactMatch:
            if n_ok:
                return None
            min_required = block_size

        else:
            raise InternalSWError

        cube = self.cube

        for n in range(4):
            if self._is_block(source_face, required_color, min_required, rc1, rc2):
                # we rotate n to find the block, so client need to rotate -n
                return (-n) % 4
            rc1 = CubeQueries.rotate_point_clockwise(cube, rc1)
            rc2 = CubeQueries.rotate_point_clockwise(cube, rc2)

        return None

    def _get_slice_m_alg(self, c1, c2):

        """
        Center Slice index [0, n)
        :param c1:
        :param c2:
        :return:
        """

        inv = self.cube.inv

        #   index is from left to right, R is from right to left,
        # so we need to invert
        c1 = inv(c1)
        c2 = inv(c2)

        if c1 > c2:
            c1, c2 = c2, c1

        return Algs.M[c1 + 1:c2 + 1]
