"""
Modern GL Board - Manages all 6 cube faces for rendering.

This module is the top-level geometry manager. It creates and coordinates
all 6 faces of the cube, handles shadow faces, and generates vertex data.

Face Layout (cube net):
    Looking at the cube from default isometric view:

           +-------+
           |   U   |
           |  +Y   |
       +---+---+---+---+
       | L | F | R | B |
       |-X |+Z |+X |-Z |
       +---+---+---+---+
           |   D   |
           |  -Y   |
           +-------+

    Face coordinates (matching legacy _board.py):
           0  1  2
       0:     U
       1:  L  F  R
       2:     D
       3:     B

Shadow Faces:
    When shadow mode is enabled (F10/F11/F12), duplicate faces are
    rendered at offset positions for visibility in isometric view:
    - L (Left): offset -75 units in X
    - D (Down): offset -50 units in Y
    - B (Back): offset -200 units in Z
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy import ndarray

from cube.domain.geometric.cube_boy import Color, FaceName

from ._modern_gl_arrow import Arrow3D, create_arrows_from_markers
from ._modern_gl_constants import (
    FACE_TRANSFORMS,
    SHADOW_OFFSETS,
)
from ._modern_gl_face import ModernGLFace

if TYPE_CHECKING:
    from cube.application.state import ApplicationAndViewState
    from cube.domain.model.PartSlice import PartSlice
    from cube.domain.model.Cube import Cube
    from cube.domain.model.PartEdge import PartEdge

    from ._modern_gl_cell import ModernGLCell


class ModernGLBoard:
    """Manages all 6 cube faces for ModernGL rendering.

    Face Coordinates:
           0  1  2
       0:     U
       1:  L  F  R
       2:     D
       3:     B

    This class:
    - Creates the 6 main faces at startup
    - Creates shadow faces when shadow mode is enabled
    - Updates all faces when cube state changes
    - Generates vertex data for rendering
    """

    __slots__ = [
        '_cube', '_vs', '_size',
        '_faces',         # Main 6 faces
        '_shadow_faces',  # Shadow faces (when enabled)
    ]

    def __init__(self, cube: "Cube", vs: "ApplicationAndViewState | None") -> None:
        """Initialize the board.

        Args:
            cube: The cube model
            vs: Application view state (for shadow mode settings)
        """
        self._cube = cube
        self._vs = vs
        self._size = cube.size

        self._faces: dict[FaceName, ModernGLFace] = {}
        self._shadow_faces: dict[FaceName, ModernGLFace] = {}

        self._create_faces()

    def _create_faces(self) -> None:
        """Create all 6 main faces.

        Face creation order and positions:
            U (Up):    center at (0, +50, 0)
            D (Down):  center at (0, -50, 0)
            F (Front): center at (0, 0, +50)
            B (Back):  center at (0, 0, -50)
            R (Right): center at (+50, 0, 0)
            L (Left):  center at (-50, 0, 0)
        """
        for face_name in FaceName:
            center, right, up = FACE_TRANSFORMS[face_name]
            face = ModernGLFace(
                face_name=face_name,
                center=np.array(center, dtype=np.float32),
                right=np.array(right, dtype=np.float32),
                up=np.array(up, dtype=np.float32),
                size=self._size,
            )
            self._faces[face_name] = face

    def _create_shadow_faces(self) -> None:
        """Create shadow faces for L, D, B when shadow mode is enabled.

        Shadow faces are duplicate faces rendered at offset positions
        so they're visible in the default isometric view.
        """
        self._shadow_faces.clear()

        if self._vs is None:
            return

        for face_name, offset in SHADOW_OFFSETS.items():
            if self._vs.get_draw_shadows_mode(face_name):
                # Get base transform and apply offset
                center, right, up = FACE_TRANSFORMS[face_name]
                shadow_center = np.array(center, dtype=np.float32) + np.array(offset, dtype=np.float32)

                face = ModernGLFace(
                    face_name=face_name,
                    center=shadow_center,
                    right=np.array(right, dtype=np.float32),
                    up=np.array(up, dtype=np.float32),
                    size=self._size,
                )
                self._shadow_faces[face_name] = face

    def update(self) -> None:
        """Update all faces from current cube state.

        Called when cube state changes (rotations, scramble, reset).
        """
        cube = self._cube

        # Check if cube size changed (reset)
        if cube.size != self._size:
            self._size = cube.size
            self._create_faces()
            self._create_shadow_faces()

        # Update main faces
        for face_name, gl_face in self._faces.items():
            cube_face = cube.face(face_name)
            gl_face.update(cube_face)

        # Recreate and update shadow faces (in case shadow mode changed)
        self._create_shadow_faces()
        for face_name, gl_face in self._shadow_faces.items():
            cube_face = cube.face(face_name)
            gl_face.update(cube_face)

    def generate_geometry(
        self,
        animated_parts: "set[PartSlice] | None" = None,
    ) -> tuple[
        np.ndarray,  # static face triangles
        np.ndarray,  # static line data
        np.ndarray | None,  # animated face triangles
        np.ndarray | None,  # animated line data
        np.ndarray | None,  # static marker triangles
        np.ndarray | None,  # animated marker triangles
    ]:
        """Generate all vertex data for rendering.

        Separates geometry into static and animated parts.

        Args:
            animated_parts: Set of PartSlices being animated, or None

        Returns:
            Tuple of (face_triangles, line_data, animated_faces, animated_lines,
                      marker_triangles, animated_marker_triangles)
        """
        face_verts: list[float] = []
        line_verts: list[float] = []
        animated_face_verts: list[float] = []
        animated_line_verts: list[float] = []
        marker_verts: list[float] = []
        animated_marker_verts: list[float] = []

        # Main faces
        for gl_face in self._faces.values():
            self._generate_face_verts(
                gl_face, animated_parts,
                face_verts, line_verts,
                animated_face_verts, animated_line_verts,
                marker_verts, animated_marker_verts,
            )

        # Shadow faces (never animated - they're static copies)
        for gl_face in self._shadow_faces.values():
            self._generate_face_verts(
                gl_face, None,  # No animation for shadows
                face_verts, line_verts,
                [], [],  # Don't collect animated verts
                marker_verts, [],  # Markers only on static for shadow
            )

        return (
            np.array(face_verts, dtype=np.float32),
            np.array(line_verts, dtype=np.float32),
            np.array(animated_face_verts, dtype=np.float32) if animated_face_verts else None,
            np.array(animated_line_verts, dtype=np.float32) if animated_line_verts else None,
            np.array(marker_verts, dtype=np.float32) if marker_verts else None,
            np.array(animated_marker_verts, dtype=np.float32) if animated_marker_verts else None,
        )

    def generate_textured_geometry(
        self,
        animated_parts: "set[PartSlice] | None" = None,
    ) -> tuple[
        dict[Color, np.ndarray],  # static triangles per color
        np.ndarray,  # static line data
        dict[Color, np.ndarray],  # animated triangles per color
        np.ndarray | None,  # animated line data
    ]:
        """Generate vertex data grouped by color for textured rendering.

        Groups cells by their COLOR (not face) so textures "stick" to
        pieces as they move around the cube.

        Args:
            animated_parts: Set of PartSlices being animated, or None

        Returns:
            Tuple of (color_triangles, lines, animated_color_triangles, animated_lines)
        """
        verts_per_color: dict[Color, list[float]] = {c: [] for c in Color}
        animated_verts_per_color: dict[Color, list[float]] = {c: [] for c in Color}
        line_verts: list[float] = []
        animated_line_verts: list[float] = []

        # Main faces
        for gl_face in self._faces.values():
            self._generate_textured_face_verts(
                gl_face, animated_parts,
                verts_per_color, line_verts,
                animated_verts_per_color, animated_line_verts,
            )

        # Shadow faces
        for gl_face in self._shadow_faces.values():
            self._generate_textured_face_verts(
                gl_face, None,
                verts_per_color, line_verts,
                {}, [],
            )

        return (
            {c: np.array(v, dtype=np.float32) for c, v in verts_per_color.items() if v},
            np.array(line_verts, dtype=np.float32),
            {c: np.array(v, dtype=np.float32) for c, v in animated_verts_per_color.items() if v},
            np.array(animated_line_verts, dtype=np.float32) if animated_line_verts else None,
        )

    def _generate_face_verts(
        self,
        gl_face: ModernGLFace,
        animated_parts: "set[PartSlice] | None",
        face_verts: list[float],
        line_verts: list[float],
        animated_face_verts: list[float],
        animated_line_verts: list[float],
        marker_verts: list[float] | None = None,
        animated_marker_verts: list[float] | None = None,
    ) -> None:
        """Generate vertices for one face."""
        for cell in gl_face.cells:
            # Check if this cell is animated
            is_animated = (
                animated_parts is not None
                and cell.part_slice is not None
                and cell.part_slice in animated_parts
            )

            if is_animated:
                cell.generate_face_vertices(animated_face_verts)
                cell.generate_line_vertices(animated_line_verts)
                cell.generate_cross_line_vertices(animated_line_verts)
                # Collect animated marker geometry
                if animated_marker_verts is not None:
                    cell.generate_marker_vertices(animated_marker_verts)
                    cell.generate_tracker_indicator_vertices(animated_marker_verts)
            else:
                cell.generate_face_vertices(face_verts)
                cell.generate_line_vertices(line_verts)
                cell.generate_cross_line_vertices(line_verts)
                # Collect static marker geometry
                if marker_verts is not None:
                    cell.generate_marker_vertices(marker_verts)
                    cell.generate_tracker_indicator_vertices(marker_verts)

    def _generate_textured_face_verts(
        self,
        gl_face: ModernGLFace,
        animated_parts: "set[PartSlice] | None",
        verts_per_color: dict[Color, list[float]],
        line_verts: list[float],
        animated_verts_per_color: dict[Color, list[float]],
        animated_line_verts: list[float],
    ) -> None:
        """Generate textured vertices for one face, grouped by color."""
        size = self._size

        for cell in gl_face.cells:
            color = cell.color_enum

            # Check if this cell is animated
            is_animated = (
                animated_parts is not None
                and cell.part_slice is not None
                and cell.part_slice in animated_parts
            )

            if is_animated:
                if color in animated_verts_per_color:
                    cell.generate_textured_vertices(animated_verts_per_color[color], size)
                cell.generate_line_vertices(animated_line_verts)
                cell.generate_cross_line_vertices(animated_line_verts)
            else:
                if color in verts_per_color:
                    cell.generate_textured_vertices(verts_per_color[color], size)
                cell.generate_line_vertices(line_verts)
                cell.generate_cross_line_vertices(line_verts)

    def generate_per_cell_textured_geometry(
        self,
        animated_parts: "set[PartSlice] | None" = None,
    ) -> tuple[
        dict[int | None, np.ndarray],  # static triangles per texture handle
        np.ndarray,  # static line data
        dict[int | None, np.ndarray],  # animated triangles per texture handle
        np.ndarray | None,  # animated line data
    ]:
        """Generate vertex data grouped by cell texture handle.

        Used for per-cell textures stored in PartEdge.c_attributes.
        Each cell's texture handle is looked up from c_attributes and
        cells with the same texture are batched together.

        Cells without texture (None) are grouped together for fallback rendering.

        Args:
            animated_parts: Set of PartSlices being animated, or None

        Returns:
            Tuple of (texture_triangles, lines, animated_texture_triangles, animated_lines)
        """
        verts_per_texture: dict[int | None, list[float]] = {}
        animated_verts_per_texture: dict[int | None, list[float]] = {}
        line_verts: list[float] = []
        animated_line_verts: list[float] = []

        # Main faces
        for gl_face in self._faces.values():
            self._generate_per_cell_textured_face_verts(
                gl_face, animated_parts,
                verts_per_texture, line_verts,
                animated_verts_per_texture, animated_line_verts,
            )

        # Shadow faces
        for gl_face in self._shadow_faces.values():
            self._generate_per_cell_textured_face_verts(
                gl_face, None,
                verts_per_texture, line_verts,
                {}, [],
            )

        return (
            {t: np.array(v, dtype=np.float32) for t, v in verts_per_texture.items() if v},
            np.array(line_verts, dtype=np.float32),
            {t: np.array(v, dtype=np.float32) for t, v in animated_verts_per_texture.items() if v},
            np.array(animated_line_verts, dtype=np.float32) if animated_line_verts else None,
        )

    def _generate_per_cell_textured_face_verts(
        self,
        gl_face: ModernGLFace,
        animated_parts: "set[PartSlice] | None",
        verts_per_texture: dict[int | None, list[float]],
        line_verts: list[float],
        animated_verts_per_texture: dict[int | None, list[float]],
        animated_line_verts: list[float],
    ) -> None:
        """Generate vertices for one face, grouped by cell texture handle.

        Uses full UV (0,0 to 1,1) since each cell has its own texture.
        """
        for cell in gl_face.cells:
            texture_handle = cell.cell_texture  # From c_attributes

            # Check if this cell is animated
            is_animated = (
                animated_parts is not None
                and cell.part_slice is not None
                and cell.part_slice in animated_parts
            )

            if is_animated:
                verts_per_texture.setdefault(texture_handle, [])
                animated_verts_per_texture.setdefault(texture_handle, [])
                cell.generate_full_uv_vertices(animated_verts_per_texture[texture_handle])
                cell.generate_line_vertices(animated_line_verts)
                cell.generate_cross_line_vertices(animated_line_verts)
            else:
                verts_per_texture.setdefault(texture_handle, [])
                cell.generate_full_uv_vertices(verts_per_texture[texture_handle])
                cell.generate_line_vertices(line_verts)
                cell.generate_cross_line_vertices(line_verts)

    def get_face_center(self, face_name: FaceName) -> ndarray:
        """Get the center point of a face."""
        return self._faces[face_name].get_center_point()

    def get_part_edge_at_cell(self, face_name: FaceName, row: int, col: int) -> "PartEdge | None":
        """Get the PartEdge at a cell position on a face.

        Args:
            face_name: Which face
            row: Row index (0 = bottom)
            col: Column index (0 = left)

        Returns:
            PartEdge at this cell, or None
        """
        cube_face = self._cube.face(face_name)
        return self._faces[face_name].get_part_edge_at_cell(cube_face, row, col)

    @property
    def faces(self) -> dict[FaceName, ModernGLFace]:
        """Get all main faces."""
        return self._faces

    def collect_arrow_endpoints(self) -> tuple[list["ModernGLCell"], list["ModernGLCell"]]:
        """Collect cells with source and destination markers.

        Source cells have c_attributes markers (moving pieces).
        Destination cells have f_attributes markers (fixed positions).

        Returns:
            Tuple of (source_cells, destination_cells)
        """
        source_cells: list["ModernGLCell"] = []
        dest_cells: list["ModernGLCell"] = []

        for gl_face in self._faces.values():
            for cell in gl_face.cells:
                if cell.part_edge is None:
                    continue

                # Check c_attributes for source markers (moving pieces)
                c_markers = cell.part_edge.c_attributes.get("markers")
                if c_markers:
                    source_cells.append(cell)

                # Check f_attributes for destination markers (fixed positions)
                f_markers = cell.part_edge.f_attributes.get("markers")
                if f_markers:
                    dest_cells.append(cell)

        return source_cells, dest_cells

    def create_arrows(
        self,
        animated_parts: "set[PartSlice] | None" = None,
        arrow_color: tuple[float, float, float] | None = None,
    ) -> list[Arrow3D]:
        """Create Arrow3D objects from current marker annotations.

        Args:
            animated_parts: Set of PartSlices currently being animated
            arrow_color: Optional arrow color from config

        Returns:
            List of arrows connecting source to destination markers.
        """
        source_cells, dest_cells = self.collect_arrow_endpoints()
        return create_arrows_from_markers(source_cells, dest_cells, animated_parts, arrow_color)

    def generate_arrow_geometry(
        self,
        arrows: list[Arrow3D],
        source_transform: "ndarray | None" = None,
    ) -> np.ndarray | None:
        """Generate vertex data for all arrows.

        Args:
            arrows: List of Arrow3D objects with current animation progress
            source_transform: Optional 4x4 transform matrix for animated source positions

        Returns:
            NumPy array of vertex data, or None if no arrows
        """
        if not arrows:
            return None

        verts: list[float] = []
        for arrow in arrows:
            arrow.generate_vertices(verts, source_transform)

        if not verts:
            return None

        return np.array(verts, dtype=np.float32)
