"""Beginner 3x3 solver - pure layer-by-layer 3x3 cube solving."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.model import Color, Part
from cube.domain.model.Face import Face
from cube.domain.solver._3x3.shared.L1Cross import L1Cross
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.protocols.Solver3x3Protocol import Solver3x3Protocol
from cube.domain.solver.solver import SolverResults, SolveStep
from cube.domain.solver.SolverName import SolverName

if TYPE_CHECKING:
    from cube.utils.logger_protocol import ILogger

from ._L1Corners import L1Corners
from ._L2 import L2
from ._L3Corners import L3Corners
from ._L3Cross import L3Cross


def _is_cross_on_face(face: Face) -> bool:
    """Check if L1 cross is solved on face (Co).

    Cross = all 4 edge stickers on face are face color, AND the edge
    stickers on adjacent faces follow the color scheme (possibly rotated).
    Uses rotate_face_and_check to handle face rotation.
    """
    # Quick: all edge face-side stickers must be face color
    if not all(e.match_face(face) for e in face.edges):
        return False
    # Full: adjacent stickers must match (with rotation)
    return face.cube.cqr.rotate_face_and_check(
        face, lambda: Part.all_match_faces(face.edges)
    ) >= 0


def _is_corners_on_face(face: Face, cross_solved: bool) -> bool:
    """Check if L1 corners are solved on face (Cr).

    Corners = all 4 corner stickers on face are face color, AND corner
    stickers on adjacent faces match adjacent edges (color scheme).
    If cross is solved, uses rotate_face_and_check for both cross + corners.
    """
    # Quick: all corner face-side stickers must be face color
    if not all(c.match_face(face) for c in face.corners):
        return False
    if cross_solved:
        # Verify corners align with cross (same rotation)
        return face.cube.cqr.rotate_face_and_check(
            face, lambda: Part.all_match_faces(face.edges) and Part.all_match_faces(face.corners)
        ) >= 0
    # Corners only (no cross) — check corners alone with rotation
    return face.cube.cqr.rotate_face_and_check(
        face, lambda: Part.all_match_faces(face.corners)
    ) >= 0


def _is_l2_solved(l1_face: Face) -> bool:
    """Check if L2 edges are solved relative to given L1 face.

    L2 edges = edges between adjacent faces that are NOT on L1 or L1.opposite.
    Each edge must have both stickers matching their respective faces.
    """
    opposite = l1_face.opposite
    for adj_face in l1_face.adjusted_faces():
        for e in adj_face.edges:
            if not e.on_face(l1_face) and not e.on_face(opposite):
                if not e.match_faces:
                    return False
    return True


class BeginnerSolver3x3(BaseSolver, Solver3x3Protocol):
    """
    Pure 3x3 beginner layer-by-layer solver.

    Solves a 3x3 cube (or a reduced NxN cube) using the beginner
    layer-by-layer method:
    1. L1 Cross - White cross on bottom
    2. L1 Corners - White corners
    3. L2 - Middle layer edges
    4. L3 Cross - Yellow cross orientation
    5. L3 Corners - Yellow corners permutation

    Does NOT include NxN reduction - use with NxNSolverOrchestrator
    for larger cubes.

    Note: solve_3x3() may raise parity exceptions on even cubes:
    - EvenCubeEdgeParityException: From L3Cross
    - EvenCubeCornerSwapException: From L3Corners

    Inherits from Solver3x3Protocol to satisfy the project's convention.
    """

    __slots__ = ["l1_cross", "l1_corners", "l2", "l3_cross", "l3_corners"]

    def __init__(
        self,
        op: OperatorProtocol,
        parent_logger: "ILogger",
    ) -> None:
        """
        Create a BeginnerSolver3x3.

        Args:
            op: Operator for cube manipulation
            parent_logger: Parent logger (cube.sp.logger for root, parent._logger for child)
        """
        super().__init__(op, parent_logger, logger_prefix="Beginner3x3")

        self.l1_cross = L1Cross(self)
        self.l1_corners = L1Corners(self)
        self.l2 = L2(self)
        self.l3_cross = L3Cross(self)
        self.l3_corners = L3Corners(self)

        # All sub-solvers must share parent's CommonOp so _start_color
        # is a single source of truth (solvers must be stateless).
        for helper in (self.l1_cross, self.l1_corners, self.l2, self.l3_cross, self.l3_corners):
            helper._cmn = self.cmn

    @property
    def get_code(self) -> SolverName:
        """Return solver identifier."""
        return SolverName.LBL

    @property
    def can_detect_parity(self) -> bool:
        """BeginnerSolver3x3 detects parity via exceptions in L3Cross/L3Corners."""
        return True

    def solve_3x3(
        self,
        debug: bool = False,
        what: SolveStep | None = None
    ) -> SolverResults:
        """
        Solve 3x3 cube.

        Args:
            debug: Enable debug output
            what: Which step to solve (default: ALL)

        Returns:
            SolverResults with solve metadata

        Raises:
            EvenCubeEdgeParityException: If edge parity detected in L3
            EvenCubeCornerSwapException: If corner swap parity detected in L3
        """
        sr = SolverResults()

        if self._cube.solved:
            return sr

        if what is None:
            what = SolveStep.ALL

        self._select_best_start_color()

        # Execute appropriate solve steps
        # Note: L3 steps may raise parity exceptions on even cubes
        match what:
            case SolveStep.L1x:
                self.l1_cross.solve()

            case SolveStep.L1:
                self.l1_cross.solve()
                self.l1_corners.solve(self.l1_cross)

            case SolveStep.L2:
                self.l1_cross.solve()
                self.l1_corners.solve(self.l1_cross)
                self.l2.solve()

            case SolveStep.L3x:
                self.l1_cross.solve()
                self.l1_corners.solve(self.l1_cross)
                self.l2.solve()
                self.l3_cross.solve()

            case SolveStep.ALL | SolveStep.L3:
                self.l1_cross.solve()
                self.l1_corners.solve(self.l1_cross)
                self.l2.solve()
                self.l3_cross.solve()
                self.l3_corners.solve()

            case SolveStep.F2L:
                # F2L is CFOP terminology, but support it here too
                self.l1_cross.solve()
                self.l1_corners.solve(self.l1_cross)
                self.l2.solve()

        return sr

    @property
    def status_3x3(self) -> str:
        """Human-readable 3x3 solving status.

        Purely read-only — does NOT mutate solver state.
        Finds L1 face by checking face colors + adjacent scheme order,
        then checks L2/L3 relative to that face. All parametric.
        """
        if self._cube.solved:
            return "Solved"

        # Find L1 face — no state mutation
        l1_face: Face | None = None
        has_cross = False
        has_corners = False
        for face in self._cube.faces:
            cr = _is_cross_on_face(face)
            co = _is_corners_on_face(face, cr)
            if cr or co:
                l1_face = face
                has_cross = cr
                has_corners = co
                if cr and co:
                    break  # Full L1 — no need to keep searching

        if l1_face is not None:
            label = l1_face.color.name[0]
            if has_cross and has_corners:
                s = f"L1({label})"
            elif has_cross:
                s = f"L1x({label})"
            else:
                s = f"L1c({label})"
        else:
            s = "No-L1"

        # L2: 4 edges between adjacent faces (not on L1 or L1.opposite)
        if l1_face is not None and _is_l2_solved(l1_face):
            s += ", L2"
        else:
            s += ", No L2"

        # L3: opposite face of L1
        if l1_face is not None:
            l3_face = l1_face.opposite
            l3_cross = _is_cross_on_face(l3_face)
            l3_corners = _is_corners_on_face(l3_face, l3_cross)
            if l3_cross and l3_corners:
                s += ", L3"
            elif l3_cross:
                s += ", L3x"
            elif l3_corners:
                s += ", L3c"
            else:
                s += ", No L3"
        else:
            s += ", No L3"

        return s

    def _select_best_start_color(self) -> None:
        """Pick the best starting color for L1.

        Scans all 6 faces using standalone _is_cross_on_face/_is_corners_on_face.
        If any face has a solved L1 (cross + corners), uses that color.
        Only called before solving — this is the ONLY place that mutates _start_color.
        """
        saved_color: Color = self.cmn.white

        for face in self._cube.faces:
            if _is_cross_on_face(face) and _is_corners_on_face(face, True):
                if face.color != saved_color:
                    self._logger.debug(None, f"L1 already solved on {face.color}, using as start color")
                saved_color = face.color
                break

        self.cmn._start_color = saved_color

    # Required by Solver ABC - delegate to status_3x3
    @property
    def _status_impl(self) -> str:
        """Human-readable solver status."""
        return self.status_3x3

    def _solve_impl(self, what: SolveStep) -> SolverResults:
        """Solve the cube. Called by AbstractSolver.solve().

        Animation and OpAborted are handled by the template method.

        Args:
            what: Which step to solve

        Returns:
            SolverResults with solve metadata
        """
        return self.solve_3x3(self._is_debug_enabled, what)

    def _supported_steps_impl(self) -> list[SolveStep]:
        """Return list of solve steps this solver supports.

        BeginnerSolver3x3 uses layer-by-layer method with these steps:
        L1x (cross), L1 (complete), L2, L3x (cross), L3 (complete).
        """
        return [
            SolveStep.L1x,
            SolveStep.L1,
            SolveStep.L2,
            SolveStep.L3x,
            SolveStep.L3,
        ]
