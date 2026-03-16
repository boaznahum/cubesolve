from collections import defaultdict
from typing import Tuple

from cube.domain.algs import Alg, Algs
from cube.domain.exceptions import InternalSWError
from cube.domain.model import Color, Edge, EdgeWing, PartColorsID
from cube.domain.model.Face import Face
from cube.domain.model.ModelHelper import ModelHelper
from cube.domain.tracker._face_trackers import FaceTracker
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.solver.common.big_cube.NxNEdgesCommon import NxNEdgesCommon
from cube.domain.solver.protocols import SolverElementsProvider
from cube.utils.OrderedSet import OrderedSet


class NxNEdges(SolverHelper):
    work_on_b: bool = True

    D_LEVEL = 3

    def __init__(self, slv: SolverElementsProvider,
                 advanced_edge_parity: bool,
                 preserve_other_edges: bool = False) -> None:
        super().__init__(slv, "NxNEdges")
        self._logger.set_level(NxNEdges.D_LEVEL)
        self._advanced_edge_parity = advanced_edge_parity
        self._preserve_other_edges = preserve_other_edges
        self._edges_common = NxNEdgesCommon(slv, advanced_edge_parity)


    def _is_solved(self):
        return all((e.is3x3 for e in self.cube.edges))

    def solved(self) -> bool:
        """

        :return: if all centers have unique colors, and it is a boy
        """

        return self._is_solved()

    def solve(self) -> bool:
        """

        :return: True if edge parity was performed
        """

        if self._is_solved():
            return False

        with self.ann.annotate(h1="Big cube edges"):
            self._do_first_11()

            if self._is_solved():
                return False

            assert self._left_to_fix == 1

            # even cube can have edge parity too
            self._do_last_edge_parity()

            self._do_first_11()

            assert self._is_solved()

            return True

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
                        self._do_last_edge_parity()
                        parity_done = True
                        continue

                    # Solve one edge
                    edge = unsolved[0]
                    # For even cubes: specify required_color to force correct orientation
                    # For odd cubes: use auto-detection (None) because middle slice defines identity
                    required_color_param = target_color if self.cube.is_even else None
                    self._do_edge(edge, required_color=required_color_param)

                return parity_done

    def _do_first_11(self):
        """

        :return:
        """

        # We must not try to solve the last one - it is parity - even in even cube
        while self._left_to_fix > 1:
            n_to_fix = self._left_to_fix
            # we need to search again and gain because solving move all edges
            # search first front-left to avoid rotation
            e = next(e for e in [self.cube.front.edge_left, *self.cube.front.edges, *self.cube.edges] if not e.is3x3)
            assert e
            self._do_edge(e)
            assert self._left_to_fix < n_to_fix

    def _report_done(self, s):
        n_to_fix = sum(not e.is3x3 for e in self.cube.edges)
        self.debug( f"{s}, Still more to fix {n_to_fix}", level=2)

    @property
    def _left_to_fix(self) -> int:
        n_to_fix = sum(not e.is3x3 for e in self.cube.edges)
        return n_to_fix

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

        # if self._left_to_fix < 2:
        #     self.debug( f"But I can't continue because I'm the last {edge} ", level=3)
        #     return False

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
                ordered_color = self._get_slice_ordered_color(face, _slice)
            else:
                # Even cube: find most common color (auto-detect)
                ordered_color = self._find_max_of_color(face, edge)
                color_un_ordered = frozenset(ordered_color)

            # Override the above
            def _h2():
                return f"/Fixing {edge.name_n_faces} " \
                       f"{ModelHelper.color_id_to_name(ordered_color)}"

            with self.ann.annotate(h2=_h2):
                self._solve_on_front_left(color_un_ordered, ordered_color)

                self._report_done(f"Done {edge}")

            return True

    def _solve_on_front_left(self, color_un_ordered: PartColorsID, ordered_color: Tuple[Color, Color]):
        """
        Edge is on front left, and we need to solve it without moving it
        :return:
        """

        # first we need to find the right color

        cube = self.cube
        face = cube.front
        edge: Edge = face.edge_left

        # now start to work
        self.debug( f"Working on edge {edge} color {ordered_color}", level=3)

        # first fix all that match color on this edge
        self._fix_all_slices_on_edge(face, edge, ordered_color, color_un_ordered)

        # now search in other edges
        self._fix_all_from_other_edges(face, edge, ordered_color, color_un_ordered)

    def _fix_all_slices_on_edge(self, face: Face, edge: Edge, ordered_color: Tuple[Color, Color],
                                color_un_ordered: PartColorsID):

        n_slices = edge.n_slices

        inv = edge.inv

        edge_can_destroyed: Edge | None = None

        is_last = self._left_to_fix == 1

        assert not is_last

        # Why set, because sometimes we need to fix i nad inv(i), so when we reach inv(i) we will try to add
        # again inv(inv(i)) == i
        slices_to_fix = OrderedSet[int]()
        slices_to_slice = OrderedSet[int]()

        for i in range(0, n_slices):

            a_slice = edge.get_slice(i)

            a_slice_id = a_slice.colors_id

            if a_slice_id != color_un_ordered:
                continue

            ordered = self._get_slice_ordered_color(face, a_slice)
            if ordered == ordered_color:
                # done
                continue

            if n_slices % 2 and i == n_slices // 2:
                raise InternalSWError()

            other_slice_i = inv(i)
            other_slice = edge.get_slice(other_slice_i)
            other_order = self._get_slice_ordered_color(face, other_slice)
            if other_order == ordered_color:
                raise InternalSWError("Don't know what to do")

            slices_to_fix.add(i)
            slices_to_slice.add(i)
            slices_to_slice.add(inv(i))

        if not slices_to_fix:
            return

        # bring an edge to help
        if not is_last and edge_can_destroyed is None:
            search_in: list[Edge] = [self.cube.front.edge_right, *OrderedSet(self.cube.edges) - {edge}]
            edge_can_destroyed = self.cqr.find_edge(search_in, lambda e: not e.is3x3)
            assert edge_can_destroyed
            self.cmn.bring_edge_to_front_right_preserve_front_left(edge_can_destroyed)

        slices = [edge.get_slice(i) for i in slices_to_slice]
        ltrs = [edge.get_face_ltr_index_from_edge_slice_index(face, i) for i in slices_to_slice]

        # Now fix

        self.debug( f"On same edge, going to slice {ltrs}", level=3)

        with self.ann.annotate((slices, AnnWhat.Moved),
                               (lambda: (edge.get_slice(inv(i)) for i in slices_to_slice),
                                AnnWhat.FixedPosition),
                               h2="Flip on same edge"
                               ):

            slice_alg = Algs.EE[[ltr + 1 for ltr in ltrs]]

            self.op.play(slice_alg)  # move me to opposite E begin from D, slice begin with 1
            self.op.play(self.rf)
            # bring them back
            self.op.play(slice_alg.prime)  # move me to opposite E begin from D, slice begin with 1

            if self._preserve_other_edges:
                # ig LBL want sits edges to be preserved
                self.op.play(self.rf.prime)


        for i in slices_to_fix:
            assert self._get_slice_ordered_color(face, edge.get_slice(inv(i))) == ordered_color

    def _fix_all_from_other_edges(self, face: Face, edge: Edge, ordered_color: Tuple[Color, Color],
                                  color_un_ordered: PartColorsID):

        other_edges = OrderedSet(face.cube.edges) - {edge}
        assert len(other_edges) == 11

        while not edge.is3x3:

            # start from one on right - to optimize
            edge_right = face.edge_right
            _other_edges = [edge_right, *(other_edges - {edge_right})]
            source_slice = self.cqr.find_slice_in_edges(_other_edges,
                                                           lambda s: s.colors_id == color_un_ordered)

            assert source_slice

            self.debug( f"Found source slice {source_slice}", level=3)

            self.cmn.bring_edge_to_front_right_preserve_front_left(source_slice.parent)

            source_slice = self._find_slice_in_edge_by_color_id(edge_right, color_un_ordered)
            assert source_slice

            while self._find_slice_in_edge_by_color_id(edge_right, color_un_ordered):
                # ok now do for all that color order match
                # is there one that can be sliced ?

                rf: Alg | None = None
                if not any(self._get_slice_ordered_color(face, s) == ordered_color for s in edge_right.all_slices):
                    rf = self.rf
                    self.op.play(rf)

                self._fix_many_from_other_edges_same_order(face, edge, ordered_color, color_un_ordered)

                if rf is not None and self._preserve_other_edges:
                    self.op.play(rf.prime)

    def _fix_many_from_other_edges_same_order(self, face: Face, edge: Edge, ordered_color: Tuple[Color, Color],
                                              color_un_ordered: PartColorsID):

        """
        Source edge is in front right

        Slice all slices that are opposite of required color
        :param face:
        :param edge:
        :param ordered_color:
        :param color_un_ordered:
        :return:
        """

        inv = edge.inv

        source_slice_indices = []
        source_slices = []
        target_slices = []
        target_indices = []

        edge_right = face.edge_right

        for source_index in range(edge.n_slices):

            source_slice = edge_right.get_slice(source_index)

            if source_slice.colors_id != color_un_ordered:
                continue  # skip this one

            if self._get_slice_ordered_color(face, source_slice) != ordered_color:
                continue  # we will handle it in next iteration

            source_ltr_index = edge_right.get_face_ltr_index_from_edge_slice_index(face, source_index)

            # source nad target have the sme lrt
            target_index = edge.get_edge_slice_index_from_face_ltr_index(face, source_ltr_index)

            target_index = inv(target_index)  # we want to bring to opposite location

            # if n slices=4, we can't handle both 1, 4, it will be handled in next iteration
            if inv(target_index) in target_indices:
                continue

            source_slices.append(source_slice)
            source_slice_indices.append(source_index)

            target_slice = edge.get_slice(target_index)

            target_slices.append(target_slice)
            target_indices.append(target_index)

            if target_slice.colors_id == color_un_ordered:
                raise InternalSWError("Don't know how to handle")

        if not target_slices:
            return False

        self.debug( f"Going to slice, sources={source_slice_indices}, target={target_indices}", level=3)

        # now slice them all
        with self.ann.annotate((source_slices, AnnWhat.Moved), (target_slices, AnnWhat.FixedPosition)):

            slice_alg = Algs.EE[[i + 1 for i in target_indices]]

            # for target_index in target_indices:
            #     # slice me
            self.op.play(slice_alg)  # slice begin with 1
            self.op.play(self.rf)
            # for target_index in target_indices:
            self.op.play(slice_alg.prime)

            if self._preserve_other_edges:
                self.op.play(self.rf.prime)

        for target_index in target_indices:
            assert self._get_slice_ordered_color(face, edge.get_slice(target_index)) == ordered_color

        return True

    def _do_last_edge_parity(self):

        assert self._left_to_fix == 1

        # self.op.toggle_animation_on()
        # still don't know how to handle
        cube = self.cube

        edge = self.cqr.find_edge(cube.edges, lambda e: not e.is3x3)
        assert edge

        self._do_edge_parity_on_edge(edge)

    def _do_edge_parity_on_edge(self, edge) -> None:
        self._edges_common._do_edge_parity_on_edge(edge)

    @staticmethod
    def _get_slice_ordered_color(f: Face, s: EdgeWing) -> Tuple[Color, Color]:
        """

        :param f:
        :param s:
        :return:  (on face color, on_other color)
        """

        return s.get_face_edge(f).color, s.get_other_face_edge(f).color

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

    @staticmethod
    def _find_slice_in_edge_by_color_id(edge: Edge, color_un_ordered: PartColorsID) -> EdgeWing | None:

        for i in range(edge.n_slices):
            s = edge.get_slice(i)
            if s.colors_id == color_un_ordered:
                return s

        return None

    @property
    def rf(self) -> Alg:
        return Algs.R + Algs.F.prime + Algs.U + Algs.R.prime + Algs.F

    def do_even_full_edge_parity_on_any_edge(self):
        assert self.cube.n_slices % 2 == 0

        self._do_edge_parity_on_edge(self.cube.front.edge_left)

    def _find_max_of_color(self, face, edge) -> Tuple[Color, Color]:
        """Auto-detect the most common color pair on an edge.

        Used for even cubes when no required color is specified.
        Counts which color-pair appears most frequently and picks the
        orientation that appears most often.
        """
        c_max = None
        n_max = 0

        hist: dict[PartColorsID, int] = defaultdict(int)

        for i in range(0, self.cube.n_slices):

            c = edge.get_slice(i).colors_id

            hist[c] += 1

            if hist[c] > n_max:
                n_max = hist[c]
                c_max = c

        assert c_max

        n_c1 = 0
        n_c2 = 0
        c1 = None
        c2 = None

        for i in range(self.cube.n_slices):

            _slice = edge.get_slice(i)
            if _slice.colors_id == c_max:

                c = edge.get_slice(i).colors_id

                ordered = self._get_slice_ordered_color(face, _slice)

                if c == ordered:
                    n_c1 += 1
                    c1 = ordered
                else:
                    n_c2 += 1
                    c2 = ordered

        assert c1 or c2

        if n_c1 > n_c2:
            assert c1
            return c1
        else:
            assert c2
            return c2

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

            ordered = self._get_slice_ordered_color(face, _slice)
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
