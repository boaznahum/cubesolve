"""EdgesTrackerHolder - tracks edge colors through cube rotations via shadow 3x3.

On big cubes, face rotations (R, L, U, D, F, B) only move the outermost edge
slices — the representative middle slice NEVER moves. So marker-based tracking
on the middle slice doesn't work. Instead, we maintain a lightweight shadow 3x3
cube that receives the same moves as the real cube, and read edge colors from it.

The shadow cube is much simpler than the old DualOperator approach:
- No DualAnnotation / piece mapping
- No special cube property (solver reads from real cube via providers)
- Just move sync + color reading

Usage:
    colors_3x3 = cube.get_3x3_colors()
    modified = colors_3x3.with_centers(th.get_face_colors())
    if cube.is_even:
        modified = modified.with_fixed_non_3x3_edges(cube, cube.original_scheme)

    with EdgesTrackerHolder(cube, modified) as edges_tracker:
        sync_op = edges_tracker.create_sync_operator(real_op)
        with cube.with_faces_color_provider(th, center_3x3_mode=True,
                                            edges_provider=edges_tracker):
            solver = Solvers3x3.beginner(sync_op, ...)
            solver.solve_3x3()

Limitations:
    - Only valid during face rotations (R, L, U, D, F, B) and whole-cube rotations.
    - NOT valid during slice moves (M, E, S) that change 3x3 edge state.
"""

from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING, Any

from cube.domain.model.Color import Color

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Cube3x3Colors import Cube3x3Colors
    from cube.domain.model.Edge import Edge
    from cube.domain.model.Face import Face
    from cube.domain.solver.protocols import OperatorProtocol


class _ShadowSyncOp:
    """Thin operator wrapper that syncs moves to a shadow 3x3 cube.

    Delegates all methods to the real operator, but after each play()
    also applies the same algorithm to the shadow cube.
    """

    def __init__(self, real_op: OperatorProtocol, shadow: Cube) -> None:
        self._real_op = real_op
        self._shadow = shadow

    def play(self, alg: Any, inv: Any = False, animation: Any = True) -> None:
        """Apply alg to both real cube (via operator) and shadow cube (directly)."""
        self._real_op.play(alg, inv=inv, animation=animation)
        # Apply same move to shadow (resolve inv, no animation)
        resolved = alg.inv() if inv else alg
        resolved.play(self._shadow, False)

    def __getattr__(self, name: str) -> Any:
        """Delegate all other methods/properties to the real operator."""
        return getattr(self._real_op, name)


class EdgesTrackerHolder:
    """Tracks assigned edge colors through cube rotations via a shadow 3x3 cube.

    Maintains a lightweight shadow 3x3 cube with valid edge colors.
    The shadow receives the same moves as the real cube (via _ShadowSyncOp),
    so its edge positions stay in sync. Edge color queries read from the shadow.

    Implements the EdgesColorsProvider protocol.
    """

    __slots__ = ("_cube", "_shadow")

    def __init__(self, cube: Cube, colors_3x3: Cube3x3Colors) -> None:
        """Create tracker with a shadow 3x3 cube initialized from the color snapshot.

        Args:
            cube: The real cube (for reference).
            colors_3x3: Valid 3x3 color snapshot (all edges must have valid pairs).
                        Typically produced by Cube3x3Colors.with_fixed_non_3x3_edges().
        """
        from cube.domain.model.Cube import Cube as CubeClass

        self._cube = cube

        # Create shadow 3x3 cube with the same color scheme
        self._shadow: Cube = CubeClass(size=3, sp=cube.sp, scheme=cube.original_scheme)
        self._shadow.is_even_cube_shadow = cube.is_even
        self._shadow.set_3x3_colors(colors_3x3)

    def create_sync_operator(self, real_op: OperatorProtocol) -> _ShadowSyncOp:
        """Create an operator wrapper that syncs moves to the shadow cube.

        Pass this wrapper to the 3x3 solver instead of the real operator.
        """
        return _ShadowSyncOp(real_op, self._shadow)

    def get_edge_face_color(self, edge: Edge, face: Face) -> Color:
        """Get the assigned color for an edge on a specific face.

        Reads from the shadow 3x3 cube's corresponding edge.
        """
        shadow_edge = self._shadow.edge(edge.name)
        shadow_face = self._shadow.face(face.name)
        return shadow_edge.face_color(shadow_face)

    def get_edge_colors(self, edge: Edge) -> frozenset[Color]:
        """Get assigned color pair for an edge (unordered)."""
        shadow_edge = self._shadow.edge(edge.name)
        return frozenset((shadow_edge.e1.color, shadow_edge.e2.color))

    def __enter__(self) -> EdgesTrackerHolder:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        pass  # No cleanup needed — shadow cube is just garbage collected
