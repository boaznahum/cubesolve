from collections import defaultdict
from typing import Tuple

from cube.domain.exceptions import InternalSWError
from cube.domain.model import Color, Edge, PartColorsID
from cube.domain.model.Face import Face
from cube.domain.model.ModelHelper import ModelHelper
from cube.domain.tracker._face_trackers import FaceTracker
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.solver.common.big_cube.NxNEdgesCommon import NxNEdgesCommon
from cube.domain.solver.protocols import SolverElementsProvider


class NxNEdges(SolverHelper):
    D_LEVEL = 3

    def __init__(self, slv: SolverElementsProvider,
                 advanced_edge_parity: bool,
                 preserve_other_edges: bool = False) -> None:
        super().__init__(slv, "NxNEdges")
        self._logger.set_level(NxNEdges.D_LEVEL)
        self._edges_common = NxNEdgesCommon(slv, advanced_edge_parity, preserve_other_edges)


    def solved(self) -> bool:
        return self._edges_common.solved()

    def solve(self) -> bool:
        return self._edges_common.solve()

    def solve_face_edges(self, face_tracker: FaceTracker) -> bool:
        """Solve only the 4 edges that contain a specific color.

        Used by layer-by-layer solver to solve one layer's edges at a time.

        Args:
            face_tracker: FaceTracker for the target face (tracks by color).

        Returns:
            True if edge parity was performed, False otherwise.

        Note:
            Finds edges by COLOR (e.g., all edges containing WHITE for white cross),
            not by position. This is correct because after centers are solved,
            the cross edges may be scattered across the cube.
        """
        # Find the 4 edges that contain the target color (by color, not position!)
        # For white cross: finds edges with WHITE (checking ALL slices, not just representative)
        target_color = face_tracker.color
        target_edges_by_color = [e for e in self.cube.edges
                                if NxNEdges._edge_contains_color(e, target_color)]

        with self._logger.tab(lambda : f"Doing face {target_color} edges"):

            # in cas eof even cube it might that two edges ahve the same color , becuase
            # we dont have middle slice
            assert (self.cube.is_even and len(target_edges_by_color) >= 4) or len(target_edges_by_color) == 4, \
                f"Expected 4 edges with {target_color}, found {len(target_edges_by_color)}"

            target_edges_by_color = target_edges_by_color[:4]

            # Check if all target edges are already solved (paired)
            if all(e.is3x3 for e in target_edges_by_color):
                return False

            with self.ann.annotate(h1=f"Edges for {target_color.name}"):
                parity_done = False
                while True:
                    # Find unsolved edges containing target color (re-query each iteration)
                    # For scrambled even cubes, check ANY slice (not just colors_id representative)
                    unsolved = [e for e in self.cube.edges
                               if NxNEdges._edge_contains_color(e, target_color) and not e.is3x3]
                    if not unsolved:
                        break

                    # Check if this is the LAST unsolved edge in the WHOLE cube
                    # (parity can only happen when all other 11 edges are solved)
                    total_cube_unsolved = sum(1 for e in self.cube.edges if not e.is3x3)
                    if total_cube_unsolved == 1 and len(unsolved) == 1:
                        # Last edge in whole cube AND it's one of our targets - parity
                        self._edges_common._do_last_edge_parity()
                        parity_done = True
                        continue

                    # Solve one edge
                    edge = unsolved[0]
                    # For even cubes: specify required_color to force correct orientation
                    # For odd cubes: use auto-detection (None) because middle slice defines identity
                    required_color_param = target_color if self.cube.is_even else None
                    self._do_edge(edge, required_color=required_color_param)

                return parity_done

    def _do_edge(self, edge: Edge, required_color: Color | None = None) -> bool:
        """Solve a single edge by pairing all its slices.

        Args:
            edge: The edge to solve.
            required_color: If provided, ensure this color is used as the primary
                color when determining ordered_color. Used by solve_face_edges()
                to solve edges for a specific face. If None, auto-detects the
                best color (existing behavior).

        Returns:
            True if the edge was solved, False if already solved.
        """

        if edge.is3x3:
            self.debug( f"Edge {edge} is already solved", level=3)
            return False
        else:
            self.debug( f"Need to work on Edge {edge} ", level=3)

        # find needed color
        n_slices = self.cube.n_slices
        color_un_ordered: PartColorsID

        face = self.cube.front

        with self.ann.annotate(h2=lambda: f"Fixing {edge.name_n_faces}"):

            self.debug( f"Brining {edge} to front-right", level=3)
            self.cmn.bring_edge_to_front_left_by_whole_rotate(edge)
            edge = self.cube.front.edge_left

            # Determine the ordered color to solve for
            if required_color is not None:
                # Use the specified required color (from solve_face_edges)
                ordered_color = self._determine_ordered_color_for_required_color(
                    face, edge, required_color
                )
                color_un_ordered = frozenset(ordered_color)
            elif n_slices % 2:
                # Odd cube: use middle slice color (auto-detect)
                _slice = edge.get_slice(n_slices // 2)
                color_un_ordered = _slice.colors_id
                ordered_color = NxNEdgesCommon.get_slice_ordered_color(face, _slice)
            else:
                # Even cube: find most common color (auto-detect)
                ordered_color = self._edges_common._find_max_of_color(face, edge)
                color_un_ordered = frozenset(ordered_color)

            # Override the above
            def _h2():
                return f"/Fixing {edge.name_n_faces} " \
                       f"{ModelHelper.color_id_to_name(ordered_color)}"

            with self.ann.annotate(h2=_h2):
                self._edges_common._solve_on_front_left(color_un_ordered, ordered_color)

                self._edges_common._report_done(f"Done {edge}")

            return True

    def _find_most_common_pair_with_color(self, edge: Edge, required_color: Color) -> Color:
        """Find the color that most commonly pairs with required_color on this edge.

        For very scrambled edges, multiple colors may appear. This finds which
        color appears most often paired with the required_color.

        Args:
            edge: The edge to analyze.
            required_color: The color we're solving for.

        Returns:
            The color that most frequently pairs with required_color.
        """
        pair_counts: dict[Color, int] = defaultdict(int)

        for i in range(edge.n_slices):
            slice_colors = edge.get_slice(i).colors_id
            if required_color in slice_colors:
                # This slice contains required_color - count its pair
                other = next(c for c in slice_colors if c != required_color)
                pair_counts[other] += 1

        if not pair_counts:
            raise InternalSWError(
                f"Edge {edge} has no slices containing {required_color}"
            )

        # Return the most common pairing
        return max(pair_counts, key=pair_counts.get)  # type: ignore

    @staticmethod
    def _edge_contains_color(edge: Edge, color: Color) -> bool:
        """Check if this edge contains the given color.

        For odd cubes (3x3, 5x5, 7x7):
            Only check the middle/representative slice (edge.colors_id).
            The middle slice defines the edge's identity. Other slices may have
            different colors during scrambling, but they don't change what edge this is.

        For even cubes (4x4, 6x6, 8x8):
            Check ALL slices. During scrambling, slices can have different color-pairs,
            so we need to check if any slice contains the target color.

        Args:
            edge: The edge to check.
            color: The color to look for.

        Returns:
            True if the edge contains this color.
        """
        # Odd cube: Only check representative slice (middle slice)
        if edge.n_slices % 2 == 1:
            return color in edge.colors_id

        # Even cube: Check all slices
        for i in range(edge.n_slices):
            if color in edge.get_slice(i).colors_id:
                return True
        return False

    def do_even_full_edge_parity_on_any_edge(self):
        self._edges_common.do_even_full_edge_parity_on_any_edge()

    def _determine_ordered_color_for_required_color(
        self, face: Face, edge: Edge, required_color: Color
    ) -> Tuple[Color, Color]:
        """Determine ordered_color with required_color as primary, using majority vote.

        Used by solve_face_edges() to ensure we solve for the correct face color.
        Counts which orientation appears most often, preferring the one with
        required_color on the face.

        Args:
            face: The face where the edge is positioned (front after rotation).
            edge: The edge to solve.
            required_color: The color that must be on the face (e.g., WHITE
                for white cross).

        Returns:
            Tuple of (color_on_face, color_on_other_face) representing the
            target orientation for all slices.

        Raises:
            InternalSWError: If required_color is not in the edge's colors.
        """
        # Verify the edge contains the required color (check ALL slices, not just representative)
        if not NxNEdges._edge_contains_color(edge, required_color):
            raise InternalSWError(
                f"Edge {edge} does not contain required color {required_color} in any slice. "
                f"Representative colors: {edge.colors_id}"
            )

        # Find all colors that appear on this edge (across all slices)
        all_colors: set[Color] = set()
        for i in range(edge.n_slices):
            all_colors.update(edge.get_slice(i).colors_id)

        # Get the other color(s) that appear with required_color
        other_colors = all_colors - {required_color}
        if len(other_colors) != 1:
            # Edge is very scrambled - has more than 2 unique colors total
            # Pick the most common pairing with required_color
            other_color = self._find_most_common_pair_with_color(edge, required_color)
        else:
            other_color = next(iter(other_colors))

        # Count orientations: how many slices have required_color on face vs other face
        # Only count slices that have the required_color paired with other_color
        # We want to pick the majority orientation, preferring required_color on face
        n_required_on_face = 0
        n_required_on_other = 0
        target_pair = frozenset({required_color, other_color})

        for i in range(edge.n_slices):
            _slice = edge.get_slice(i)
            if _slice.colors_id != target_pair:
                continue  # Skip slices with different color-pair (very scrambled edge)

            ordered = NxNEdgesCommon.get_slice_ordered_color(face, _slice)
            face_color, other_face_color = ordered

            self.debug(f"  Slice {i}: face={face}, ordered={ordered}, face_color={face_color}, other_face_color={other_face_color}, required={required_color}")

            if face_color == required_color:
                n_required_on_face += 1
            elif other_face_color == required_color:
                n_required_on_other += 1

        self.debug(f"  Counts: n_required_on_face={n_required_on_face}, n_required_on_other={n_required_on_other}")

        # CRITICAL: We want required_color on the face (e.g., WHITE on F for white cross).
        # The counting tells us the CURRENT state of scrambled edge, not the TARGET state!
        #
        # If n_required_on_face > 0: Some slices already have correct orientation
        # If n_required_on_other > 0: Some/all slices have WRONG orientation (flipped)
        #
        # We ALWAYS want (required_color, other_color) to solve edge with required_color on face!
        #
        # The old logic was: if all slices have required_color on OTHER face, return (other_color, required_color)
        # This is WRONG because it tells the solver to KEEP the wrong orientation!

        self.debug(f"  Returning: (required_color={required_color}, other_color={other_color})")
        return (required_color, other_color)
