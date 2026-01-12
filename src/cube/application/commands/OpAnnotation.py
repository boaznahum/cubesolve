"""Operator annotation support."""

from collections.abc import Iterable, Iterator
from contextlib import contextmanager, nullcontext
from typing import (
    TYPE_CHECKING,
    Callable,
    ContextManager,
    Generator,
    Literal,
    Tuple,
    TypeAlias,
)

from cube.application.exceptions.app_exceptions import InternalSWError
from cube.application.markers import MarkerConfig
from cube.domain.algs.Algs import Algs
from cube.domain.model import Corner, Edge, Part, PartColorsID, PartEdge, PartSlice

from .AnnWhat import AnnWhat

if TYPE_CHECKING:
    from .Operator import Operator

_OP: TypeAlias = "Operator"

_SLice_Tracking_UniqID: int = 0

_HEAD: TypeAlias = str | Callable[[], str] | None
_HEADS = Tuple[_HEAD, _HEAD, _HEAD] | None

_ANN_BASE_ELEMENT: TypeAlias = Part | PartColorsID | PartSlice | PartEdge

_ANN_ELEMENT_0: TypeAlias = _ANN_BASE_ELEMENT | Iterator[_ANN_BASE_ELEMENT] | Iterable[_ANN_BASE_ELEMENT] | Callable[
    [], _ANN_BASE_ELEMENT]

_ANN_ELEMENT_1: TypeAlias = _ANN_ELEMENT_0 | Iterator[_ANN_ELEMENT_0] | Iterable[_ANN_ELEMENT_0] | Callable[
    [], _ANN_ELEMENT_0]

SupportsAnnotation: TypeAlias = _ANN_ELEMENT_1 | Iterator[_ANN_ELEMENT_1] | Iterable[_ANN_ELEMENT_1] | Callable[
    [], _ANN_ELEMENT_1]


