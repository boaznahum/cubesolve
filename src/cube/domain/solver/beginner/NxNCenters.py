import sys
from collections.abc import Iterator, Sequence, Iterable, Set
from enum import Enum, unique
from typing import Tuple, TypeAlias

from cube.domain import algs
from cube.application import config
from cube.domain.algs import Algs
from cube.domain.exceptions import InternalSWError
from cube.domain.model import FaceName, Color, CenterSlice
from cube.domain.model.Cube import Cube
from cube.domain.model.cube_boy import CubeLayout, color2long
from cube.domain.model.Face import Face
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.FaceTracker import FaceTracker
from cube.domain.solver.beginner.NxnCentersFaceTracker import NxNCentersFaceTrackers
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.common.SolverElement import SolverElement
from cube.utils.OrderedSet import OrderedSet


def use(_):
    pass


_status = None

Point: TypeAlias = Tuple[int, int]
Block: TypeAlias = Tuple[Point, Point]


@unique
class _SearchBlockMode(Enum):
    CompleteBlock = 1
    BigThanSource = 2
    ExactMatch = 3  # required on source match source


class _CompleteSlice:
    is_row: bool
    index: int  # of row/column
    n_matches: int  # number of pieces match color

    def __init__(self, is_row: bool, index: int, n_matches: int, contains_trackers) -> None:
        self.is_row = is_row
        self.index = index
        self.n_matches = n_matches
        self.contains_track_slice = contains_trackers


