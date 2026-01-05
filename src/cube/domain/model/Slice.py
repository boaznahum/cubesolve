"""
Slice class for cube rotations.

This is the SINGLE SOURCE OF TRUTH for slice geometry. Other code should
derive slice information from here rather than hardcoding cycles/tables.

================================================================================
CUBE ORIENTATION AND AXES
================================================================================

Standard cube orientation (viewer looking at Front face):

                 +Y (Up)
                  │
                  │    +Z (Back, into screen)
                  │   /
                  │  /
                  │ /
                  │/
    +X (Right) ──┼────────
                /│
               / │
              /  │
             /   │
   -Z (Front, toward viewer)

Face layout (unfolded):

              ┌─────┐
              │  U  │
              │     │
        ┌─────┼─────┼─────┬─────┐
        │  L  │  F  │  R  │  B  │
        │     │     │     │     │
        └─────┼─────┼─────┴─────┘
              │  D  │
              │     │
              └─────┘

================================================================================
SLICE DEFINITIONS
================================================================================

Each slice rotates the 4 faces PERPENDICULAR to its axis.
The axis faces (and their opposites) stay in place but don't rotate.

┌──────────┬───────────┬─────────────────┬───────────────────────────────────┐
│  Slice   │   Axis    │  Affects Faces  │  Rotation Direction               │
├──────────┼───────────┼─────────────────┼───────────────────────────────────┤
│    M     │   L ↔ R   │   F, U, B, D    │  Like L (clockwise facing L)      │
│    E     │   U ↔ D   │   F, R, B, L    │  Like D (clockwise facing D)      │
│    S     │   F ↔ B   │   U, R, D, L    │  Like F (clockwise facing F)      │
└──────────┴───────────┴─────────────────┴───────────────────────────────────┘

API Reference:
  - Algs.M.get_face_name() → L  (M rotates like L)
  - Algs.E.get_face_name() → D  (E rotates like D)
  - Algs.S.get_face_name() → F  (S rotates like F)

================================================================================
SLICE TRAVERSAL (used in _get_slices_by_index)
================================================================================

Each slice traverses 4 faces. The starting face and edge determine the
traversal order. Traversal uses edge.opposite(face) to find the next face.

M Slice (axis L-R):
~~~~~~~~~~~~~~~~~~
    Start: Front face, edge_bottom

           U
           ↑
    F → edge_bottom.opposite(F) → U → edge_bottom.opposite(U) → B → ... → D → F

    Traversal: F → U → B → D → F

         ┌───┐
         │ U │ ←─┐
         └─┬─┘   │
           │     │
    ┌──────↓─────┴───┐
    │ F    ↓    B    │   (L and R not shown - they're the axis faces)
    └──────↑─────────┘
           │
         ┌─┴─┐
         │ D │
         └───┘

E Slice (axis U-D):
~~~~~~~~~~~~~~~~~~
    Start: Right face, edge_left

    Traversal: R → B → L → F → R

    ┌───┬───┬───┬───┐
    │ L │ F │ R │ B │
    │ ← │ ← │ ← │ ← │←─┐
    └───┴───┴───┴───┘  │
      │                │
      └────────────────┘

    (U and D not shown - they're the axis faces)

S Slice (axis F-B):
~~~~~~~~~~~~~~~~~~
    Start: Up face, edge_left

    Traversal: U → R → D → L → U

         ┌───┐
    ┌───→│ U │
    │    └─┬─┘
    │      ↓
    │ ┌────┴────┐
    │ │ L     R │
    │ │ ↑     ↓ │
    │ └────┬────┘
    │      ↓
    │    ┌─┴─┐
    └────│ D │
         └───┘

    (F and B not shown - they're the axis faces)

================================================================================
RELATIONSHIP TO WHOLE-CUBE ROTATIONS (X, Y, Z)
================================================================================

Whole-cube rotations use slices internally:

┌────────┬─────────────────┬──────────────────────────────────────────────────┐
│ Whole  │ Implementation  │  Rotation Direction                              │
├────────┼─────────────────┼──────────────────────────────────────────────────┤
│   X    │ M' + R + L'     │  Like R (clockwise facing R)                     │
│   Y    │ E' + U + D'     │  Like U (clockwise facing U)                     │
│   Z    │ S + F + B'      │  Like F (clockwise facing F)                     │
└────────┴─────────────────┴──────────────────────────────────────────────────┘

API Reference:
  - Algs.X.get_face_name() → R  (X rotates like R, OPPOSITE of M's L!)
  - Algs.Y.get_face_name() → U  (Y rotates like U, OPPOSITE of E's D!)
  - Algs.Z.get_face_name() → F  (Z rotates like F, SAME as S's F!)

Direction Relationship:
  - M.face (L) is OPPOSITE to X.face (R) → opposite directions
  - E.face (D) is OPPOSITE to Y.face (U) → opposite directions
  - S.face (F) is SAME as Z.face (F) → same direction

This relationship is used to derive rotation cycles without hardcoding.

================================================================================
FACE CYCLES (derived from traversal)
================================================================================

Content flow during positive rotation (n=1):

  X rotation: D → F → U → B → D  (content on D moves to F, etc.)
  Y rotation: R → F → L → B → R  (content on R moves to F, etc.)
  Z rotation: L → U → R → D → L  (content on L moves to U, etc.)

These cycles can be derived from Slice traversal:
  1. Get the 4 faces from slice traversal
  2. Adjust direction based on slice.face vs whole_cube.face relationship

================================================================================
"""