class OpAnnotation:

    def __init__(self, op: _OP) -> None:
        super().__init__()
        self.op = op
        self.cube = op.cube

    @property
    def animation_on(self):
        return self.op.animation_enabled

    # @contextmanager
    def _w_slice_edges_annotate(self, _edges: Iterable[Tuple[PartEdge, bool, MarkerConfig]],
                                text: _HEADS | None = None):

        """
        Annotate moved slice
        :param _edges:  [Slice, fixed/moved, marker], not consumed if animation is off
         see
        :return:
        """

        op = self.op
        mm = self.cube.sp.marker_manager

        global _SLice_Tracking_UniqID

        # now consume iterator
        slices = [*_edges]

        def _key(_i):
            return "annotation_track" + str(abs(_i))

        #                  type,         key_index, marker_name
        slots: list[Tuple[Literal[1, 2, 3], int, str]] = []
        s: Tuple[PartEdge, bool, MarkerConfig]
        for s in slices:
            _slice: PartEdge = s[0]
            fixed = s[1]
            marker = s[2]

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
                slots.append((_type, -_SLice_Tracking_UniqID, key))
                mm.add_marker(_slice, key, marker, moveable=False)
                _slice.f_attributes[key] = key
            else:
                slots.append((_type, _SLice_Tracking_UniqID, key))
                mm.add_marker(_slice, key, marker, moveable=True)
                _slice.c_attributes[key] = key

        has_text = text and any(text)
        if has_text:
            assert text
            _text = []
            for _t in text:
                if callable(_t):
                    _t = _t()
                _text.append(_t)
            op.app_state.animation_text.push_heads(_text[0], _text[1], _text[2])
        op.play(Algs.AN)

        try:
            yield None
        finally:

            cqr = self.cube.cqr

            if has_text:
                op.app_state.animation_text.pop_heads()

            cube = self.cube
            for slot in slots:

                i = slot[1]
                _type = slot[0]
                marker_name = slot[2]

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

                # TODO [#15]: Marker cleanup fails during OpAborted - see __todo_solvers.md
                e = cqr.find_slice_edge(parts, _c_pred(i, key))

                if i < 0:
                    # if have a bug, nested annimation in __fixed_edge, so key already deleted
                    mm.remove_marker(e, marker_name, moveable=False)
                    del e.f_attributes[key]
                else:
                    mm.remove_marker(e, marker_name, moveable=True)
                    del e.c_attributes[key]

            op.play(Algs.AN)

    def annotate(self, *elements: Tuple[SupportsAnnotation, AnnWhat],
                 h1: _HEAD = None,
                 h2: _HEAD = None,
                 h3: _HEAD = None,
                 animation: bool = True) -> ContextManager[None]:

        """
        Annotate moved slice
        :param h1: tet headline 1
        :param h2: tet headline 2
        :param h3: tet headline 3, preserved for alg
        :param elements: iterators/iterable are consumed once and only once  if animation is  enabled
                AnnWhat.Moved track element when it moved around
                AnnWhat.FixedPosition annotate at fixed location
                if PartColorsID is specified:
                  if by position, element is searched by position(it's destination) and racked by AnnWhat.Position
                  otherwise, current location is searched and tracked by AnnWhat.FixedPosition

        :param animation:
        :return:
        """
        on = self.op.animation_enabled

        if (not on) or (not animation):
            return nullcontext()
        else:
            return self._annotate(*elements, h1=h1, h2=h2, h3=h3, animation=animation)

    @contextmanager
    def _annotate(self, *elements: Tuple[SupportsAnnotation, AnnWhat],
                  h1: _HEAD = None,
                  h2: _HEAD = None,
                  h3: _HEAD = None,
                  animation: bool = True) -> Generator[None, None, None]:

        global _SLice_Tracking_UniqID

        edges: list[Tuple[PartEdge, bool, MarkerConfig]] = []
        cube = self.cube
        mf = cube.sp.marker_factory

        # we invoke a specific method, to stop recursively check for type
        # we already know the type

        def process_slice_edge(_e: PartEdge, what: AnnWhat):
            if what == AnnWhat.Moved:
                by_position = False
            elif what == AnnWhat.FixedPosition:
                by_position = True
            else:
                raise InternalSWError("AnnWhat.Both is applicable only for Part or PartColorID")

            if by_position:
                marker = mf.c2()  # Destination marker (stays at position)
            else:
                marker = mf.c1()  # Moved marker (follows piece)

            edges.append((_e, by_position, marker))

        def process_slice(s: PartSlice, what: AnnWhat):
            part_edge: PartEdge
            for part_edge in s.edges:
                process_slice_edge(part_edge, what)

        def process_part(e: Part, what: AnnWhat):
            s: PartSlice
            for s in e.all_slices:
                process_slice(s, what)

        def process_element(e: SupportsAnnotation, _what: AnnWhat):

            # check for clor id before iterator iterable
            if isinstance(e, frozenset):  # PartColorsID
                ex : frozenset = e # satisfy pyright
                part: Part
                if _what in [AnnWhat.Moved, AnnWhat.Both]:
                    part = cube.find_part_by_colors(ex)
                    process_part(part, AnnWhat.Moved)
                if _what in [AnnWhat.FixedPosition, AnnWhat.Both]:
                    part = cube.find_part_by_pos_colors(ex)
                    process_part(part, AnnWhat.FixedPosition)

            elif isinstance(e, (Iterable, Iterator)):
                for ee in e:
                    process_element(ee, _what)  # type: ignore

            elif isinstance(e, Part):
                if _what == AnnWhat.Both:
                    process_part(e, AnnWhat.Moved)
                    process_part(e, AnnWhat.FixedPosition)
                elif _what == AnnWhat.Moved:
                    process_part(e, AnnWhat.Moved)
                else:
                    process_part(e, AnnWhat.FixedPosition)

            elif isinstance(e, PartSlice):
                process_slice(e, _what)

            elif isinstance(e, PartEdge):
                # finally someone need to do the work
                process_slice_edge(e, _what)

            elif callable(e):
                process_element(e(), _what)

            else:
                raise InternalSWError(f"Unknown type {type(e)}")

        for e, what in elements:
            process_element(e, what)

        # if movable:
        #     for s in movable:
        #         edges.append((s.edge, False, VMarker.C1))
        #
        # if fixed:
        #     for s in fixed:
        #         edges.append((s.edge, True, VMarker.C2))

        yield from self._w_slice_edges_annotate(edges,
                                                text=(h1, h2, h3))
