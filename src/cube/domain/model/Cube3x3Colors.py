"""Cube3x3Colors - immutable snapshot of 3x3 cube state with face-based color mapping."""

from __future__ import annotations

from dataclasses import dataclass, replace

from cube.domain.model._part import CornerName, EdgeName
from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName


@dataclass(frozen=True)
class EdgeColors:
    """Colors of a single edge, keyed by face name.

    An edge belongs to two faces, so the dict has exactly 2 entries.
    For example, the FU edge has colors for faces F and U.
    """

    colors: dict[FaceName, Color]

    def __post_init__(self) -> None:
        if len(self.colors) != 2:
            raise ValueError(f"EdgeColors must have exactly 2 faces, got {len(self.colors)}")

    def with_color(self, face: FaceName, color: Color) -> "EdgeColors":
        """Return new EdgeColors with one face's color changed."""
        if face not in self.colors:
            raise ValueError(f"Face {face} not in this edge (has {list(self.colors.keys())})")
        new_colors = dict(self.colors)
        new_colors[face] = color
        return EdgeColors(new_colors)


@dataclass(frozen=True)
class CornerColors:
    """Colors of a single corner, keyed by face name.

    A corner belongs to three faces, so the dict has exactly 3 entries.
    For example, the FRU corner has colors for faces F, R, and U.
    """

    colors: dict[FaceName, Color]

    def __post_init__(self) -> None:
        if len(self.colors) != 3:
            raise ValueError(f"CornerColors must have exactly 3 faces, got {len(self.colors)}")

    def with_color(self, face: FaceName, color: Color) -> "CornerColors":
        """Return new CornerColors with one face's color changed."""
        if face not in self.colors:
            raise ValueError(f"Face {face} not in this corner (has {list(self.colors.keys())})")
        new_colors = dict(self.colors)
        new_colors[face] = color
        return CornerColors(new_colors)


