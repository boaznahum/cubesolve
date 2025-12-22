from cube.domain.algs import Algs
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.SolverElement import SolverElement
from cube.domain.solver.protocols import SolverElementsProvider


class AdvancedEdgeEdgeParity(SolverElement):

    def __init__(self, solver: SolverElementsProvider) -> None:
        super().__init__(solver)

    def do_full_even_edge_parity(self):
        """
        Do a full even parity on FU edge

        """
        cube = self.cube

        # https://cubingcheatsheet.com/algs6x.html
        # 2-3Rw' U2 2-3Lw F2 2-3Lw' F2 2-3Rw2 U2 2-3Rw U2 2-3Rw' U2 F2 2-3Rw2 F2

        Rw = Algs.R[2:cube.size//2]  # on 4x4 R[2:2], on 6x6 R[2:3]
        Lw = Algs.L[2:cube.size//2]  # on 4x4 R[2:2], on 6x6 R[2:3]
        F2 = Algs.F * 2
        U2 = Algs.U * 2

        with self.annotate((cube.fu, AnnWhat.Moved), h2="Doing OLL even full edge parity"):

            alg = Rw.p +  U2 + Lw + F2 + Lw.p + F2 + Rw*2 + U2 + Rw + U2 + Rw.p + U2 + F2 + Rw*2  + F2

            self.op.play(alg)





