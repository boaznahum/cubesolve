"""Cube3x3Colors - immutable snapshot of 3x3 cube state with face-based color mapping."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from cube.domain.model._part import CornerName, EdgeName
from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName
from cube.utils.service_provider import IServiceProvider

if TYPE_CHECKING:
    from cube.domain.geometric.cube_color_scheme import CubeColorScheme
    from cube.domain.model.Cube import Cube


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

    def with_fixed_non_3x3_edges(
        self,
        cube: "Cube",
        reference_scheme: "CubeColorScheme"
    ) -> "Cube3x3Colors":
        """Build valid 3x3 edge colors by matching big cube edges to template edges.

        Used when creating shadow cubes from even cubes during L1 solving.
        Matches 3x3-valid edges from big cube to template edges by color-pair,
        ignoring position and orientation.

        Args:
            cube: The source cube to get 3x3-valid edges from (via edge.is3x3)
            reference_scheme: Color scheme providing edge color-pairs

        Returns:
            New Cube3x3Colors with all 12 edges having valid template color-pairs.

        Algorithm:
            1. Get template: 12 edge names → color-pairs (frozenset) from scheme
            2. Get big cube: 3x3-valid edges → color-pairs (frozenset)
            3. Match by color-pair: template edge with {WHITE,RED} ← big cube edge with {WHITE,RED}
            4. For unmatched template edges: use template colors

        Position and orientation don't matter - 3x3 solver will fix positions!

        Example - 4x4 cube during L1:
            - Big cube edge at FL: frozenset({WHITE, RED}), is3x3=True
            - Template edge DR: frozenset({WHITE, RED})
            - Match: DR ← {WHITE, RED} from big cube edge at FL
            - Shadow cube edge DR will have WHITE and RED (order doesn't matter)
        """
        from cube.domain.exceptions import InternalSWError

        # Get all template color-pairs from BOY layout
        available_pairs: set[frozenset[Color]] = set(reference_scheme.edge_colors())

        # TWO-PASS algorithm to prioritize 3x3-valid edges:
        # Pass 1: Keep all 3x3-valid edges with valid color-pairs
        # Pass 2: Fill in non-3x3 edges with unused template pairs

        new_edges: dict[EdgeName, EdgeColors] = {}

        # PASS 1: Process 3x3-valid edges first
        for edge_name, edge_colors in self.edges.items():
            edge = cube.edge(edge_name)
            current_pair = frozenset(edge_colors.colors.values())

            # If edge is 3x3-valid AND its color-pair is in template AND not yet used:
            if edge.is3x3 and current_pair in available_pairs:
                # Keep the extracted colors
                available_pairs.remove(current_pair)
                new_edges[edge_name] = edge_colors

        # PASS 2: Fill in remaining edges (non-3x3) with unused template pairs
        for edge_name, edge_colors in self.edges.items():
            if edge_name in new_edges:
                continue  # Already processed in pass 1

            # Edge is non-3x3 or has invalid/duplicate color-pair
            # Pick unused template color-pair
            if not available_pairs:
                raise InternalSWError(
                    f"No available template color-pairs. "
                    f"Edge {edge_name}: is3x3={cube.edge(edge_name).is3x3}"
                )

            # Pick any unused pair
            color_pair = available_pairs.pop()

            # Assign colors to faces (order doesn't matter for 3x3 solver)
            colors_list = sorted(list(color_pair), key=lambda c: c.value)
            face_list = sorted(list(edge_colors.colors.keys()), key=lambda f: f.value)

            new_edges[edge_name] = EdgeColors({
                face_list[0]: colors_list[0],
                face_list[1]: colors_list[1]
            })

        return replace(self, edges=new_edges)

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

    def matches_scheme(self, scheme: "CubeColorScheme") -> bool:
        """Check if centers match the given color scheme.

        Creates a CubeColorScheme from center colors and uses
        rotation-aware comparison.

        Args:
            scheme: The color scheme to compare against.

        Returns:
            True if centers match *scheme* up to whole-cube rotation.
        """
        from cube.domain.geometric.cube_color_scheme import CubeColorScheme as CCS
        candidate = CCS(self.centers)
        return scheme.same(candidate)

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
    def create_empty(sp: IServiceProvider) -> "Cube3x3Colors":
        """Create a Cube3x3Colors with all WHITE placeholders.

        All colors are initialized to WHITE and should be overwritten with actual colors.
        The structure (which edges connect which faces) comes from SchematicCube geometry.

        Args:
            sp: Service provider (unused, kept for API compatibility).

        Returns:
            Cube3x3Colors with all edges/corners/centers initialized to WHITE.

        Note: The resulting structure won't be valid until all colors are set to actual values.
        """
        from cube.domain.geometric.schematic_cube import SchematicCube

        scheme = SchematicCube.inst()

        # Get edge-to-faces mapping from geometry (the authoritative source)
        edge_faces_map = scheme.edge_faces()

        # Create empty edge colors for all 12 edges
        edges: dict[EdgeName, EdgeColors] = {}
        for edge_name, (f1, f2) in edge_faces_map.items():
            edges[edge_name] = EdgeColors({f1: Color.WHITE, f2: Color.WHITE})

        # Get corner-to-faces mapping from geometry (the authoritative source)
        corner_faces_map = scheme.corner_faces()

        # Create empty corner colors for all 8 corners
        corners: dict[CornerName, CornerColors] = {}
        for corner_name, (f1, f2, f3) in corner_faces_map.items():
            corners[corner_name] = CornerColors({f1: Color.WHITE, f2: Color.WHITE, f3: Color.WHITE})

        # Create empty centers (WHITE placeholder)
        centers: dict[FaceName, Color] = {fn: Color.WHITE for fn in FaceName}

        return Cube3x3Colors(edges=edges, corners=corners, centers=centers)
