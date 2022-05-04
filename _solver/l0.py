from _solver.base_solver import SolverElement, ISolver
from algs import Algs
from elements import Color, Face, FaceName


class L0(SolverElement):
    __slots__ = ["_start_color"]

    def __init__(self, slv: ISolver) -> None:
        super().__init__(slv)

        self._start_color = Color.WHITE

    @property
    def _white(self):
        """
        when ever we say 'white' we mean color of start color
        """
        return self._start_color

    @property
    def _white_face(self) -> Face:
        w: Color = self._white

        f: Face = self.cube.color_2_face(w)

        self.debug(w, " is on ", f)

        return f

    def is_l0_cross(self) -> bool:
        """
        :return: true if there is 'white' cross
        """

        wf: Face = self._white_face
        es = wf.edges

        for e in es:
            if not e.match_faces:
                return False

        return True

    def solve_l0_cross(self):
        self._bring_white_up()




    def _bring_white_up(self):

        # 1 bring white face up
        w: Face = self._white_face

        if w.name != FaceName.U:

            self.debug("Need to Binging ", w, 'to', FaceName.U)

            match w.name:

                case FaceName.F:
                    self.op.op(Algs.X)

                case FaceName.B:
                    self.op.op(-Algs.X)

                case FaceName.D:
                    self.op.op(Algs.X * 2)

                case FaceName.L:
                    self.op.op(Algs.Y + Algs.X)

                case FaceName.R:
                    self.op.op(-Algs.Y + Algs.X)
