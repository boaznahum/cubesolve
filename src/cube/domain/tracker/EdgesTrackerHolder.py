"""EdgesTrackerHolder - tracks edge colors through cube rotations via markers.

Uses moveable_attributes on PartEdge objects to track assigned edge colors.
Markers travel with the sticker data during rotate_4cycle(), so colors
stay correct through face rotations and whole-cube rotations.

One marker per edge, placed on one PartEdge. The marker value is a tuple
(my_face_color, other_face_color) — so both colors are recoverable from
finding a single PartEdge.

After rotations, the marker may land on a different slice index (due to
ltr coordinate inversion between edges), so the provider searches all
slices to find it (starting from n//2 as optimization).

Usage:
    colors_3x3 = cube.get_3x3_colors()
    modified = colors_3x3.with_centers(th.get_face_colors())
    if cube.is_even:
        modified = modified.with_fixed_non_3x3_edges(cube, cube.original_scheme)

    with EdgesTrackerHolder(cube, modified) as edges_tracker:
        with cube.with_faces_color_provider(th, center_3x3_mode=True,
                                            edges_provider=edges_tracker):
            solver = Solvers3x3.beginner(self._op, ...)
            solver.solve_3x3()

Limitations:
    - Only valid during face rotations (R, L, U, D, F, B) and whole-cube rotations.
    - NOT valid during slice moves (M, E, S) that split edge slices.
"""

from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING

from cube.domain.model.EdgesColorsProvider import EdgesColorsProvider

from cube.domain.exceptions import InternalSWError
from cube.domain.model.Color import Color
from cube.domain.model.PartEdge import PartEdge

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Cube3x3Colors import Cube3x3Colors
    from cube.domain.model.Edge import Edge
    from cube.domain.model.Face import Face

_EDGES_TRACKER_PREFIX = "_edges_track:"


class EdgesTrackerHolder(EdgesColorsProvider):
    """Tracks assigned edge colors through cube rotations via PartEdge markers.

    Places one marker per edge on a representative PartEdge. The marker value
    is (my_face_color, other_face_color). Since moveable_attributes travel
    with the sticker during rotations, the colors stay correct.

    To read: search the edge's slices for the marker (it may have moved to
    a different slice index due to ltr coordinate inversion between edges).

    Implements the EdgesColorsProvider protocol.
    """

    __slots__ = ("_cube", "_key", "_cache_modify_counter", "_cache")

    def __init__(self, cube: Cube, colors_3x3: Cube3x3Colors) -> None:
        """Create tracker by marking one PartEdge per edge with assigned colors.

        Args:
            cube: The real cube.
            colors_3x3: Valid 3x3 color snapshot (all edges must have valid pairs).
                        Typically produced by Cube3x3Colors.with_fixed_non_3x3_edges().
        """
        self._cube = cube
        self._key = f"{_EDGES_TRACKER_PREFIX}{id(self):x}"
        self._cache_modify_counter: int = -1
        self._cache: dict[str, tuple[PartEdge, tuple[Color, Color]]] = {}

        # Mark one PartEdge per edge with (my_face_color, other_face_color)
        for edge_name, edge_colors in colors_3x3.edges.items():
            edge = cube.edge(edge_name)
            # Pick e1 (first representative PartEdge)
            pe = edge.e1
            my_face_name = pe.face.name
            other_face_name = next(fn for fn in edge_colors.colors if fn != my_face_name)
            pe.moveable_attributes[self._key] = (
                edge_colors.colors[my_face_name],
                edge_colors.colors[other_face_name],
            )

    def _find_marker(self, edge: Edge) -> tuple[PartEdge, tuple[Color, Color]]:
        """Search edge slices for our marker.

        Starts from n//2 as optimization (marker is often near the middle).

        Returns:
            (found_pe, (my_color, other_color)) where my_color is for found_pe.face
        """
        # Check cache
        #claude you dont need it, cube.domain.model.Cube.Cube.mutation_cache does the work
        current_counter = self._cube._modify_counter
        if self._cache_modify_counter == current_counter:
            cached = self._cache.get(edge._name)
            if cached is not None:
                return cached

        # Search all slices
        n = edge.n_slices
        start = n // 2
        key = self._key
        for offset in range(n):
            idx = (start + offset) % n
            sl = edge.get_slice(idx)
            for pe in sl.edges:
                if key in pe.moveable_attributes:
                    result: tuple[PartEdge, tuple[Color, Color]] = (
                        pe, pe.moveable_attributes[key]
                    )
                    # Update cache
                    if self._cache_modify_counter != current_counter:
                        self._cache.clear()
                        self._cache_modify_counter = current_counter
                    self._cache[edge._name] = result
                    return result

        raise InternalSWError(f"Edge marker {self._key} not found on {edge}")

    def get_edge_face_color(self, edge: Edge, face: Face) -> Color:
        """Get the assigned color for an edge on a specific face."""
        pe, (my_color, other_color) = self._find_marker(edge)
        if pe.face is face:
            return my_color
        else:
            return other_color

    def get_edge_colors(self, edge: Edge) -> frozenset[Color]:
        """Get assigned color pair for an edge (unordered)."""
        _, (my_color, other_color) = self._find_marker(edge)
        return frozenset((my_color, other_color))

    def _cleanup(self) -> None:
        """Remove markers from all edge PartEdges."""
        key = self._key
        for edge in self._cube.edges:
            for sl in edge.all_slices:
                for pe in sl.edges:
                    if key in pe.moveable_attributes:
                        del pe.moveable_attributes[key]
                        break  # only one marker per edge

    def __enter__(self) -> EdgesTrackerHolder:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._cleanup()
