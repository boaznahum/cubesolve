"""Cube layout implementation."""

from __future__ import annotations

from collections.abc import Collection, Iterator
from typing import TYPE_CHECKING, Mapping

from cube.domain.exceptions import InternalSWError
from cube.domain.geometric.FRotation import FUnitRotation
from cube.domain.model.Edge import Edge
from cube.domain.model.SliceName import SliceName
from cube.domain.geometric.cube_layout import (
    CubeLayout,
    _ADJACENT,
    _ALL_OPPOSITE,
    _OPPOSITE,
)
from cube.domain.geometric.Face2FaceTranslator import TransformType
from cube.domain.geometric.slice_layout import CLGColRow, SliceLayout, _SliceLayout
from cube.utils.config_protocol import ConfigProtocol, IServiceProvider
from cube.utils.Cache import CacheManager

from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Face import Face


class _CubeLayout(CubeLayout):
    """Concrete implementation of CubeLayout protocol.

    Manages a mapping of faces to colors, with support for:
    - Read-only layouts (like the BOY singleton)
    - Mutable layouts for comparison/manipulation
    - Geometric operations (opposite, adjacent faces)

    The face geometry (opposite, adjacent) is defined at the protocol level
    and shared by all implementations.
    """

    def __init__(self, read_only: bool, faces: Mapping[FaceName, Color],
                 sp: IServiceProvider) -> None:
        """Create a new CubeLayout.

        Args:
            read_only: If True, layout cannot be modified (used for BOY singleton).
            faces: Mapping of each face to its color.
            sp: Service provider for configuration access.
        """
        self._faces: dict[FaceName, Color] = dict(faces)
        self._read_only = read_only
        self._sp = sp
        self._edge_colors: Collection[frozenset[Color]] | None = None
        self._cache_manager = CacheManager.create(sp.config)

        self._slices: Mapping[SliceName, SliceLayout] = {
            SliceName.S: _SliceLayout(SliceName.S, self),
            SliceName.E: _SliceLayout(SliceName.E, self),
            SliceName.M: _SliceLayout(SliceName.M, self),
        }

        # Lazy-initialized internal 3x3 cube for geometry queries
        self._internal_cube: Cube | None = None
        self._creating_internal_cube: bool = False

    @property
    def config(self) -> ConfigProtocol:
        """Get configuration via service provider."""
        return self._sp.config

    @property
    def cache_manager(self) -> CacheManager:
        """Get the cache manager for this layout."""
        return self._cache_manager

    @property
    def _cube(self) -> "Cube":
        """Get internal 3x3 cube for geometry queries (lazy initialization).

        This cube is used to answer template-level geometry questions that
        require traversing face/edge relationships. It's created on first access.

        Raises:
            InternalSWError: If called during cube creation (cycle detected).
        """
        if self._internal_cube is not None:
            return self._internal_cube

        if self._creating_internal_cube:
            raise InternalSWError(
                "Circular dependency detected: CubeLayout._cube accessed while "
                "creating internal cube. This indicates a geometry method was "
                "called during Cube.__init__() that requires the internal cube."
            )

        # Create the internal 3x3 cube
        self._creating_internal_cube = True
        try:
            from cube.domain.model.Cube import Cube
            self._internal_cube = Cube(3, self._sp)
            # Set the layout directly (Cube doesn't accept layout in __init__)
            self._internal_cube._original_layout = self
        finally:
            self._creating_internal_cube = False

        return self._internal_cube

    def __getitem__(self, face: FaceName) -> Color:
        """Get the color for a specific face."""
        return self._faces[face]

    def get_slice(self, slice_name: SliceName) -> SliceLayout:
        return self._slices[slice_name]

    def colors(self) -> Collection[Color]:
        """Get all colors in this layout."""
        return [*self._faces.values()]

    def edge_colors(self) -> Collection[frozenset[Color]]:
        """Get all valid edge color combinations."""
        if self._edge_colors is not None:
            return self._edge_colors

        colors: set[frozenset[Color]] = set()

        for f1, c1 in self._faces.items():
            for f2, c2 in self._faces.items():
                if f1 is not f2:
                    if f2 is not _ALL_OPPOSITE[f1]:
                        c = frozenset((c1, c2))
                        colors.add(c)

        self._edge_colors = colors

        return self._edge_colors

    def opposite_color(self, color: Color) -> Color:
        """Get the color on the face opposite to the given color's face."""
        return self._faces[self.opposite(self._find_face(color))]

    def same(self, other: CubeLayout) -> bool:
        """Check if this layout is equivalent to another.

        Args:
            other: Another layout to compare with.

        Returns:
            True if layouts are equivalent, False otherwise.
        """
        # because this might be NxN in which center color have no meaning
        # we need to check
        for c in other.colors():
            if not self._is_face(c):
                return False

        # so it safe to continue !!!

        this = self.clone()

        # Check opposite colors
        # make sure that opposite colors on this, are the same in other layout
        for f1, f2 in _OPPOSITE.items():

            c1 = other[f1]
            c2 = other[f2]

            this_c1_face: FaceName = this._find_face(c1)
            this_c2_face = _ALL_OPPOSITE[this_c1_face]

            this_c2 = this._faces[this_c2_face]
            if c2 != this_c2:
                return False

        # find color of other front
        other_f_color: Color = other[FaceName.F]

        this_f_match = this._find_face(other_f_color)

        this._bring_face_to_front(this_f_match)
        assert this._faces[FaceName.F] == other_f_color

        # find UP color on other
        other_u_color = other[FaceName.U]

        this_u_match = this._find_face(other_u_color)
        if this_u_match == FaceName.B:
            return False  # on this it is on Back, can't match other layout

        this._bring_face_up_preserve_front(this_u_match)  # preserve front
        assert this._faces[FaceName.U] == other_u_color

        other_l_color = other[FaceName.L]

        this_l_color = this._faces[FaceName.L]

        if other_l_color != this_l_color:
            return False

        return True  # same layout

    def is_boy(self) -> bool:
        """Check if this layout matches the standard BOY color scheme."""
        from cube.domain.geometric import cube_boy
        return self.same(cube_boy.get_boy_layout(self._sp))

    def clone(self) -> _CubeLayout:
        """Create a mutable copy of this layout."""
        return _CubeLayout(False, self._faces, self._sp)

    def opposite(self, fn: FaceName) -> FaceName:
        """Get the face opposite to the given face."""
        return _ALL_OPPOSITE[fn]

    def is_adjacent(self, face1: FaceName, face2: FaceName) -> bool:
        """Check if two faces are adjacent (share an edge)."""
        return face2 in _ADJACENT[face1]

    def get_adjacent_faces(self, face: FaceName) -> tuple[FaceName, ...]:
        """Get all faces adjacent to the given face."""
        return _ADJACENT[face]

    def iterate_orthogonal_face_center_pieces(
            self,
            cube: "Cube",
            layer1_face: "Face",
            side_face: "Face",
            layer_slice_index: int,
    ) -> Iterator[tuple[int, int]]:
        return cube.geometric.iterate_orthogonal_face_center_pieces(
            layer1_face, side_face, layer_slice_index
        )

    def get_slices_between_faces(
            self,
            source_face: "Face",
            target_face: "Face",
    ) -> list[SliceName]:
        """
        Get the slice(s) that connect source_face to target_face.

        TODO: This is a patch implementation using translate_source_from_target.
              Consider deriving this directly from slice geometry.
        """
        from cube.domain.geometric.Face2FaceTranslator import Face2FaceTranslator

        # Use a dummy coordinate - we just need the slice info
        dummy_coord = (0, 0)
        result = Face2FaceTranslator.translate_source_from_target(
            target_face, source_face, dummy_coord
        )

        # Extract unique slice names from slice_algorithms
        slice_names: list[SliceName] = []
        for slice_alg_result in result.slice_algorithms:
            slice_name = slice_alg_result.whole_slice_alg.slice_name
            if slice_name is not None and slice_name not in slice_names:
                slice_names.append(slice_name)

        return slice_names

    def _is_face(self, color: Color) -> FaceName | None:
        """Find which face has the given color, or None if not found."""
        for f, c in self._faces.items():
            if c == color:
                return f
        return None

    def _find_face(self, color: Color) -> FaceName:
        """Find which face has the given color.

        Args:
            color: The color to find.

        Returns:
            The face with that color.

        Raises:
            InternalSWError: If color is not found.
        """
        fn = self._is_face(color)

        if fn:
            return fn

        raise InternalSWError(f"No such color {color} in {self}")

    def _bring_face_to_front(self, f: FaceName) -> None:
        """Rotate layout so the given face becomes Front.

        Used internally by same() for layout comparison.

        Args:
            f: The face to bring to front position.
        """
        assert not self._read_only

        if f != FaceName.F:

            match f:

                case FaceName.U:
                    self._rotate_x(-1)

                case FaceName.B:
                    self._rotate_x(-2)

                case FaceName.D:
                    self._rotate_x(1)

                case FaceName.L:
                    self._rotate_y(-1)

                case FaceName.R:
                    self._rotate_y(1)

                case _:
                    raise InternalSWError(f"Unknown face {f}")

    def _bring_face_up_preserve_front(self, face: FaceName) -> None:
        """Rotate layout so the given face becomes Up, keeping Front unchanged.

        Only works for faces adjacent to Front (not Back).

        Args:
            face: The face to bring to up position.

        Raises:
            InternalSWError: If face is Back (cannot preserve Front).
        """
        if face == FaceName.U:
            return

        if face == FaceName.B:
            raise InternalSWError(f"{face} is not supported")

        match face:

            case FaceName.L:
                self._rotate_z(1)

            case FaceName.D:
                self._rotate_z(2)

            case FaceName.R:
                self._rotate_z(-1)

            case _:
                raise InternalSWError(f" Unknown face {face.name}")

    def _rotate_x(self, n: int) -> None:
        """Rotate layout around R axis (like cube rotation x).

        Args:
            n: Number of 90° rotations (positive = U→F→D→B direction).
        """
        faces = self._faces

        for _ in range(n % 4):
            self._check()
            f = faces[FaceName.F]
            faces[FaceName.F] = faces[FaceName.D]
            faces[FaceName.D] = faces[FaceName.B]
            faces[FaceName.B] = faces[FaceName.U]
            faces[FaceName.U] = f
            self._check()

    def _rotate_y(self, n: int) -> None:
        """Rotate layout around U axis (like cube rotation y).

        Args:
            n: Number of 90° rotations (positive = F→L→B→R direction).
        """
        faces = self._faces

        for _ in range(n % 4):
            self._check()
            f = faces[FaceName.F]
            faces[FaceName.F] = faces[FaceName.R]
            faces[FaceName.R] = faces[FaceName.B]
            faces[FaceName.B] = faces[FaceName.L]
            faces[FaceName.L] = f
            self._check()

    def _rotate_z(self, n: int) -> None:
        """Rotate layout around F axis (like cube rotation z).

        Args:
            n: Number of 90° rotations (positive = U→L→D→R direction).
        """
        faces = self._faces

        for _ in range(n % 4):
            self._check()
            u = faces[FaceName.U]
            faces[FaceName.U] = faces[FaceName.L]
            faces[FaceName.L] = faces[FaceName.D]
            faces[FaceName.D] = faces[FaceName.R]
            faces[FaceName.R] = u
            self._check()

    def __str__(self) -> str:
        faces: dict[FaceName, Color] = self._faces

        s = ""

        s += "-" + str(faces[FaceName.B].value) + "-" + "\n"
        s += "-" + str(faces[FaceName.U].value) + "-" + "\n"
        s += str(faces[FaceName.L].value) + str(faces[FaceName.F].value) + str(faces[FaceName.R].value) + "\n"
        s += "-" + str(faces[FaceName.D].value) + "-" + "\n"

        return s

    def __repr__(self) -> str:
        return self.__str__()

    def _check(self) -> None:
        """Verify layout sanity (if config enables it)."""
        if not self.config.check_cube_sanity:
            return

        for c in Color:
            assert self._find_face(c)

    def translate_target_from_source(self,
                                     source_face: Face,
                                     target_face: Face,
                                     source_coord: tuple[int, int],
                                     slice_name: SliceName
                                     ) -> FUnitRotation:

        def compute_unit_rotation() -> FUnitRotation:
            return source_face.cube.geometric.translate_target_from_source(
                source_face, target_face, source_coord, slice_name
            )

        cache_key = (source_face.name, target_face.name, slice_name)
        cache = self.cache_manager.get("CubeLayout.translate_target_from_source",
                                       FUnitRotation)

        unit_rotation = cache.compute(cache_key, compute_unit_rotation)

        return unit_rotation

    def get_face_edge_rotation_cw(self, face: Face) -> list[Edge]:
        """
        Get the four edges of a face in clockwise rotation order.

        Returns edges in the order content moves during a clockwise face rotation:
        top → right → bottom → left → (back to top)

        In LTR Coordinate System (looking at face from outside cube):
        ============================================================

                        T (top direction)
                        ↑
                        │
                ┌───────┴───────┐
                │   edge_top    │
                │               │
          L ←───│edge    edge   │───→ R (right direction)
                │_left   _right │
                │               │
                │  edge_bottom  │
                └───────┬───────┘
                        │
                        ↓
                       -T

        Clockwise rotation order: [0]=top, [1]=right, [2]=bottom, [3]=left

        When face rotates CW, content flows: T → R → (-T) → (-R) → T
        - Content at top edge moves to right edge
        - Content at right edge moves to bottom edge
        - Content at bottom edge moves to left edge
        - Content at left edge moves to top edge

        Args:
            face: The face to get edges for.

        Returns:
            List of 4 edges in clockwise order: [top, right, bottom, left]
        """
        rotation_edges: list[Edge] = [face.edge_top, face.edge_right,
                                      face.edge_bottom, face.edge_left]

        return rotation_edges

    def does_slice_cut_rows_or_columns(self, slice_name: SliceName, face_name: FaceName) -> CLGColRow:
        """Determine if a slice cuts rows or columns on a given face.

        Delegates to the SliceLayout for this slice.
        """
        return self.get_slice(slice_name).does_slice_cut_rows_or_columns(face_name)

    def derive_transform_type(
        self,
        source: FaceName,
        target: FaceName,
    ) -> TransformType | None:
        """
        Derive the TransformType for coordinate mapping between two faces.

        This method computes how coordinates transform when content moves from
        source face to target face via a whole-cube rotation (X, Y, or Z).

        The result is purely geometric and does not depend on cube size - it's
        derived from slice traversal geometry using symbolic corner analysis.

        Args:
            source: The face where content originates (e.g., FaceName.F)
            target: The face where content arrives (e.g., FaceName.U)

        Returns:
            TransformType indicating how (row, col) coordinates change:
            - IDENTITY: (r, c) → (r, c) - no change
            - ROT_90_CW: (r, c) → (inv(c), r) - 90° clockwise
            - ROT_90_CCW: (r, c) → (c, inv(r)) - 90° counter-clockwise
            - ROT_180: (r, c) → (inv(r), inv(c)) - 180° rotation
            - None: if faces are same or opposite (no direct connection)

        Example:
            layout.derive_transform_type(FaceName.F, FaceName.U)
            → TransformType.IDENTITY (F→U via X keeps coordinates)

        GEOMETRIC ASSUMPTION: Opposite faces rotate in opposite directions.
        See Face2FaceTranslator.py comment block for details.
        """
        from cube.domain.geometric._CubeGeometric import (
            _SLICE_ROTATION_FACE,
            _AXIS_ROTATION_FACE,
            _OPPOSITE_FACES,
        )

        if source == target:
            return None

        # Check for opposite faces - need special handling (two 90° rotations)
        is_opposite = _ALL_OPPOSITE.get(source) == target

        # Find which slice connects them
        from cube.domain.geometric._CubeGeometric import _CubeGeometric
        slice_name = _CubeGeometric.get_slice_for_faces(source, target)
        if slice_name is None:
            return None  # Should not happen

        # Use internal 3x3 cube for face/edge objects only
        cube = self._cube

        if is_opposite:
            # For opposite faces, find an intermediate adjacent face and compose
            # the transforms: source → intermediate → target
            intermediate = self._get_adjacent_in_cycle(cube, slice_name, source)
            transform1 = self._derive_adjacent_transform(cube, slice_name, source, intermediate)
            transform2 = self._derive_adjacent_transform(cube, slice_name, intermediate, target)
            transform = self._compose_transforms(transform1, transform2)
        else:
            transform = self._derive_adjacent_transform(cube, slice_name, source, target)

        # Check if we need to invert due to opposite rotation faces
        slice_rot_face = _SLICE_ROTATION_FACE[slice_name]
        axis_rot_face = _AXIS_ROTATION_FACE[slice_name]

        if _OPPOSITE_FACES.get(slice_rot_face) == axis_rot_face:
            transform = self._invert_transform(transform)

        return transform

    def _get_adjacent_in_cycle(
        self,
        cube: "Cube",
        slice_name: SliceName,
        face_name: FaceName,
    ) -> FaceName:
        """Get an adjacent face in the slice cycle (next in CW order)."""
        from cube.domain.geometric.slice_layout import _SliceLayout

        slice_layout = _SliceLayout(slice_name)
        rotation_face = cube.face(slice_layout.get_face_name())
        rotation_edges = cube.layout.get_face_edge_rotation_cw(rotation_face)
        cycle_faces = [edge.get_other_face(rotation_face) for edge in rotation_edges]

        face_idx = next(i for i, f in enumerate(cycle_faces) if f.name == face_name)
        return cycle_faces[(face_idx + 1) % 4].name

    def _derive_adjacent_transform(
        self,
        cube: "Cube",
        slice_name: SliceName,
        source: FaceName,
        target: FaceName,
    ) -> TransformType:
        """Derive transform between two adjacent faces in the same slice cycle."""
        source_props = self._get_face_edge_properties(cube, slice_name, source)
        target_props = self._get_face_edge_properties(cube, slice_name, target)

        source_corner = self._props_to_corner(source_props)
        target_corner = self._props_to_corner(target_props)

        return self._corner_pair_to_transform(source_corner, target_corner)

    @staticmethod
    def _compose_transforms(t1: TransformType, t2: TransformType) -> TransformType:
        """Compose two transforms: apply t1 first, then t2."""
        # Map TransformType to rotation count (0-3)
        to_count = {
            TransformType.IDENTITY: 0,
            TransformType.ROT_90_CW: 1,
            TransformType.ROT_180: 2,
            TransformType.ROT_90_CCW: 3,
        }
        from_count = {
            0: TransformType.IDENTITY,
            1: TransformType.ROT_90_CW,
            2: TransformType.ROT_180,
            3: TransformType.ROT_90_CCW,
        }
        return from_count[(to_count[t1] + to_count[t2]) % 4]

    @staticmethod
    def _get_face_edge_properties(
        cube: "Cube",
        slice_name: SliceName,
        face_name: FaceName,
    ) -> tuple[bool, bool, bool]:
        """
        Get edge properties for a face in the slice traversal.

        Returns (is_horizontal, is_slot_inverted, is_index_inverted).
        These properties fully determine the reference corner without needing n_slices.
        """
        from cube.domain.geometric.slice_layout import _SliceLayout

        face = cube.face(face_name)
        slice_layout = _SliceLayout(slice_name)
        rotation_face = cube.face(slice_layout.get_face_name())

        # Find entry edge by traversing the cycle
        rotation_edges = cube.layout.get_face_edge_rotation_cw(rotation_face)
        cycle_faces = [edge.get_other_face(rotation_face) for edge in rotation_edges]

        # Find this face in the cycle
        face_idx = next(i for i, f in enumerate(cycle_faces) if f.name == face_name)

        # Entry edge is shared with previous face in cycle
        prev_face = cycle_faces[(face_idx - 1) % 4]
        entry_edge: Edge = face.get_shared_edge(prev_face)

        # Edge properties
        is_horizontal = face.is_bottom_or_top(entry_edge)
        is_slot_inverted = (
            face.is_top_edge(entry_edge) if is_horizontal
            else face.is_right_edge(entry_edge)
        )

        # Index inversion: check if slice starts from rotation face side
        shared_with_rotating = face.get_shared_edge(rotation_face)
        if is_horizontal:
            is_index_inverted = face.edge_left is not shared_with_rotating
        else:
            is_index_inverted = face.edge_bottom is not shared_with_rotating

        return (is_horizontal, is_slot_inverted, is_index_inverted)

    @staticmethod
    def _props_to_corner(props: tuple[bool, bool, bool]) -> int:
        """
        Map edge properties to symbolic corner (0-3).

        Corners are encoded as:
        - 0: (0, 0)     - origin
        - 1: (n-1, 0)   - bottom-left when inverted row
        - 2: (0, n-1)   - top-right when inverted col
        - 3: (n-1, n-1) - opposite corner

        The mapping depends on (is_horizontal, is_slot_inverted, is_index_inverted).
        """
        is_h, is_si, is_ii = props

        # Reference point formula at (slice_index=0, slot=0):
        # Horizontal: (inv(slot) if si else slot, idx if not ii else inv(idx))
        #           = (inv(0) if si else 0, 0 if not ii else inv(0))
        #           = (N if si else 0, 0 if not ii else N)  where N = n-1
        # Vertical:   (idx if not ii else inv(idx), inv(slot) if si else slot)
        #           = (0 if not ii else N, N if si else 0)

        if is_h:
            row_is_max = is_si  # inv(slot) at slot=0 gives n-1
            col_is_max = is_ii  # inv(idx) at idx=0 gives n-1
        else:
            row_is_max = is_ii  # inv(idx) at idx=0 gives n-1
            col_is_max = is_si  # inv(slot) at slot=0 gives n-1

        # Encode as corner ID
        return (1 if row_is_max else 0) + (2 if col_is_max else 0)

    @staticmethod
    def _corner_pair_to_transform(source_corner: int, target_corner: int) -> TransformType:
        """
        Derive TransformType from source→target corner mapping.

        For a rotation R, if R(corner_i) = corner_j, then:
        - IDENTITY: 0→0, 1→1, 2→2, 3→3
        - ROT_90_CW: 0→1, 1→3, 2→0, 3→2  (corners rotate CW)
        - ROT_180: 0→3, 1→2, 2→1, 3→0
        - ROT_90_CCW: 0→2, 1→0, 2→3, 3→1

        We have source_corner → target_corner, need to find which rotation does this.
        """
        # Build lookup: which rotation maps source to target?
        # For each rotation, compute where corner 0 goes
        rotation_table = {
            (0, 0): TransformType.IDENTITY,
            (0, 1): TransformType.ROT_90_CW,
            (0, 3): TransformType.ROT_180,
            (0, 2): TransformType.ROT_90_CCW,
            (1, 1): TransformType.IDENTITY,
            (1, 3): TransformType.ROT_90_CW,
            (1, 2): TransformType.ROT_180,
            (1, 0): TransformType.ROT_90_CCW,
            (2, 2): TransformType.IDENTITY,
            (2, 0): TransformType.ROT_90_CW,
            (2, 1): TransformType.ROT_180,
            (2, 3): TransformType.ROT_90_CCW,
            (3, 3): TransformType.IDENTITY,
            (3, 2): TransformType.ROT_90_CW,
            (3, 0): TransformType.ROT_180,
            (3, 1): TransformType.ROT_90_CCW,
        }
        return rotation_table[(source_corner, target_corner)]

    @staticmethod
    def _invert_transform(transform: TransformType) -> TransformType:
        """Invert a transform (for opposite rotation directions)."""
        inversion = {
            TransformType.IDENTITY: TransformType.IDENTITY,
            TransformType.ROT_90_CW: TransformType.ROT_90_CCW,
            TransformType.ROT_180: TransformType.ROT_180,
            TransformType.ROT_90_CCW: TransformType.ROT_90_CW,
        }
        return inversion[transform]