@dataclass(frozen=True)
class Cube3x3Colors:
    """Immutable snapshot of a 3x3 cube's edge, corner, and center colors.

    This class captures the essential color state of a 3x3 cube (or an NxN
    cube reduced to 3x3 representation) in a type-safe, immutable structure.

    Each edge and corner stores its colors keyed by the face they belong to,
    making the semantics clear (e.g., EdgeColors for FU edge has colors for
    faces F and U).

    Attributes:
        edges: Mapping from EdgeName to colors on that edge (keyed by face)
        corners: Mapping from CornerName to colors on that corner (keyed by face)
        centers: Mapping from FaceName to the center color of that face
    """

    edges: dict[EdgeName, EdgeColors]
    corners: dict[CornerName, CornerColors]
    centers: dict[FaceName, Color]

    def with_center(self, face: FaceName, color: Color) -> "Cube3x3Colors":
        """Return new Cube3x3Colors with one center color changed."""
        new_centers = dict(self.centers)
        new_centers[face] = color
        return replace(self, centers=new_centers)

    def with_centers(self, centers: dict[FaceName, Color]) -> "Cube3x3Colors":
        """Return new Cube3x3Colors with centers replaced."""
        return replace(self, centers=dict(centers))

    def with_edge_color(
        self, edge: EdgeName, face: FaceName, color: Color
    ) -> "Cube3x3Colors":
        """Return new Cube3x3Colors with one edge sticker color changed."""
        if edge not in self.edges:
            raise ValueError(f"Edge {edge} not in this cube")
        new_edges = dict(self.edges)
        new_edges[edge] = self.edges[edge].with_color(face, color)
        return replace(self, edges=new_edges)

    def with_corner_color(
        self, corner: CornerName, face: FaceName, color: Color
    ) -> "Cube3x3Colors":
        """Return new Cube3x3Colors with one corner sticker color changed."""
        if corner not in self.corners:
            raise ValueError(f"Corner {corner} not in this cube")
        new_corners = dict(self.corners)
        new_corners[corner] = self.corners[corner].with_color(face, color)
        return replace(self, corners=new_corners)

    def is_boy(self, original_layout: dict[FaceName, Color]) -> bool:
        """Check if centers match the original cube layout.

        The "BOY" check compares current center colors against the cube's
        original layout. A cube is "in BOY state" when its centers haven't
        been permuted from the original configuration.

        Args:
            original_layout: The original face-to-color mapping from the cube.
                             Get this from cube.original_layout or similar.

        Returns:
            True if centers match the original layout.
        """
        return self.centers == original_layout

    def is_complete(self) -> bool:
        """Check if this has all required entries.

        Verifies structural completeness:
        - Has exactly 12 edges
        - Has exactly 8 corners
        - Has exactly 6 centers

        Returns:
            True if structurally complete.
        """
        return len(self.edges) == 12 and len(self.corners) == 8 and len(self.centers) == 6

    def get_color_counts(self) -> dict[Color, int]:
        """Count how many times each color appears in total.

        Counts all stickers: 6 centers + 24 edge stickers + 24 corner stickers = 54.

        Returns:
            Mapping of color to occurrence count.
        """
        color_count: dict[Color, int] = {c: 0 for c in Color}

        # Count centers
        for color in self.centers.values():
            color_count[color] += 1

        # Count edge stickers
        for edge_colors in self.edges.values():
            for color in edge_colors.colors.values():
                color_count[color] += 1

        # Count corner stickers
        for corner_colors in self.corners.values():
            for color in corner_colors.colors.values():
                color_count[color] += 1

        return color_count

    @staticmethod
    def create_empty() -> "Cube3x3Colors":
        """Create a Cube3x3Colors with all None placeholders.

        Useful as a starting point when building from face tracker input.
        Note: The resulting structure won't be valid until all colors are set.
        """
        from cube.domain.model._part import EdgeName, CornerName

        # Create empty edge colors for all 12 edges
        # Edge names: FL, FU, FR, FD, BL, BU, BR, BD, UR, RD, DL, LU
        edges: dict[EdgeName, EdgeColors] = {}
        edge_faces = {
            EdgeName.FU: (FaceName.F, FaceName.U),
            EdgeName.FR: (FaceName.F, FaceName.R),
            EdgeName.FD: (FaceName.F, FaceName.D),
            EdgeName.FL: (FaceName.F, FaceName.L),
            EdgeName.BU: (FaceName.B, FaceName.U),
            EdgeName.BR: (FaceName.B, FaceName.R),
            EdgeName.BD: (FaceName.B, FaceName.D),
            EdgeName.BL: (FaceName.B, FaceName.L),
            EdgeName.LU: (FaceName.L, FaceName.U),
            EdgeName.UR: (FaceName.U, FaceName.R),
            EdgeName.DL: (FaceName.D, FaceName.L),
            EdgeName.RD: (FaceName.R, FaceName.D),
        }
        # Use WHITE as placeholder (will be overwritten)
        for edge_name, (f1, f2) in edge_faces.items():
            edges[edge_name] = EdgeColors({f1: Color.WHITE, f2: Color.WHITE})

        # Create empty corner colors for all 8 corners
        corners: dict[CornerName, CornerColors] = {}
        corner_faces = {
            CornerName.FLU: (FaceName.F, FaceName.L, FaceName.U),
            CornerName.FRU: (FaceName.F, FaceName.R, FaceName.U),
            CornerName.FRD: (FaceName.F, FaceName.R, FaceName.D),
            CornerName.FLD: (FaceName.F, FaceName.L, FaceName.D),
            CornerName.BLU: (FaceName.B, FaceName.L, FaceName.U),
            CornerName.BRU: (FaceName.B, FaceName.R, FaceName.U),
            CornerName.BRD: (FaceName.B, FaceName.R, FaceName.D),
            CornerName.BLD: (FaceName.B, FaceName.L, FaceName.D),
        }
        for corner_name, (f1, f2, f3) in corner_faces.items():
            corners[corner_name] = CornerColors({f1: Color.WHITE, f2: Color.WHITE, f3: Color.WHITE})

        # Create empty centers (WHITE placeholder)
        centers: dict[FaceName, Color] = {fn: Color.WHITE for fn in FaceName}

        return Cube3x3Colors(edges=edges, corners=corners, centers=centers)
