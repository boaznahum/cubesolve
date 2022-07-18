from cube.model import Part
from cube.solver.common.base_solver import BaseSolver
from cube.solver.common.solver_element import StepSolver


def use(_):
    pass


_status = None


class PLL(StepSolver):

    def __init__(self, slv: BaseSolver) -> None:
        super().__init__(slv)
        self._set_debug_prefix("PLL")

    @property
    def is_solved(self):
        return Part.all_in_position(self.yellow_face.parts)

    def is_rotate_and_solved(self):
        """
        Can be solved only by rotate
        :return:
        """
        return self.cqr.rotate_face_and_check(self.yellow_face, lambda :self.is_solved) >= 0


    def solve(self):

        if self.is_solved():
            return  # avoid rotating cube

        with self.ann.annotate(h1="PLL"):
            self._solve()

    def _solve(self):

        # maybe need only rotation

        rotate_alg = self.cqr.rotate_face_and_check_get_alg(self.cmn.white_face.opposite, self.is_solved)

        if rotate_alg:
            self.play(rotate_alg)
            return  # done

        # we assume we have a cross
        self.cmn.bring_face_up(self.white_face.opposite)

        self._do_pll()

        assert self.is_solved()

    def _do_pll(self):
        pass