from typing import TYPE_CHECKING, Iterable, Sequence, Tuple, TypeAlias

from .PartSlice import CenterSlice, EdgeWing, PartSlice
from .Center import Center
from .Edge import Edge
from .Face import Face
from .SliceName import SliceName
from .SuperElement import SuperElement

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from .Cube import Cube

_Cube: TypeAlias = "Cube"


class Slice(SuperElement):
    __slots__ = [
        "_name",
        "_slice_index",
        "_left", "_left_bottom", "_bottom",
        "_right_bottom", "_right", "_right_top",
        "_top", "_left_top",
        "_edges", "_centers",
        "_for_debug"

    ]

    def __init__(self, cube: _Cube, name: SliceName,
                 left_top: Edge, top: Center, right_top: Edge,
                 right: Center,
                 right_bottom: Edge, bottom: Center, left_bottom: Edge,
                 left: Center) -> None:
        super().__init__(cube)
        self._name: SliceName = name
        self._left = left
        self._left_bottom = left_bottom
        self._bottom = bottom
        self._right_bottom = right_bottom
        self._right = right
        self._right_top = right_top
        self._top = top
        self._left_top = left_top

        self._edges: Sequence[Edge] = [left_top, right_top, right_bottom, left_bottom]
        self._centers: Sequence[Center] = [top, left, bottom, right]

        self.set_parts(
            left_top, top, right_top,
            right,
            right_bottom, bottom, left_bottom,
            left
        )

    def _get_slices_by_index(self, slice_index: int) -> Tuple[Sequence[EdgeWing], Sequence[CenterSlice]]:
        # First we need to decide with which edge to start, to get consistent results
        current_edge: Edge  # this determines the direction of rotation
        current_index: int
        current_face: Face

        match self._name:
            case SliceName.M:  # over L, works
                current_face = self.cube.front
                current_edge = current_face.edge_bottom
                current_index = slice_index

            case SliceName.E:  # over D, works
                current_face = self.cube.right
                current_edge = current_face.edge_left
                current_index = slice_index

            case SliceName.S:  # over F, works
                current_face = self.cube.up
                current_edge = current_face.edge_left
                current_index = slice_index

            case _:
                raise ValueError(f"Unknown slice name: {self._name}")

        # noinspection PyUnboundLocalVariable no it is not
        assert current_face.is_edge(current_edge)

        n_slices = self.n_slices

        inv = self.inv

        # !!! we treat start index as in LTR coordinates on start face !!!
        edges: list[EdgeWing] = []
        centers: list[CenterSlice] = []
        for _ in range(4):
            # here start face handling

            center: Center = current_face.center

            _c: Sequence[CenterSlice]

            if current_face.is_bottom_or_top(current_edge):
                if current_face.is_top_edge(current_edge):
                    _c = [center.get_center_slice((inv(i), current_index)) for i in range(n_slices)]
                else:
                    _c = [center.get_center_slice((i, current_index)) for i in range(n_slices)]

            else:
                if current_face.is_right_edge(current_edge):
                    _c = [center.get_center_slice((current_index, inv(i))) for i in range(n_slices)]
                else:
                    _c = [center.get_center_slice((current_index, i)) for i in range(n_slices)]

            centers.extend(_c)

            edge_slice = current_edge.get_slice_by_ltr_index(current_face, current_index)
            edges.append(edge_slice)

            # PHYSICAL ALIGNMENT PROBLEM:
            # When rotating a slice, the user sees a visual line going around 4 faces.
            # Each face has its own internal storage order, so Face F's index 2 might
            # be Face U's index 0. But they must be PHYSICALLY ALIGNED - same visual line!
            #
            # SOLUTION: Use the shared edge as a BRIDGE between face ltr systems.
            # The edge translates: current_face ltr → edge index → next_face ltr
            # This preserves physical alignment across all 4 faces.
            #
            # See: docs/design2/edge-face-coordinate-system-approach2.md
            #
            next_edge: Edge = current_edge.opposite(current_face)
            next_face = next_edge.get_other_face(current_face)
            assert next_face.is_edge(next_edge)

            # Translate: current_face's ltr → edge internal index → next_face's ltr
            next_slice_index = next_edge.get_slice_index_from_ltr_index(current_face, current_index)
            current_index = next_edge.get_ltr_index_from_slice_index(next_face, next_slice_index)
            current_edge = next_edge
            current_face = next_face

        return edges, centers

    def _get_index_range(self, slices_indexes: Iterable[int] | int | None) -> Iterable[int]:
        """
            :param slices_indexes:         None=[0, n_slices-1]

            :return:
            """

        n_slices = self.n_slices

        if slices_indexes is None:
            return range(0, n_slices)

        if isinstance(slices_indexes, int):
            slices_indexes = [slices_indexes]

        for i in slices_indexes:
            assert 0 <= i <= self.n_slices - 1

        return slices_indexes

    def _rotate(self, slices_indexes: Iterable[int] | None):

        """
        :param slices_indexes:         None=[0, n_slices-1]

        :return:
        """

        s_range = self._get_index_range(slices_indexes)

        n_slices = self.n_slices

        for i in s_range:

            elements: tuple[Sequence[EdgeWing], Sequence[CenterSlice]] = self._get_slices_by_index(i)

            # rotate edges
            # e0 <-- e1 <-- e2 ... e[n-1]
            # e[n-1] <-- e0
            edges: Sequence[EdgeWing] = elements[0]
            prev: EdgeWing = edges[0]
            e0: EdgeWing = prev.clone()
            for e in edges[1:]:
                prev.copy_colors_ver(e)
                prev = e

            edges[-1].copy_colors_ver(e0)

            # rotate centers
            # c0 <-- c1 <-- c2 ... c[n-1]
            # c[n-1] <-- c0
            centers: Sequence[CenterSlice] = elements[1]
            for j in range(n_slices):  #
                prev_c: CenterSlice = centers[j]  # on the first face
                c0: CenterSlice = prev_c.clone()
                for fi in range(1, 4):  # 1 2 3
                    c = centers[j + fi * n_slices]
                    prev_c.copy_center_colors(c)
                    prev_c = c

                centers[j + 3 * n_slices].copy_center_colors(c0)

    def rotate(self, n=1, slices_indexes: Iterable[int] | None = None):

        """

        :param n:
        :param slices_indexes: [0..n-2-1] [0, n_slices-1] or None=[0, n_slices-1]
        :return:
        """

        if n == 0:
            return

        # TODO [#11]: BUG - M slice direction is inverted compared to standard notation
        # See: https://alg.cubing.net/?alg=m and https://ruwix.com/the-rubiks-cube/notation/advanced/
        if self._name != SliceName.M:
            n = -n

        def _p():
            # f: Face
            # for f in self.cube.faces:
            #     print(f, f.center._colors_id_by_colors, ",", end='')
            # print()
            pass

        _p()
        for _ in range(n % 4):
            self._rotate(slices_indexes)
            _p()
            self.cube.modified()
            # Update texture directions after each step (like Face.rotate)
            self._update_texture_directions_after_rotate(1, slices_indexes)

        _p()
        self.cube.reset_after_faces_changes()
        _p()
        self.cube.sanity()
        _p()

    def _update_texture_directions_after_rotate(self, quarter_turns: int, slices_indexes: Iterable[int] | None) -> None:
        """Update texture direction for stickers affected by slice rotation.

        Configuration is loaded from texture_rotation_config.yaml.

        Args:
            quarter_turns: Number of 90° rotations (already adjusted for direction)
            slices_indexes: Which slice indices were rotated
        """
        # Skip texture updates during query mode
        if self.cube._in_query_mode:
            return

        # Load config from YAML
        from cube.presentation.gui import texture_rotation_loader as trl
        slice_name = self._name.name  # SliceName.M -> "M"

        s_range = self._get_index_range(slices_indexes)

        for i in s_range:
            edges, centers = self._get_slices_by_index(i)

            # Update edge stickers
            for edge_wing in edges:
                for part_edge in edge_wing.edges:
                    face_name = part_edge.face.name.name
                    delta = trl.get_delta(slice_name, face_name)
                    if delta != 0:
                        part_edge.rotate_texture(quarter_turns * delta)

            # Update center stickers
            for center_slice in centers:
                part_edge = center_slice.edge
                face_name = part_edge.face.name.name
                delta = trl.get_delta(slice_name, face_name)
                if delta != 0:
                    part_edge.rotate_texture(quarter_turns * delta)

    def get_rotate_involved_parts(self, slice_indexes: int | Iterable[int] | None) -> Sequence[PartSlice]:

        """
        :param slice_indexes: [0..n-2-1] [0, n_slices-1] or None
        :return:
        """

        parts: list[PartSlice] = []

        s_range = self._get_index_range(slice_indexes)

        for i in s_range:
            elements: tuple[Sequence[EdgeWing], Sequence[CenterSlice]] = self._get_slices_by_index(i)

            parts.extend(elements[0])
            parts.extend(elements[1])

        return parts

    @property
    def slices(self) -> Iterable[PartSlice]:
        index = 0
        if index is None:
            for p in self._parts:
                yield from p.all_slices
        else:
            for e in self._edges:
                yield e.get_slice(index)

            n = self.cube.n_slices
            for c in self._centers:
                for i in range(n):
                    yield c.get_slice((i, index))
