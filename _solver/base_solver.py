from contextlib import contextmanager
from enum import unique, Enum
from typing import Tuple, Callable

from _solver.isolver import ISolver
from algs.algs import Algs
from model.cube import Cube, CubeSupplier
from model.cube_face import Face
from cube_operator import Operator
from model.cube_queries import CubeQueries
from model.elements import Part, PartColorsID, CenterSlice, EdgeSlice

_SLice_Tracking_UniqID: int = 0


@unique
class AnnWhat(Enum):
    """
    If color is given , find its actual location and track it where it goes
    If part is given find it actual location and track it where it goes
    """
    FindLocationTrackByColor = 1
    Postion = 2


class SolverElement(CubeSupplier):
    __slots__ = ["_solver"]

    _solver: ISolver

    def __init__(self, solver: ISolver) -> None:
        self._solver = solver

    def debug(self, *args):
        self._solver.debug(args)

    @property
    def cube(self) -> Cube:
        return self._solver.cube

    @property
    def op(self) -> Operator:
        return self._solver.op

    # noinspection PyUnresolvedReferences
    @property
    def _cmn(self) -> "CommonOp":  # type: ignore
        return self._solver.cmn

    @property
    def white_face(self) -> Face:
        return self._cmn.white_face

    @property
    def running_solution(self):
        return self._solver.running_solution

    def _annotate(self, *parts: Tuple[Part, bool], un_an: bool = False):

        """
        :param parts:  bool in tuple is  'annotated by fixed_location'
        :param un_an:
        :return:
        """

        if self.running_solution or not self.op.is_with_animation:
            return

        if un_an:
            for p in parts:
                p[0].un_annotate()
        else:
            for p in parts:
                p[0].annotate(p[1])

        self.op.op(Algs.AN)

    def _w_annotate(self, *elements: Tuple[Part | PartColorsID, bool]):

        """
        :param elements:  bool in tuple is  'annotated by fixed_location'
        if part is given we annotate the part (by color or by fixed), if color is given we search for it
        :param un_an:
        :return:
        """

        on = self.op.animation_enabled

        if not on:
            try:
                yield None
            finally:
                return

                # save colors, in case part move
        colors: list[PartColorsID] = []
        # save parts, in color changed
        parts: list[Part] = []
        for e in elements:
            pc: Part | PartColorsID = e[0]

            if isinstance(pc, frozenset):
                colors.append(pc)
                parts.append(self.cube.find_part_by_colors(pc))
            else:
                colors.append(pc.colors_id_by_color)
                parts.append(pc)

        self._annotate(*zip(parts, [p[1] for p in elements]))
        try:
            yield None
        finally:
            new_parts: list[Part] = []
            for i, e in enumerate(elements):
                if e[1]:  # by fixed location
                    new_parts.append(parts[i])
                else:
                    new_parts.append(self.cube.find_part_by_colors(colors[i]))

            self._annotate(*zip(new_parts, [p[1] for p in elements]), un_an=True)

    @contextmanager
    def w_annotate(self, *elements: Tuple[Part | PartColorsID, bool]):
        yield from self._w_annotate(*elements)

    @contextmanager
    def w_annotate2(self, *elements: Tuple[Part | PartColorsID, AnnWhat]):

        """
        :param elements:  bool in tuple is  'annotated by fixed_location'
        if part is given we annotate the part (by color or by fixed), if color is given we search for it
        :param un_an:
        :return:
        """

        on = self.op.animation_enabled

        if not on:
            try:
                yield None
            finally:
                return

        what_to_track: list[Tuple[PartColorsID, bool]] = []
        for e in elements:
            pc: Part | PartColorsID = e[0]
            what: AnnWhat = e[1]

            c: PartColorsID
            by_color: bool
            if isinstance(pc, frozenset):
                c = pc
            else:
                c = pc.colors_id_by_color

            if what == AnnWhat.FindLocationTrackByColor:
                by_position = False
            elif what == AnnWhat.Postion:
                by_position = True
            else:
                assert False

            what_to_track.append((c, by_position))

        yield from self._w_annotate(*what_to_track)


    @contextmanager
    def w_center_slice_annotate(self, *slices: CenterSlice, animation=True):

        """
        Annotate moved slice
        :param animation:
        :param elements:  bool in tuple is  'annotated by fixed_location'
        if part is given we annotate the part (by color or by fixed), if color is given we search for it
        :param un_an:
        :return:
        """

        on = self.op.animation_enabled

        global _SLice_Tracking_UniqID

        if (not on) or (not animation):
            try:
                yield None
            finally:
                return

        ids = []
        s: CenterSlice
        for s in slices:
            _SLice_Tracking_UniqID += 1
            ids.append(_SLice_Tracking_UniqID)
            s.edge.c_attributes["annotation"] = True
            s.edge.c_attributes["annotation_track"] = _SLice_Tracking_UniqID

        self.op.op(Algs.AN)

        try:
            yield None
        finally:

            cube = self.cube
            for i in ids:
                s = CubeQueries.find_center_slice(cube, lambda _s : i == _s.edge.c_attributes["annotation_track"])
                del s.edge.c_attributes["annotation"]
                del s.edge.c_attributes["annotation_track"]

            self.op.op(Algs.AN)

    @contextmanager
    def w_edge_slice_annotate(self, face: Face, *slices: EdgeSlice, animation=True):

        """
        Annotate moved slice
        :param face:
        :param animation:
        :param elements:  bool in tuple is  'annotated by fixed_location'
        if part is given we annotate the part (by color or by fixed), if color is given we search for it
        :param un_an:
        :return:
        """

        on = self.op.animation_enabled

        global _SLice_Tracking_UniqID

        if (not on) or (not animation):
            try:
                yield None
            finally:
                return

        ids: list[int] = []
        for s in slices:
            _SLice_Tracking_UniqID += 1
            ids.append(_SLice_Tracking_UniqID)
            s.get_face_edge(face).c_attributes["annotation"] = True
            s.get_face_edge(face).c_attributes["annotation_track"] = _SLice_Tracking_UniqID

        self.op.op(Algs.AN)

        try:
            yield None
        finally:

            def _slice_pred(_i: int) -> Callable[[EdgeSlice], bool]:

                def _pred(s: EdgeSlice):
                    for e in s.edges:
                        if e.c_attributes["annotation_track"] == i:
                            del e.c_attributes["annotation"]
                            del e.c_attributes["annotation_track"]
                            return True
                    return False

                return _pred

            cube = self.cube
            for i in ids:
                CubeQueries.find_slice_in_cube_edges(cube, _slice_pred(i))

            self.op.op(Algs.AN)