class NxNCenters(SolverElement):
    def __init__(self, slv: BaseSolver) -> None:
        super().__init__(slv)

        self._faces: Sequence[FaceTracker] = []

        self._trackers = NxNCentersFaceTrackers(slv)

        self._sanity_check_is_a_boy = config.SOLVER_SANITY_CHECK_IS_A_BOY
        self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES = config.OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES
        self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES_ONLY_TARGET_ZERO = config.OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES_ONLY_TARGET_ZERO
        self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_BLOCKS = config.OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_BLOCKS
        self._OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS = config.OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS

    def debug(self, *args, level=3):
        if level <= NxNCenters.D_LEVEL:
            super().debug("NxX Centers:", args)

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

        with self.ann.annotate(h1="Big cube centers"):
            try:
                self._solve()
            finally:
                self._trackers._debug_print_track_slices("After solving")
                self._trackers._remove_all_track_slices()
                self._trackers._debug_print_track_slices("After removal")

    def _solve(self) -> None:

        cube = self.cube

        faces: list[FaceTracker]

        if cube.n_slices % 2:
            # odd cube

            # do without back as long as there is work to do
            faces = [FaceTracker.track_odd(f) for f in cube.faces]

        else:

            f1: FaceTracker = self._trackers.track_no_1()

            f2 = f1.track_opposite()

            # because we find f1 by max colors, then it is clear that it has at least one of such a color
            # and opposite doesn't need color for tracing
            # self._do_faces([f1, f2], True, True)

            # now colors of f1/f2 can't be on 4 that left, so we can choose any one
            f3 = self._trackers._track_no_3([f1, f2])
            f4 = f3.track_opposite()

            # f3 contains at least one color that is not in f1, f2, so no need to bring at leas one
            # but there is a question if such f3 always exists
            self._do_faces([f3, f4], True, True)

            f5, f6 = self._trackers._track_two_last([f1, f2, f3, f4])

            # so we don't need this also, otherwise _track_two_last should crash
            self._do_faces([f5], True, True)
            self._asserts_is_boy([f1, f2, f3, f4, f5, f6])

            FaceTracker.remove_face_track_slices(f5.face)

            f5 = FaceTracker.search_color_and_track(f5.face, f5.color)
            f6 = f5.track_opposite()

            faces = [f1, f2, f3, f4, f5, f6]
            self._faces = faces

            self._asserts_is_boy(faces)

            self._trackers._debug_print_track_slices("After creating all faces")

            # self._faces = faces

            # now each face has at least one color, so

        # SPECIAL_CASE_1
        # A rare case here, when use_back_too is false and complete slice is enabled
        # We have two slices, that have no source other on of the other and on back(but back is not is used)
        # These sources are on the same slice S
        # Face RED finds two colors on S
        # Face Orange finds two colors S
        # what happens is that RED takes slice from ORANGE
        # then ORANGE take from RED, infinite loop
        # It is very rare:
        #   there should be empty target slice in the target face (see config)
        #   this slice is swapped, and not filled by other step(becuase it's sources are on back)
        # To overcome it we swap only if number sources is > n//2
        while True:
            if not self._do_faces(faces, False, False):
                break
            self._asserts_is_boy(faces)

        self._asserts_is_boy(faces)

        self._do_faces(faces, False, True)

        self._asserts_is_boy(faces)

        assert self._is_solved()

    def _do_faces(self, faces: Sequence[FaceTracker], minimal_bring_one_color, use_back_too: bool) -> bool:
        # while True:
        self.debug("_do_faces:", *faces)
        work_done = False
        for f in faces:
            # we must trace faces, because they are moved by algorith
            # we need to locate the face by original_color, b ut on odd cube, the color is of the center
            if self._do_center(f, minimal_bring_one_color, use_back_too):
                work_done = True
                if len(faces) == 6:
                    self._asserts_is_boy(faces)
            # if NxNCenters.work_on_b or not work_done:
            #     break

        return work_done

    def _print_faces(self):

        for f in self._faces:
            print(f.face, f.color, " ", end="")
        print()

    # noinspection PyUnreachableCode,PyUnusedLocal
    def _asserts_is_boy(self, faces: Iterable[FaceTracker]):

        if not self._sanity_check_is_a_boy:
            return

        layout = {f.face.name: f.color for f in faces}

        cl: CubeLayout = CubeLayout(False, layout)

        is_boy = cl.same(self.cube.original_layout)

        if not is_boy:
            print(cl, file=sys.stderr)
            print(file=sys.stderr)

        assert is_boy

    def _do_center(self, face_loc: FaceTracker, minimal_bring_one_color, use_back_too: bool) -> bool:

        if self._is_face_solved(face_loc.face, face_loc.color):
            self.debug(f"Face is already done {face_loc.face}",
                       level=1)
            return False

        color = face_loc.color

        if minimal_bring_one_color and self._has_color_on_face(face_loc.face, color):
            self.debug(f"{face_loc.face} already has at least one {color}")
            return False

        sources:Set[Face] = OrderedSet(self.cube.faces) - {face_loc.face}
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

    def __do_center(self, face_loc: FaceTracker, minimal_bring_one_color: bool, use_back_too: bool) -> bool:

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

        with self.ann.annotate(h2=f"{color2long(face_loc.color).value} face"):
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

        if n % 2 and self._OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS:

            ok_on_this = self.count_color_on_face(face, color)

            on_source = self.count_color_on_face(source_face, color)

            if on_source - ok_on_this > 2:  # swap two faces is about two communicators
                self._swap_entire_face_odd_cube(color, face, source_face)
                work_done = True

        if self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES:
            if self._do_complete_slices(color, face, source_face):
                work_done = True
                if minimal_bring_one_color:
                    return work_done

        if self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_BLOCKS:
            # should move minimal_bring_one_color into _do_blocks, because ein case of back, it can do too much
            if self._do_blocks(color, face, source_face):
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

    def _do_complete_slices(self, color, face, source_face) -> bool:

        work_done = False

        # do while work is done
        while True:
            if not self._do_one_complete_slice(color, face, source_face):
                return work_done

            work_done = True

    def _do_one_complete_slice(self, color, target_face: Face, source_face: Face) -> bool:

        source_slices: Sequence[_CompleteSlice] = self._search_slices_on_face(source_face, color, None, True)

        if not source_slices:
            return False

        odd_mid_slice: int | None = None
        n_slices = self.cube.n_slices
        if n_slices % 2:
            odd_mid_slice = n_slices // 2

        # cache already searched source_slices on the target face
        slices_on_target_face: dict[int, Sequence[_CompleteSlice]] = {}

        for source_slice in source_slices:

            index = source_slice.index

            if index == odd_mid_slice:
                continue  # skip this one

            if source_slice.contains_track_slice:
                continue  # we can't move it happens in even cube

            target_slices = slices_on_target_face.get(index)

            if target_slices is None:
                target_slices = self._search_slices_on_face(target_face, color, index, False)
                assert len(target_slices) == 4  # we search vertical and horizontal x  index, inv(index)
                slices_on_target_face[index] = target_slices

            min_target_slice = target_slices[0]

            if not min_target_slice.contains_track_slice:

                if (
                        (min_target_slice.n_matches == 0 or
                         not self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES_ONLY_TARGET_ZERO) and
                          source_slice.n_matches > 0 / 2.0  # SEE SPECIAL_CASE_1 above
                ) and source_slice.n_matches > min_target_slice.n_matches:
                    # ok now swap

                    # before = self.count_color_on_face(face, color)

                    # self._debug_print_track_slices()
                    # print("before", end="")
                    # self._print_faces()
                    # before = [ (f.face, f.color) for f in self._faces]

                    # _tf: FaceLoc = next(_f for _f in self._faces if _f.face is target_face)
                    # _sf: FaceLoc = next(_f for _f in self._faces if _f.face is source_face)
                    # print(f"@@@ to {color} {_tf} from {_sf} n={source_slice.n_matches}")

                    with self.ann.annotate(h2=f", Swap complete slice"):
                        self._swap_slice(min_target_slice, target_face, source_slice, source_face)

                    # print("after", end="")
                    # self._print_faces()
                    # _after = [ (f.face, f.color) for f in self._faces]
                    # if _before != _after:
                    #     print("xxxx")
                    #     raise InternalSWError()

                    # self._debug_print_track_slices()
                    # self._asserts_is_boy(self._faces)

                    # after = self.count_color_on_face(face, color)

                    # print(before, after, color)

                    return True

        return False

    def _swap_slice(self, target_slice: _CompleteSlice,
                    target_face: Face,
                    source_slice: _CompleteSlice, source_face: Face):

        cube = self.cube
        n_slices = cube.n_slices

        target_index: int

        # slice must be vertical
        op = self.op
        if target_slice.is_row:
            target_slice_block_1 = cube.cqr.rotate_point_counterclockwise((target_slice.index, 0))
            target_index = target_slice_block_1[1]
            op.play(Algs.F.prime)
        else:
            # column
            target_index = target_slice.index

        # now we must bring source slice into position (0,  target_index^)

        nm1 = cube.n_slices - 1
        source_index = source_slice.index
        if source_slice.is_row:
            s1 = (source_index, 0)
            s2 = (source_index, nm1)
        else:
            s1 = (0, source_index)
            s2 = (nm1, source_index)

        # now we need to bring source slice such that one of its endpoints is (0,  target_index^)
        required_on_target = (0, cube.inv(target_index))

        def is_column(p1: Point, p2: Point):

            return (p1[0] == 0 and p2[0] == n_slices - 1) or (p2[0] == 0 and p1[0] == n_slices - 1)

        source_is_back = source_face is cube.back
        n_rotate: int | None = None
        for i in range(4):

            if is_column(s1, s2):
                s1_on_target = self._point_on_target(source_is_back, s1)
                s2_on_target = self._point_on_target(source_is_back, s2)

                if s1_on_target == required_on_target or s2_on_target == required_on_target:
                    n_rotate = i
                    break

            s1 = cube.cqr.rotate_point_clockwise(s1)
            s2 = cube.cqr.rotate_point_clockwise(s2)

        assert n_rotate is not None

        # now rotate source face accordingly:
        rotate_source_alg = Algs.of_face(source_face.name)
        op.play(rotate_source_alg * n_rotate)

        mul = 2 if source_is_back else 1
        # do the swap:
        slice_source_alg: algs.Alg = self._get_slice_m_alg(target_index, target_index)

        def ann_source() -> Iterator[CenterSlice]:
            for rc in self._2d_range(s1, s2):
                yield source_face.center.get_center_slice(rc)

        def ann_target() -> Iterator[CenterSlice]:

            for rc in self._2d_range((0, target_index), (nm1, target_index)):
                yield target_face.center.get_center_slice(rc)

        with self.ann.annotate((ann_source(), AnnWhat.Moved), (ann_target(), AnnWhat.FixedPosition)):
            op.play(slice_source_alg * mul +
                  rotate_source_alg * 2 +  # this replaces source slice with target
                  slice_source_alg.prime * mul
                  )

    def _do_blocks(self, color, face, source_face):

        work_done = False

        cube = self.cube

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

                rc1_on_target = cube.cqr.rotate_point_clockwise(rc1_on_target)
                rc2_on_target = cube.cqr.rotate_point_clockwise(rc2_on_target)

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
                self.op.play(rotate.prime)

            case FaceName.D:
                # todo open range should be supported by slicing
                self.op.play(rotate.prime * 2)

            case FaceName.R:
                # todo open range should be supported by slicing
                self.op.play(rotate)

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

        return self.cube.cqr.rotate_point_clockwise((row, column), n)

    def rotate_point_counterclockwise(self, row: int, column: int, n=1) -> Tuple[int, int]:
        return self.cube.cqr.rotate_point_counterclockwise((row, column), n)

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
        raise InternalSWError("Need to fix MM")

        swap_faces = [Algs.MM()[1:mid_pls_1 - 1].prime * rotate_mul, Algs.F.prime * 2,
                      Algs.MM()[1:mid_pls_1 - 1] * rotate_mul,
                      Algs.MM()[mid_pls_1 + 1:end].prime * rotate_mul,
                      Algs.F * 2 + Algs.MM()[mid_pls_1 + 1:end] * rotate_mul
                      ]
        op.op(Algs.seq_alg(None, *swap_faces))

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
                print("Intersection still exists after rotation", file=sys.stderr)
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

        def _ann_target():

            for rc in self._2d_range_on_source(False, rc1, rc2):
                yield face.center.get_center_slice(rc)

        def _ann_source():
            _on_src1_1 = self._point_on_source(is_back, rc1)
            _on_src1_2 = self._point_on_source(is_back, rc2)
            # why - ? because we didn't yet rotate it
            _on_src1_1 = cube.cqr.rotate_point_clockwise(_on_src1_1, -n_rotate)
            _on_src1_2 = cube.cqr.rotate_point_clockwise(_on_src1_2, -n_rotate)
            for rc in self._2d_range(_on_src1_1, _on_src1_2):
                yield source_face.center.get_center_slice(rc)

        def _h2():
            size_ = self._block_size2(rc1, rc2)
            return f", {size_[0]}x{size_[1]} communicator"

        with self.ann.annotate((_ann_source, AnnWhat.Moved),
                               (_ann_target, AnnWhat.FixedPosition),
                               h2=_h2
                               ):
            if n_rotate:
                self.op.play(Algs.of_face(source_face.name) * n_rotate)
            self.op.play(Algs.seq_alg(None, *cum))

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

    def count_color_on_face(self, face: Face, color: Color) -> int:
        return self.cqr.count_color_on_face(face, color)

    @staticmethod
    def _has_color_on_face(face: Face, color: Color) -> int:
        for s in face.center.all_slices:
            if s.color == color:
                return True
        return False

    @staticmethod
    def _count_colors_on_block(color: Color, source_face: Face, rc1: Tuple[int, int], rc2: Tuple[int, int],
                               ignore_if_back=False) -> int:

        n, _ = NxNCenters._count_colors_on_block_and_tracker(color, source_face, rc1, rc2, ignore_if_back)

        return n

    @staticmethod
    def _count_colors_on_block_and_tracker(color: Color, source_face: Face, rc1: Tuple[int, int], rc2: Tuple[int, int],
                                           ignore_if_back=False) -> Tuple[int, int]:

        """
        Count number of centerpieces on center that match color
        :param source_face: front up or back
        :param rc1: one corner of block, front coords, center slice indexes
        :param rc2: other corner of block, front coords, center slice indexes
        :return:
        """

        cube = source_face.cube
        fix_back_coords = not ignore_if_back and source_face is cube.back

        if fix_back_coords:
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
        _trackers = 0
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                center_slice = source_face.center.get_center_slice((r, c))
                if color == center_slice.color:
                    _count += 1
                if not _trackers and FaceTracker.is_track_slice(center_slice):
                    _trackers += 1

        return _count, _trackers

    def _search_slices_on_face(self, face, color, index: int | None, search_max: bool) -> list[_CompleteSlice]:

        """

        :param face:
        :param color:
        :param index: if not None then return only (index, 0) (index^, 0), (0, index), (0, index^)
        :param search_max:
        :return:
        """

        cube = self.cube
        inv = cube.inv
        n_slices = cube.n_slices
        nm1 = n_slices - 1

        rows: Iterable[int]
        columns: Iterable[int]
        if index is not None:
            rows = [index, inv(index)]
            columns = [index, inv(index)]
        else:
            rows = range(n_slices)
            columns = rows

        _slices = []
        for r in rows:

            n, t = self._count_colors_on_block_and_tracker(color, face, (r, 0), (r, nm1), ignore_if_back=True)

            if n > 1 or not search_max:  # one is not interesting, will be handled by communicator
                # if we search for minimum than we want zero too
                _slice = _CompleteSlice(True, r, n, t > 0)
                _slices.append(_slice)

        for c in columns:

            n, t = self._count_colors_on_block_and_tracker(color, face, (0, c), (nm1, c), ignore_if_back=True)

            if n > 1 or not search_max:  # one is not interesting, will be handled by communicator
                # if we search for minimum than we want zero too
                _slice = _CompleteSlice(False, c, n, t > 0)
                _slices.append(_slice)

        _slices = sorted(_slices, key=lambda s: s.n_matches, reverse=search_max)

        return _slices

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

    @staticmethod
    def _block_size2(rc1: Tuple[int, int], rc2: Tuple[int, int]) -> Tuple[int, int]:
        return (abs(rc2[0] - rc1[0]) + 1), (abs(rc2[1] - rc1[1]) + 1)

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
            rc1 = cube.cqr.rotate_point_clockwise(rc1)
            rc2 = cube.cqr.rotate_point_clockwise(rc2)

        return None

    def _get_slice_m_alg(self, c1, c2):

        """

        :param c1: Center Slice index [0, n)
        :param c2: Center Slice index [0, n)
        :return: m slice in range suitable for [c1, c2]
        """

        #   index is from left to right, L is from left to right,
        # so we don't need to invert

        if c1 > c2:
            c1, c2 = c2, c1

        return Algs.M[c1 + 1:c2 + 1].prime

    D_LEVEL = 3
