"""Edge slice parity fix for NxN cubes (OLL parity).

Contains both basic (M-slice) and advanced (R/L-slice) algorithms for
flipping misoriented edge slices. All callers that need to fix edge
parity go through this class.

Basic (M-slice):
    Simple 4×(M' U2) M' pattern. Fast but disturbs other edges.

Advanced (R/L-slice):
    https://speedcubedb.com/a/6x6/6x6L2E
    R/L-slice pattern that preserves other edges.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

from cube.domain.algs import Algs
from cube.domain.model import Color, Edge, EdgeWing
from cube.domain.model.Face import Face
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.ParityFix import ParityFix
from cube.domain.solver.common.CommonOp import EdgeSliceTracker
from cube.domain.solver.common.SolverHelper import SolverHelper

if TYPE_CHECKING:
    from cube.domain.solver.protocols import SolverElementsProvider


class EdgeSliceParity(SolverHelper):
    """Fix edge parity (OLL parity) by flipping inner edge slices.

    On even cubes, all slices of an edge can be flipped together — invisible
    during reduction but detected by L3Cross as 1 or 3 flipped edges.

    On odd cubes, partial parity (some slices flipped) is detected during
    reduction and fixed here too.

    Two algorithms:
    - Basic (M-slice): simple, disturbs other edges
    - Advanced (R/L-slice): preserves other edges
    """

    def __init__(self, solver: SolverElementsProvider) -> None:
        super().__init__(solver, "EdgeSliceParity")

    def fix_edge_parity(self, advanced: bool) -> ParityFix:
        """Fix even cube full edge parity on front-left edge.

        Args:
            advanced: If True, use R/L-slice algorithm (preserves edge pairing,
                      no re-reduce needed). If False, use M-slice algorithm
                      (disrupts edge pairing, caller must re-reduce).

        Returns:
            True if advanced algorithm was used (no re-reduce needed),
            False if basic algorithm was used (re-reduce needed).
        """
        assert self.cube.n_slices % 2 == 0
        return self._do_edge_parity_on_edge(self.cube.front.edge_left, advanced)


    def do_edge_parity_on_edge(self, edge: Edge, advanced: bool = False) -> ParityFix:
        """Fix edge parity on a specific edge.

        Brings edge to front-top position, determines which slices need fixing,
        then applies either M-based (basic) or R/L-based (advanced) parity alg.

        Args:
            edge: The edge to fix.
            advanced: If True, use R/L-slice algorithm.
        """
        return self._do_edge_parity_on_edge(edge, advanced)

    def _do_edge_parity_on_edge(self, edge: Edge, advanced: bool) -> ParityFix:
        """Apply OLL parity algorithm to a single edge."""
        with self._logger.tab(lambda: f"Doing edge parity on edge: {edge}"):

            cube = self.cube
            n_slices = cube.n_slices

            face = cube.front

            tracer: EdgeSliceTracker
            with self.cmn.track_e_slice(edge.get_slice(0)) as tracer:
                self.debug(lambda: f"Doing parity on {edge}", level=1)
                edge = self.cmn.bring_edge_to_front_left_by_whole_rotate(edge)
                assert edge is face.edge_left
                assert edge is cube.fl
                self.op.play(Algs.F)

                edge = tracer.the_slice_nl.parent
                assert edge is face.edge_top
                edge = cube.front.edge_top

            if n_slices % 2:
                required_color = self.get_slice_ordered_color(face, edge.get_slice(n_slices // 2))
            else:
                # In even, we can have partial and complete parity. In case of complete,
                # we reach here from solver after finding edge in 3x3. With partial we
                # reach here from the edge solver. In first case we need to reverse all
                # slices, in second case we pick the first one (that can later cause OLL
                # parity when solving as 3x3).
                required_color = self.get_slice_ordered_color(face, edge.get_slice(0))
                required_color = required_color[::-1]

            slices_to_fix: list[EdgeWing] = []
            slices_indices_to_fix: list[int] = []
            _all = True
            for i in range(n_slices // 2):

                s = edge.get_slice(i)
                color = self.get_slice_ordered_color(face, s)
                if color != required_color:
                    slices_indices_to_fix.append(i)
                    slices_to_fix.append(s)
                else:
                    _all = False

            ann = "Fixing edge(OLL) Parity"
            if n_slices % 2 == 0 and _all:
                ann += "(Full even)"

            with self.ann.annotate((slices_to_fix, AnnWhat.Moved), h1=ann):
                # slices are from [1 nn], so we need to add 1
                plus_one = [i + 1 for i in slices_indices_to_fix]

                if not advanced:
                    self._do_basic(plus_one)
                    return ParityFix.NonAdvanced
                else:
                    self._do_advanced(plus_one)
                    return ParityFix.NonAdvanced

    def _do_basic(self, plus_one: list[int]) -> None:
        """Basic M-slice parity fix: 4×([i]M' U2) [i]M'.

        Example on 6x6, flipping slice 3 of the FU edge:
            [3:3]M' U2  [3:3]M' U2  [3:3]M' U2  [3:3]M' U2  [3:3]M'
le
        Net effect: flips the target edge slices in place.

        Disrupts edge pairing: M-slice moves rotate ONLY the inner
        layer without the outer L/R faces. This separates paired
        wing slices on the FL, FR, BL, BR edges that share the same
        M-layer. Caller must re-reduce (re-pair edges) after this fix.
        """
        self.debug(lambda: f"*** Doing parity on M {plus_one}", level=2)
        for _ in range(4):
            self.op.play(Algs.MM[plus_one].prime)
            self.op.play(Algs.U * 2)
        self.op.play(Algs.MM[plus_one].prime)

    def _do_advanced(self, plus_one: list[int]) -> None:
        """Advanced R/L-slice parity fix — preserves edge pairing.

        Uses R/L-slice moves instead of M-slice. These move the outer
        layer together with inner slices, so other edges stay paired.
        No re-reduction needed after this fix.

        Source: https://speedcubedb.com/a/6x6/6x6L2E
        3R' U2 3L F2 3L' F2 3R2 U2 3R U2 3R' U2 F2 3R2 F2
        """
        # In case of R/L we need to add 1, because 1 is R, and slices begin with 2
        plus_one = [i + 1 for i in plus_one]

        self.debug(lambda: f"*** Doing parity on R {plus_one}", level=2)

        rs = Algs.R[plus_one]
        ls = Algs.L[plus_one]
        u2 = Algs.U * 2
        f2 = Algs.F * 2

        alg = (rs.prime + u2 + ls + f2 + ls.prime + f2
               + rs * 2 + u2 + rs + u2 + rs.prime + u2 + f2
               + rs * 2 + f2)

        self.op.play(alg)

    @staticmethod
    def get_slice_ordered_color(f: Face, s: EdgeWing) -> Tuple[Color, Color]:
        """Get the ordered color pair of a slice relative to a face.

        :param f: The face to determine ordering from
        :param s: The edge wing slice
        :return: (color on face f, color on the other face)
        """
        return s.get_face_edge(f).color, s.get_other_face_edge(f).color
