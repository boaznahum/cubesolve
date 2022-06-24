from collections.abc import Iterable, Iterator
from contextlib import contextmanager, AbstractContextManager
from enum import unique, Enum
from typing import Tuple, Literal, Optional, TypeAlias, Callable

from _solver.isolver import ISolver
from algs.algs import Algs
from cube_operator import Operator
from model.cube import Cube, CubeSupplier
from model.cube_face import Face
from model.cube_queries import CubeQueries
from model.elements import Part, PartColorsID, CenterSlice, EdgeSlice, PartSlice, Corner, Edge, PartEdge
from viewer.viewer_markers import VMarker, VIEWER_ANNOTATION_KEY

_SLice_Tracking_UniqID: int = 0

_HEAD: TypeAlias = Optional[str|Callable[[], str]]
_HEADS = Optional[Tuple[_HEAD, _HEAD, _HEAD]]


@unique
class AnnWhat(Enum):
    """
    If color is given , find its actual location and track it where it goes
    If part is given find it actual location and track it where it goes
    """
    FindLocationTrackByColor = 1
    Position = 2


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

    def w_annotate(self, *elements: Tuple[Part | PartColorsID, bool],
                   h1=None,
                   h2=None,
                   h3=None) -> AbstractContextManager:
        return self._w_annotate(*elements, text=(h1, h2, h3))

    @property
    def animation_on(self):
        return self.op.animation_enabled

    # @contextmanager
    def _w_slice_edges_annotate(self, _edges: Iterable[Tuple[PartEdge, bool, VMarker]],
                                text: _HEADS = None,
                                animation=True):

        """
        Annotate moved slice
        :param animation:
        :param _edges:  [Slice, fixed/moved, marker], not consumed if animation is off
         see
        :return:
        """

        op = self.op

        on = op.animation_enabled
        if (not on) or (not animation):
            try:
                yield None
            finally:
                return

        global _SLice_Tracking_UniqID

        annotation_key = VIEWER_ANNOTATION_KEY

        # now consume iterator
        slices = [*_edges]

        def _key(_i):
            return "annotation_track" + str(abs(_i))

        slots: list[Tuple[Literal[1, 2, 3], int]] = []
        s: Tuple[PartEdge, bool, VMarker]
        for s in slices:
            _slice: PartEdge = s[0]
            fixed = s[1]
            marker = s[2]  # see view_markers.py

            _SLice_Tracking_UniqID += 1

            part: Part = _slice.parent.parent
            _type: Literal[1, 2, 3]

            if isinstance(part, Corner):
                _type = 1
            elif isinstance(part, Edge):
                _type = 2
            else:
                _type = 3

            # because it can be nested or overlap, we add the index to the key

            key = _key(_SLice_Tracking_UniqID)
            if fixed:
                _slice.f_attributes[annotation_key] = marker
                _slice.f_attributes[key] = key
                slots.append((_type, -_SLice_Tracking_UniqID))
            else:
                slots.append((_type, _SLice_Tracking_UniqID))
                _slice.c_attributes[annotation_key] = marker
                _slice.c_attributes[key] = key

        has_text = text and any(text)
        if has_text:
            assert text
            _text = []
            for _t  in text:
                if isinstance(_t, Callable):
                    _t = _t()
                _text.append(_t)
            op.app_state.animation_text.push_heads(_text[0], _text[1], _text[2])
        op.op(Algs.AN)

        try:
            yield None
        finally:

            if has_text:
                op.app_state.animation_text.pop_heads()

            cube = self.cube
            for slot in slots:

                i = slot[1]
                _type = slot[0]

                def _c_pred(_i, _key):

                    if _i < 0:
                        def _pred(_e: PartEdge) -> bool:
                            return _key == _e.f_attributes.get(_key)

                    else:
                        def _pred(_e: PartEdge) -> bool:
                            return _key == _e.c_attributes.get(_key)

                    _pred.__doc__ = f"Find {i}"

                    return _pred

                parts: Iterable[Part]

                if _type == 1:  # Corner
                    parts = cube.corners
                elif _type == 2:  # Edge
                    parts = cube.edges
                else:
                    parts = cube.centers

                key = _key(i)

                try:
                    e = CubeQueries.find_slice_edge(parts, _c_pred(i, key))
                except:
                    print("")
                    raise

                if i < 0:
                    # if have a bug, nested annimation in __fixed_edge, so key already deleted

                    # del e.f_attributes[annotation_key]
                    e.f_attributes.pop(annotation_key, None)

                    del e.f_attributes[key]
                else:
                    # del e.c_attributes[annotation_key]
                    e.c_attributes.pop(annotation_key, None)
                    del e.c_attributes[key]

            op.op(Algs.AN)

    @contextmanager
    def w_center_slice_annotate(self, *, movable: Iterable[CenterSlice] | Iterator[CenterSlice] | None = None,
                                fixed: Iterable[CenterSlice] | Iterator[CenterSlice] | None = None,
                                animation=True):

        """
        Annotate moved slice
        :param movable: not consumed if animation is off
        :param fixed: not consumed if animation is off
        :param animation:
        :return:
        """

        on = self.op.animation_enabled

        global _SLice_Tracking_UniqID

        if (not on) or (not animation):
            try:
                yield None
            finally:
                return

        edges: list[Tuple[PartEdge, bool, VMarker]] = []

        if movable:
            for s in movable:
                edges.append((s.edge, False, VMarker.C1))

        if fixed:
            for s in fixed:
                edges.append((s.edge, True, VMarker.C2))

        yield from self._w_slice_edges_annotate(edges, animation=animation)

    @contextmanager
    def w_edge_slice_annotate(self, face: Face, *slices: EdgeSlice, animation=True):

        """
        Annotate moved slice
        :param face:
        :param animation:
        if part is given we annotate the part (by color or by fixed), if color is given we search for it
        :return:
        """

        on = self.op.animation_enabled

        if (not on) or (not animation):
            try:
                yield None
            finally:
                return

        edges: list[Tuple[PartEdge, bool, VMarker]] = []

        for s in slices:
            edges.append((s.get_face_edge(face), False, VMarker.C1))

        yield from self._w_slice_edges_annotate(edges, animation=animation)

    @contextmanager
    def _none(self):
        try:
            yield None
        finally:
            return

    @contextmanager
    def w_annotate2(self, *elements: Tuple[Part | PartColorsID, AnnWhat],
                    animation=True,
                    text: _HEADS = None):

        """
        :param text:
        :param animation:
        :param elements:  bool in tuple is  'annotated by fixed_location'
        if part is given we annotate the part (by color or by fixed), if color is given we search for it
        :return:
        """

        on = self.op.animation_enabled

        if (not on) or (not animation):
            try:
                yield None
            finally:
                return

        edges: list[Tuple[PartEdge, bool, VMarker]] = []

        cube = self.cube

        for e in elements:
            pc = e[0]
            w: AnnWhat = e[1]

            by_position = w == AnnWhat.Position

            part: Part

            if isinstance(pc, frozenset):

                if by_position:
                    part = cube.find_part_by_pos_colors(pc)
                else:
                    part = cube.find_part_by_colors(pc)
            else:
                part = pc

            if by_position:
                marker = VMarker.C2
            else:
                marker = VMarker.C1

            s: PartSlice
            for s in part.all_slices:
                for eg in s.edges:
                    edges.append((eg, by_position, marker))

        yield from self._w_slice_edges_annotate(edges, animation=animation, text=text)

    def _w_annotate(self, *elements: Tuple[Part | PartColorsID, bool],
                    text: _HEADS = None) -> AbstractContextManager:

        """
        :param elements:  bool in tuple is  'annotated by fixed_location'
        if part is given we annotate the part (by color or by fixed), if color is given we search for it
        :param un_an:
        :return:
        """

        on = self.op.animation_enabled

        if not on:
            return self._none()

        _elements: list[Tuple[Part | PartColorsID, AnnWhat]] = []

        for e in elements:

            if e[1]:
                _elements.append((e[0], AnnWhat.Position))
            else:
                _elements.append((e[0], AnnWhat.FindLocationTrackByColor))

        return self.w_annotate2(*_elements, text=text)
