from typing import Callable, Any, TypeAlias

from cube.application import config
from cube.domain.model import Color, CenterSlice, CenterSliceIndex
from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.model.CubeQueries2 import Pred
from cube.domain.model.VMarker import viewer_add_view_marker, VMarker

_TRACKER_KEY_PREFIX = "_nxn_centers_track:"

_FaceSearcher = Callable[[], Face]

_FaceLoc: TypeAlias = "FaceTracker"


class FaceTracker:
    _tracer_unique_id: int = 0

    def __init__(self, color: Color, tracker: _FaceSearcher) -> None:
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

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def by_pred(cube: Cube, color: Color, pred: Pred[Face]) -> _FaceLoc:

        t: _FaceSearcher = lambda: cube.cqr.find_face(pred)

        return FaceTracker(color, t)

    @staticmethod
    def by_center_piece(_slice: CenterSlice) -> _FaceLoc:

        """
        Put a marker on __slice and track it
        :param _slice:
        :return:
        """

        FaceTracker._tracer_unique_id += 1

        key = _TRACKER_KEY_PREFIX + str(_slice.color) + str(FaceTracker._tracer_unique_id)
        edge = _slice.edge
        edge.c_attributes[key] = True

        if config.SOLVER_ANNOTATE_TRACKERS:
            viewer_add_view_marker(edge.c_attributes, VMarker.C0)  # to debug if alg move trackers

        def _slice_pred(s: CenterSlice):
            return key in s.edge.c_attributes

        def _face_pred(_f: Face):
            return _f.cube.cqr.find_slice_in_face_center(_f, _slice_pred) is not None

        color = _slice.color
        cube = _slice.parent.cube

        return FaceTracker.by_pred(cube, color, _face_pred)

    @staticmethod
    def search_color_and_track(face: Face, color: Color):
        """
        Find slice on face that has a specific color and track it
        :param face:
        :param color:
        :return:
        """

        _slice = face.cube.cqr.find_slice_in_face_center(face, lambda s: s.color == color)
        assert _slice

        return FaceTracker.by_center_piece(_slice)

    @staticmethod
    def search_by_index_and_track(f: Face, rc: CenterSliceIndex) -> _FaceLoc:

        # Why can't we track by slice index ? because when moving from face to face
        #  index may be changed
        _slice = f.center.get_center_slice(rc)
        return FaceTracker.by_center_piece(_slice)

    @staticmethod
    def track_odd(f: Face) -> _FaceLoc:

        cube = f.cube
        n_slices = cube.n_slices

        assert n_slices % 2  # see comment below
        rc = (n_slices // 2, n_slices // 2)

        # only middle in odd, doesn't change index when moving from face to face

        #        return self._track_slice(f, rc)
        color = f.center.get_center_slice(rc).color

        # This can be done only on odd cube and indexes n/2, n/2
        # because when moving from face to face slice coordinate are changed
        # and only on odd cube center slice is unique !!!
        def pred(_f: Face):
            return _f.center.get_center_slice(rc).color == color

        return FaceTracker.by_pred(cube, color, pred)

    def track_opposite(self) -> "FaceTracker":

        f: FaceTracker = self

        f_color = f.color

        cube = f.face.cube

        second_color = cube.original_layout.opposite_color(f_color)

        def _pred() -> Face:
            _f: Face
            return cube.cqr.find_face(lambda _f: _f.opposite is f.face)

        return FaceTracker(second_color, _pred)

    @staticmethod
    def is_track_slice(s: CenterSlice):

        for k in s.edge.c_attributes.keys():
            if isinstance(k, str) and k.startswith(_TRACKER_KEY_PREFIX):
                return True

        return False

    @staticmethod
    def remove_face_track_slices(f: Face):
        """
        Track slices prevent swapping of whole slices and big blocks
        :param f:
        :return:
        """
        for s in f.center.all_slices:
            cs = s.edge.c_attributes
            for k in [*cs.keys()]:  # need to copy, we modify it
                if isinstance(k, str) and k.startswith(_TRACKER_KEY_PREFIX):
                    del cs[k]
