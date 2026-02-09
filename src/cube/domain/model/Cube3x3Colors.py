"""Cube3x3Colors - immutable snapshot of 3x3 cube state with face-based color mapping."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from cube.domain.model._part import CornerName, EdgeName
from cube.domain.model.Color import Color
from cube.domain.geometric.cube_layout import CubeLayout
from cube.domain.model.FaceName import FaceName
from cube.utils.service_provider import IServiceProvider

if TYPE_CHECKING:
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
        reference_layout: "CubeLayout"
    ) -> "Cube3x3Colors":
        """Replace non-3x3 edge colors with valid reference colors.

        Used when creating shadow cubes from even cubes during L1 solving, where
        some edges are 3x3-valid but others are still scrambled.

        Args:
            cube: The source cube to check edge validity (via edge.is3x3)
            reference_layout: Layout providing valid edge color-pairs (via edge_colors())

        Returns:
            New Cube3x3Colors with non-3x3 edges replaced by unused valid color-pairs.

        Algorithm:
            1. Build set of available edge color-pairs from reference_layout.edge_colors()
            2. For each edge in self.edges:
                a. Look up Edge object in cube by EdgeName
                b. Get the two faces from edge.e1.face.name and edge.e2.face.name
                c. If edge.is3x3: keep current colors, remove from available set
                d. If not edge.is3x3: pop unused color-pair, create new EdgeColors
            3. Return new Cube3x3Colors with updated edges dict

        Example - 4x4 cube during L1:
            - Edge FU: is3x3=True (both slices RED-GREEN) → keep RED-GREEN
            - Edge FR: is3x3=False (slices RED-BLUE, ORANGE-WHITE) → replace with unused pair like BLUE-ORANGE
            - Edge FL: is3x3=True (both slices RED-ORANGE) → keep RED-ORANGE
            - Edge FD: is3x3=False → replace with another unused pair
            Result: All 12 edges have valid, unique color-pairs, passes sanity check
        """
        from cube.domain.exceptions import InternalSWError

        # Get edge-to-faces mapping from the layout (the authoritative source)
        edge_faces_map: dict[EdgeName, tuple[FaceName, FaceName]] = reference_layout.edge_faces()

        # Build set of available color-pairs from BOY layout
        # Each frozenset contains exactly 2 colors (one edge color-pair)
        available_pairs: set[frozenset[Color]] = set(reference_layout.edge_colors())

        # Track which color-pairs have been used to detect duplicates
        used_pairs: set[frozenset[Color]] = set()

        # Build new edges dict, preserving valid 3x3-edges and replacing invalid/non-3x3 edges
        new_edges: dict[EdgeName, EdgeColors] = {}

        for edge_name, edge_colors in self.edges.items():
            # Look up Edge object in cube to check is3x3 property
            edge = cube.edge(edge_name)

            # Get the two faces for this edge from the layout
            f1, f2 = edge_faces_map[edge_name]

            # Get the current color-pair for this edge
            current_pair = frozenset([
                edge_colors.colors[f1],
                edge_colors.colors[f2]
            ])

            # Keep the edge only if:
            # 1. It's 3x3-valid (all slices have same colors)
            # 2. Its color-pair hasn't been used yet (no duplicates)
            # 3. Its color-pair is valid (exists in BOY layout)
            if edge.is3x3 and current_pair not in used_pairs and current_pair in available_pairs:
                # Keep existing colors
                available_pairs.remove(current_pair)
                used_pairs.add(current_pair)
                new_edges[edge_name] = edge_colors
            else:
                # Replace with unused color-pair
                # This handles: non-3x3 edges, duplicate color-pairs, invalid color-pairs
                if not available_pairs:
                    raise InternalSWError(
                        f"No available edge color-pairs for replacement. "
                        f"Already processed {len(new_edges)} edges, "
                        f"{len(self.edges) - len(new_edges)} remaining. "
                        f"Edge {edge_name}: is3x3={edge.is3x3}, current_pair={current_pair}, "
                        f"used_pairs={used_pairs}"
                    )

                # Pop any unused pair
                color_pair = available_pairs.pop()
                used_pairs.add(color_pair)

                # Assign colors to faces based on reference layout orientation
                # The reference layout knows which color belongs on which face
                ref_color_f1 = reference_layout[f1]
                ref_color_f2 = reference_layout[f2]

                # Check which orientation matches the reference layout
                if {ref_color_f1, ref_color_f2} == color_pair:
                    # This pair belongs to this edge in the reference layout - use correct orientation
                    new_edge_colors = EdgeColors({
                        f1: ref_color_f1,
                        f2: ref_color_f2
                    })
                else:
                    # This pair is for a different edge - assign arbitrarily but consistently
                    # Convert frozenset to sorted list for deterministic assignment
                    colors_list = sorted(list(color_pair), key=lambda c: c.value)
                    new_edge_colors = EdgeColors({
                        f1: colors_list[0],
                        f2: colors_list[1]
                    })
                new_edges[edge_name] = new_edge_colors

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

    def get_layout(self, sp: IServiceProvider) -> CubeLayout:
        """Create a CubeLayout from these center colors.

        Args:
            sp: Service provider for configuration.

        Returns:
            CubeLayout representing the current center configuration.
        """
        return CubeLayout.create_layout(False, self.centers, sp)

    def is_boy(self, sp: IServiceProvider) -> bool:
        """Check if centers match the standard BOY layout.

        Uses CubeLayout.same() for proper comparison that handles
        cube rotations correctly. Compares against the global BOY
        instance from cube_boy.

        Args:
            sp: Service provider for configuration.

        Returns:
            True if this layout matches the BOY color scheme.
        """
        current: CubeLayout = self.get_layout(sp)
        return current.is_boy()

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
        """Create a Cube3x3Colors with all WHITE placeholders using the global BOY layout.

        All colors are initialized to WHITE and should be overwritten with actual colors.
        The structure (which edges connect which faces) comes from the global BOY layout,
        making CubeLayout the authority for all layout questions.

        Args:
            sp: Service provider to access the global BOY layout.

        Returns:
            Cube3x3Colors with all edges/corners/centers initialized to WHITE.

        Note: The resulting structure won't be valid until all colors are set to actual values.

        Example:
            empty = Cube3x3Colors.create_empty(sp)
        """
        from cube.domain.model._part import CornerName, EdgeName
        from cube.domain.geometric import cube_boy

        # Get the global BOY layout (cached singleton)
        boy_layout = cube_boy.get_boy_layout(sp)

        # Get edge-to-faces mapping from layout (the authoritative source)
        edge_faces_map = boy_layout.edge_faces()

        # Create empty edge colors for all 12 edges
        edges: dict[EdgeName, EdgeColors] = {}
        for edge_name, (f1, f2) in edge_faces_map.items():
            edges[edge_name] = EdgeColors({f1: Color.WHITE, f2: Color.WHITE})

        # Get corner-to-faces mapping from layout (the authoritative source)
        corner_faces_map = boy_layout.corner_faces()

        # Create empty corner colors for all 8 corners
        corners: dict[CornerName, CornerColors] = {}
        for corner_name, (f1, f2, f3) in corner_faces_map.items():
            corners[corner_name] = CornerColors({f1: Color.WHITE, f2: Color.WHITE, f3: Color.WHITE})

        # Create empty centers (WHITE placeholder)
        centers: dict[FaceName, Color] = {fn: Color.WHITE for fn in FaceName}

        return Cube3x3Colors(edges=edges, corners=corners, centers=centers)
