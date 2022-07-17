from collections.abc import Sequence, Iterable, Collection
from typing import Tuple

from cube.model import Color, CenterSlice
from cube.model.cube_boy import CubeLayout
from cube.model.cube_face import Face
from cube.model.cube_queries2 import Pred
from cube.solver.common.face_tracker import FaceTracker
from cube.solver.common.base_solver import BaseSolver
from cube.solver.common.solver_element import SolverElement


class NxNCentersFaceTrackers(SolverElement):

    def __init__(self, solver: BaseSolver) -> None:
        super().__init__(solver)

    def _track_no_1(self) -> FaceTracker:

        cube = self.cube
        if cube.n_slices % 2:
            return FaceTracker.track_odd(cube.front)
        else:
            f, c = self._find_face_with_max_colors()
            # see there why can't we track by index
            return FaceTracker.search_color_and_track(f, c)

    def _track_no_3(self, two_first: Sequence[FaceTracker]) -> FaceTracker:

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

        return FaceTracker.search_color_and_track(f3, f3_color)

    def _track_two_last(self, four_first: Sequence[FaceTracker]) -> Tuple[FaceTracker, FaceTracker]:
        cube = self.cube

        assert cube.n_slices % 2 == 0

        left_two_faces: list[Face] = list({*cube.faces} - {f.face for f in four_first})

        assert len(left_two_faces) == 2

        first_4_colors: set[Color] = set((f.color for f in four_first))

        left_two_colors: set[Color] = set(self.cube.original_layout.colors()) - first_4_colors

        c5: Color = left_two_colors.pop()
        c6: Color = left_two_colors.pop()

        f5: Face = left_two_faces.pop()

        color = c5
        pred = self._create_f5_pred(four_first, color)

        if pred(f5):
            # f5/c5 make it a BOY
            pass
        else:
            color = c6
            # other = c5
            # f5/c5 make it a BOY
            pred = self._create_f5_pred(four_first, color)
            assert pred(f5)

        f5_track = FaceTracker.by_pred(cube, color, pred)
        f6_track = f5_track.track_opposite()

        return f5_track, f6_track

    def _create_f5_pred(self, four_first: Sequence[FaceTracker], color) -> Pred[Face]:

        cube = self.cube

        four_first = [*four_first]

        first_4_colors: set[Color] = set((f.color for f in four_first))

        def _pred(f: Face):

            """

            :param f:
            :return: True if f/color make it a boy
            """

            left_two_faces: set[Face] = {*cube.faces} - {f.face for f in four_first}

            if f not in left_two_faces:
                return False

            left_two_colors: set[Color] = set(self.cube.original_layout.colors()) - first_4_colors

            assert color in left_two_colors

            c5: Color = left_two_colors.pop()
            c6: Color = left_two_colors.pop()

            f5: Face = left_two_faces.pop()
            f6: Face = left_two_faces.pop()

            # make f as f5
            if f5 is not f:
                f5, f6 = f, f5

            if c5 is not color:
                c5, c6 = color, c5

            try1 = {f.face.name: f.color for f in four_first}
            try1[f5.name] = c5
            try1[f6.name] = c6
            cl: CubeLayout = CubeLayout(False, try1)

            if cl.same(self.cube.original_layout):
                return True  # f/color make it a BOY

            f5, f6 = (f6, f5)
            try1 = {f.face.name: f.color for f in four_first}
            try1[f5.name] = c5
            try1[f6.name] = c6
            cl = CubeLayout(False, try1)
            assert cl.same(self.cube.original_layout)

            return False

        return _pred

    @staticmethod
    def _is_track_slice(s: CenterSlice):
        return FaceTracker.is_track_slice(s)

    # noinspection PyUnreachableCode
    def _remove_all_track_slices(self):

        """
        Track slices prevent swapping of whole slices and big blocks
        :return:
        """
        for f in self.cube.faces:
            FaceTracker.remove_face_track_slices(f)

    # noinspection PyUnreachableCode,PyUnusedLocal
    def _debug_print_track_slices(self, message: str):

        if True:
            return

        print(f"=== track slices: {message}================================")
        for f in self.cube.faces:
            for s in f.center.all_slices:

                if self.is_track_slice(s):
                    print(f"Track slice: {s} {s.color} on {f}")
        print("===================================")

    def _find_face_with_max_colors(self, faces: Iterable[Face] = None,
                                   colors: Collection[Color] = None) -> Tuple[Face, Color]:

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
                n = self.cqr.count_color_on_face(f, c)
                if n > n_max:
                    n_max = n
                    f_max = f
                    c_max = c

        assert f_max and c_max  # mypy
        return f_max, c_max
