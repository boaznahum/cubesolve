from typing import Tuple, Optional

from cube.algs import Alg, Algs
from cube.app_exceptions import InternalSWError
from cube.model import FaceName, Part
from cube.model.cube_face import Face
from cube.solver.common.advanced_even_oll_big_cube_parity import AdvancedEvenEdgeFullEdgeParity
from cube.solver.common.base_solver import BaseSolver
from cube.solver.common.solver_element import StepSolver


def use(_):
    pass


_status = None

_algs: dict[str, Alg | str] = {}


class OLL(StepSolver):
    """
    Credits to https://ruwix.com/the-rubiks-cube/advanced-cfop-fridrich/orient-the-last-layer-oll/
    """

    def __init__(self, slv: BaseSolver) -> None:
        super().__init__(slv)
        self._set_debug_prefix("OLL")
        self._oll_parity = AdvancedEvenEdgeFullEdgeParity(slv)

    def is_solved(self) -> bool:
        """

        :return: true if all edges matches ignoring cross orientation.
        so you must call solve even if this return true
        """

        yf: Face = self.white_face.opposite

        return all(p.match_face(yf) for p in yf.parts)

    def solve(self):

        if self.is_solved():
            return

        # quick without rotating cube:

        with self.ann.annotate(h1="Doing OLL"):
            self._solve()

    def _solve(self):
        # 'yellow' face
        yf: Face = self.white_face.opposite

        self.cmn.bring_face_up(yf)
        # yf is no longer valid - need to track
        assert self.white_face.opposite.name == FaceName.U

        self._check_and_do_oll_edge_parity()

        self._do_oll()

    def _do_oll(self):

        state: str = ""
        alg: Alg | None = None
        for r in range(4):
            state = self._encode_state()
            self.debug(f"Found state after {r} rotations:\n{state}")

            alg = self._get_state_alg(state)

            if alg is not None:
                break

            if r == 3:
                break  # don't rotate again

            self.play(Algs.U)

        if alg is None:
            raise InternalSWError(f"Unknown state {state}")

        self.play(alg)

        assert self.is_solved()

    def _check_and_do_oll_edge_parity(self):
        """
        Assume 'yellow' on top
        :return:
        """

        up = self.cube.up
        n_edges = sum(e.match_face(up) for e in up.edges)

        if n_edges not in [0, 2, 4]:
            if self.cube.n_slices % 2 == 0:
                self.debug(f"Found OLL(Edge Parity)")
                self._oll_parity.solve()
            else:
                # on odd cube it should be soled by edges
                raise InternalSWError("Edge parity on odd cube")

    def _encode_state(self) -> str:
        # noinspection SpellCheckingInspection
        """
        For Y/y for Yellow facet

        xyyyx  --> Back face
        yYYYy
        yYYYy  ---> Up
        yYYYy
        xyyyx  ---> Front Face

        :return:
        """

        cube = self.cube
        c = cube
        up = c.up
        back = c.back
        right = c.right
        left = c.left
        front = c.front
        yellow = up.color

        def e(face: Face, *parts: Part):
            s = ""

            for p in parts:
                if p.get_face_edge(face).color == yellow:
                    s += "y"
                else:
                    s += "-"

            return s

        top_left = up.corner_top_left
        top_right = up.corner_top_right
        bottom_left = up.corner_bottom_left
        bottom_right = up.corner_bottom_right
        e_top = up.edge_top
        e_left = up.edge_left
        e_right = up.edge_right
        e_bottom = up.edge_bottom
        s1 = "x" + e(back, top_left, e_top, top_right) + "x"
        s2 = e(left, top_left) + e(up, top_left, e_top, top_right) + e(right, top_right)
        s3 = e(left, e_left) + e(up, e_left, up.center, e_right) + e(right, e_right)
        s4 = e(left, bottom_left) + e(up, bottom_left, e_bottom, bottom_right) + e(right, bottom_right)
        s5 = "x" + e(front, bottom_left, e_bottom, bottom_right) + "x"

        return "\n".join([s1, s2, s3, s4, s5])

    def _get_state_alg(self, state: str) -> Alg | None:

        d_alg = self._get_state_alg_raw(state)

        if not d_alg:
            return None

        alg = d_alg[1]
        self.debug(f"Found alg: {d_alg[0]} : {alg}")

        if isinstance(alg, str):
            alg = Algs.parse(alg)
        return alg

    def _get_state_alg_raw(self, state: str) -> Optional[Tuple[str, Alg|str]]:
        """

        Credits to https://ruwix.com/the-rubiks-cube/advanced-cfop-fridrich/orient-the-last-layer-oll/

        Why case ond not dictionary ? Se we can check coverage
        :param state:
        :return:
        """


        # normalize it to my form
        state2 = state.strip().replace("\n", ", ")
        state = state.strip().replace("\n", "")
        self.debug(f"Comparing state:{state2}")

        #################### 4 corners
        match state:
            case "x-y-x" "-y-y-" "-yy-y" "-yyy-" "x---x":
                return "4 Corners", "M' U' M U2' M' U' M"

        #################### "Shape L"
            # match state:
            case "x---x" "y-yy-" "y-yy-" "----y" "xyy-x":
                return "Shape L", "r U2 R' U' R U' r'"

        return None
