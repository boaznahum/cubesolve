"""Protocol for providing edge colors during 3x3 solving on big cubes.

When solving L1/L3 on big cubes, some edges may not be fully paired
(is3x3=False). The 3x3 solver needs valid edge colors that track through
moves. This protocol allows overriding Edge.colors_id and Edge.face_color
with tracker-assigned colors.

Mirrors the FacesColorsProvider pattern for centers.
See: FacesColorsProvider.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from cube.domain.model.Color import Color

if TYPE_CHECKING:
    from cube.domain.model.Edge import Edge
    from cube.domain.model.Face import Face


class EdgesColorsProvider(Protocol):
    """Provider of reliable edge colors for big cube 3x3 solving.

    Implementations (e.g., EdgesTrackerHolder) use moveable_attributes
    on PartEdge objects to track assigned colors through cube rotations.
    """

    def get_edge_face_color(self, edge: Edge, face: Face) -> Color:
        """Get the assigned color for an edge on a specific face.

        Args:
            edge: The edge to query (positional — represents the slot).
            face: The face to get the color for (must be one of the edge's two faces).

        Returns:
            The assigned color for that edge-face combination.
        """
        ...

    def get_edge_colors(self, edge: Edge) -> tuple[Color, Color]:
        """Get the assigned color pair for an edge, ordered as (e1_color, e2_color).

        Args:
            edge: The edge to query.

        Returns:
            Tuple of (e1 face color, e2 face color).
        """
        ...
