from cube.domain.tracker._face_trackers import FaceTracker
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.solver.common.big_cube.NxNEdgesCommon import NxNEdgesCommon
from cube.domain.solver.protocols import SolverElementsProvider


class NxNEdges(SolverHelper):
    """Public facade for NxN edge pairing. Delegates all logic to NxNEdgesCommon.

    This class exists to preserve the public API used by solvers:
      - CageNxNSolver, BeginnerReducer use solve() and do_even_full_edge_parity_on_any_edge()
      - DirectLayerByLayerNxNSolver, _LBLL3Edges use solve_face_edges()
    """

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
        return self._edges_common.solve_face_edges(face_tracker)

    def do_even_full_edge_parity_on_any_edge(self) -> None:
        self._edges_common.do_even_full_edge_parity_on_any_edge()
