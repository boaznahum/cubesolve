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

from .FaceName import FaceName
from .PartSlice import CenterSlice, EdgeWing, PartSlice
from .PartEdge import PartEdge
from .Center import Center
from .Edge import Edge
from .SliceName import SliceName
from .SuperElement import SuperElement
from cube.utils.Cache import CacheManager
from ..geometric.slice_layout import SliceLayout

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from .Cube import Cube
    from cube.domain.geometric.cube_walking import CubeWalkingInfo

_Cube: TypeAlias = "Cube"


class Slice(SuperElement):
    __slots__ = [
        "_name",
        "_slice_index",
        "_left", "_left_bottom", "_bottom",
        "_right_bottom", "_right", "_right_top",
        "_top", "_left_top",
        "_edges", "_centers",
        "_for_debug",
        "_cache_manager",  # CacheManager instance for this slice (respects config.enable_cube_cache)
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

        self._slice_layout : SliceLayout = cube.layout.get_slice(name)

        # Create cache manager for this slice (CacheManagerImpl or CacheManagerNull based on config)
        self._cache_manager = CacheManager.create(cube.config)



        self.set_parts(
            left_top, top, right_top,
            right,
            right_bottom, bottom, left_bottom,
            left
        )

    def _get_walking_info(self) -> "CubeWalkingInfo":
        """
        Get the CubeWalkingInfo for this slice.

        Caching is handled at two levels:
        1. SliceLayout caches CubeWalkingInfoUnit (size-independent topology)
        2. SizedCubeLayout caches CubeWalkingInfo (size-dependent coordinates)

        Returns:
            CubeWalkingInfo for this slice (cached at SizedCubeLayout level)
        """
        return self.cube.sized_layout.create_walking_info(self._name)

    def _get_slices_by_index(self, slice_index: int) -> Tuple[Sequence[EdgeWing], Sequence[CenterSlice]]:
        """
        Get all edge wings and center slices for a given slice index.

        Performance Optimization:YES
        ========================
        This method is called TWICE per slice per quarter turn:
        1. In _rotate() to get elements for rotation (line ~339)
        2. In _update_texture_directions_after_rotate() (line ~473)

        For a 5×5 cube (n_slices=3), rotating M slice once:
        - 3 slice indices × 2 calls each = 6 calls to this method

        Each call without caching:
        - Calls _get_walking_info() (which may itself be cached)
        - Iterates over 4 faces
        - For each face: n_slices center lookups + 1 edge lookup
        - Creates new EdgeWing and CenterSlice lists

        Cache Strategy:
        - Uses CacheManager from cube.layout (respects config.enable_cube_cache)
        - Keyed by (slice_name, slice_index) - e.g., (SliceName.M, 0)
        - The returned EdgeWing/CenterSlice objects are REFERENCES to actual cube pieces
        - They don't need invalidation because they point to the same objects
        - The cache just avoids recomputing WHICH objects to return

        Why References Are Safe:
        - The EdgeWing and CenterSlice objects returned are the actual cube pieces
        - When we rotate, we modify their colors, not their identity
        - Next rotation will get the same objects (with new colors) - that's correct!

        Args:
            slice_index: Which slice (0 to n_slices-1)

        Returns:
            Tuple of (edge_wings, center_slices) for all 4 faces
        """
        def compute_slices() -> Tuple[Sequence[EdgeWing], Sequence[CenterSlice]]:
            walk_info = self._get_walking_info()
            n_slices = self.n_slices

            edges: list[EdgeWing] = []
            centers: list[CenterSlice] = []

            for face_info in walk_info:
                # Get center slices using precomputed point function
                center: Center = face_info.face.center
                for slot in range(n_slices):
                    point = face_info.compute_point(slice_index, slot)
                    centers.append(center.get_center_slice(point))

                # Get edge wing using the stored edge and local slice index
                local_index = face_info.compute_point(slice_index, 0)[1] if face_info.face.is_bottom_or_top(face_info.edge) else face_info.compute_point(slice_index, 0)[0]
                edge_slice = face_info.edge.get_slice_by_ltr_index(face_info.face, local_index)
                edges.append(edge_slice)

            return edges, centers

        cache_key = ("Slice._get_slices_by_index", self._name, slice_index)  # e.g., ("...", SliceName.M, 0)
        cache = self._cache_manager.get(cache_key, tuple)

        return cache.compute(compute_slices)

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

        sp = self.cube.sp
        mm = sp.marker_manager
        mf = sp.marker_factory
        add_markers = sp.config.markers_config.DRAW_CENTER_INDEXES

        for i in s_range:

            elements: tuple[Sequence[EdgeWing], Sequence[CenterSlice]] = self._get_slices_by_index(i)

            # Rotate edges using 4-cycle reference rotation (no cloning needed)
            # Each EdgeWing has 2 PartEdges on 2 adjacent faces
            # Pattern: e0 ← e1 ← e2 ← e3 ← e0
            # This creates 2 independent 4-cycles for the 2 PartEdges per EdgeWing
            edges: Sequence[EdgeWing] = elements[0]

            # For slice rotation, adjacent edges share a face. We use this to
            # identify the 2 independent 4-cycles:
            # Cycle 1: e0[other_0] ← e1[other_1] ← e2[other_2] ← e3[other_3]
            #   where other_i = face NOT shared with edge[(i+1)%4]
            # Cycle 2: e0[shared_0] ← e1[shared_1] ← e2[shared_2] ← e3[shared_3]
            #   where shared_i = face shared with edge[(i+1)%4]

            # Get the shared/other faces for each edge
            shared_faces = []
            other_faces = []
            for idx in range(4):
                next_idx = (idx + 1) % 4
                shared = edges[idx].single_shared_face(edges[next_idx])
                other = edges[idx].get_other_face(shared)
                shared_faces.append(shared)
                other_faces.append(other)

            # Cycle 1: PartEdges on the "other" faces (not shared with next edge)
            PartEdge.rotate_4cycle(
                edges[0].get_face_edge(other_faces[0]),
                edges[1].get_face_edge(other_faces[1]),
                edges[2].get_face_edge(other_faces[2]),
                edges[3].get_face_edge(other_faces[3])
            )

            # Cycle 2: PartEdges on the "shared" faces
            PartEdge.rotate_4cycle(
                edges[0].get_face_edge(shared_faces[0]),
                edges[1].get_face_edge(shared_faces[1]),
                edges[2].get_face_edge(shared_faces[2]),
                edges[3].get_face_edge(shared_faces[3])
            )

            # Rotate PartSlice tracking data for edges
            PartSlice.rotate_4cycle_slice_data(edges[0], edges[1], edges[2], edges[3])

            # Rotate centers using 4-cycle reference rotation (no cloning needed)
            # For each position j, there's a 4-cycle of CenterSlices
            # Pattern: centers[j] ← centers[j+n] ← centers[j+2n] ← centers[j+3n] ← centers[j]
            centers: Sequence[CenterSlice] = elements[1]
            for j in range(n_slices):
                # Get the 4 CenterSlices in the cycle
                c0 = centers[j]
                c1 = centers[j + n_slices]
                c2 = centers[j + 2 * n_slices]
                c3 = centers[j + 3 * n_slices]

                # Each CenterSlice has 1 PartEdge
                PartEdge.rotate_4cycle(c0.edge, c1.edge, c2.edge, c3.edge)

                # Rotate PartSlice tracking data for centers
                PartSlice.rotate_4cycle_slice_data(c0, c1, c2, c3)

                if add_markers:
                    marker_name = f"idx_{j}"
                    # Handle markers for all 4 centers in the cycle
                    for c in [c0, c1, c2, c3]:
                        char = mf.char(str(j))
                        if j < 3:
                            mm.add_marker(c.edge, marker_name, char, moveable=False)
                        else:
                            mm.remove_marker(c.edge, marker_name, moveable=False)

    def rotate(self, n=1, slices_indexes: Iterable[int] | None = None):
        """
        Rotate the slice n quarter turns.

        Args:
            n: Number of quarter turns (positive = clockwise looking at rotation face from outside)
            slices_indexes: Which slice indices to rotate, or None for all [0, n_slices-1]

        Direction Inversion Explanation:
        ================================
        We invert n because _rotate() cycles content OPPOSITE to traversal order.

        Example - M slice (rotates like L, clockwise looking from left):

        1. GEOMETRIC TRAVERSAL ORDER (clockwise around L face):
           Looking at L from outside, clockwise visits: U → F → D → B → U

                    U
                    ↓
               B ←──L──→ F      Clockwise: U → F → D → B
                    ↓
                    D

        2. _rotate() CYCLING MECHANISM:
           Elements collected in traversal order: [e_U, e_F, e_D, e_B]
           _rotate() does: e0 ← e1 ← e2 ← e3 ← e0

           So: e_U ← e_F ← e_D ← e_B ← e_U
           Meaning: U gets F's content, F gets D's, D gets B's, B gets U's

        3. RESULTING CONTENT MOVEMENT:
           Content flows: U → B → D → F → U (OPPOSITE of traversal!)

        4. CORRECT M ROTATION (like L clockwise):
           Content should flow: U → F → D → B → U

        5. SOLUTION:
           Invert n so _rotate() runs in reverse, giving correct direction:
           Content flows: U → F → D → B → U ✓

        This applies uniformly to M, E, and S slices.
        """

        if n == 0:
            return

        # Invert direction: _rotate() cycles opposite to geometric traversal order
        # See docstring above for detailed explanation with diagrams
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

    def compute_slice_index(self,
            face: FaceName,
            coord: tuple[int, int],
            n_slices: int
    ) -> int:
        """
        Compute the 0-based slice index for a given face and coordinate.

        Args:
            face: The face where the coordinate originates
            coord: 0-based (row, col) on the face
            n_slices: Number of inner slices (cube.n_slices = cube.size - 2)

        Returns:
            0-based slice index in range [0, n_slices-1]
        """
        row, col = coord
        computer = self._slice_layout.create_slice_index_computer(face)
        return computer(row, col, n_slices)
