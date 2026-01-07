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
from cube.domain.geometric.slice_layout import SliceLayout, _SliceLayout
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
            SliceName.S: _SliceLayout(SliceName.S),
            SliceName.E: _SliceLayout(SliceName.E),
            SliceName.M: _SliceLayout(SliceName.M),

        }

    @property
    def config(self) -> ConfigProtocol:
        """Get configuration via service provider."""
        return self._sp.config

    @property
    def cache_manager(self) -> CacheManager:
        """Get the cache manager for this layout."""
        return self._cache_manager

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
        from cube.domain.geometric._CubeLayoutGeometry import _CubeLayoutGeometry
        return _CubeLayoutGeometry.iterate_orthogonal_face_center_pieces(
            cube, layer1_face, side_face, layer_slice_index
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

        from cube.domain.geometric._CubeLayoutGeometry import _CubeLayoutGeometry

        def compute_unit_rotation() -> FUnitRotation:
            return _CubeLayoutGeometry.translate_target_from_source(
                source_face,
                target_face, source_coord, slice_name
            )

        cache_key = (source_face.name, target_face.name, slice_name)
        cache = self.cache_manager.get("CubeLayout.translate_target_from_source",
                                       FUnitRotation)

        unit_rotation = cache.compute(cache_key, compute_unit_rotation)

        return unit_rotation

    def get_face_edge_rotation_cw(self, face: Face) -> list[Edge]:
        """
        claude: describe this method with diagrams, ltr system bottom top left right
        :return:
        """

        rotation_edges: list[Edge] = [face.edge_top, face.edge_right,
                                      face.edge_bottom, face.edge_left]

        return rotation_edges
