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

    @property
    def is_solved(self) -> bool:
        """

        :return: true if all edges matches ignoring cross orientation.
        so you must call solve even if this return true
        """

        yf: Face = self.white_face.opposite

        return all(p.match_face(yf) for p in yf.parts)

    def is_rotate_and_solved(self):
        """
        Can be solved only by rotate
        :return:
        """
        return self.cqr.rotate_face_and_check(self.yellow_face, lambda: self.is_solved) >= 0

    def solve(self):

        if self.is_solved:
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
        description = ""
        for r in range(4):
            state = self._encode_state()
            self.debug(f"Found state after {r} rotations:\n{state}")

            description_alg: tuple[str, Alg] | None = self._get_state_alg(state)

            if description_alg is not None:
                description, alg = description_alg
                break  # found

            if r == 3:
                break  # don't rotate again, we failed to found

            self.play(Algs.U)

        if alg is None:
            raise InternalSWError(f"Unknown state {state}")

        self.debug(f"Found OLL alg '{description}' {alg}")

        self.play(alg)

        assert self.is_solved

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

    def _get_state_alg(self, state: str) -> Optional[Tuple[str, Alg]]:

        d_alg = self._get_state_alg_raw(state)

        if not d_alg:
            return None

        alg = d_alg[1]
        description = d_alg[0]
        self.debug(f"Found (raw) alg: {description} : {alg}")

        if isinstance(alg, str):
            alg = Algs.parse(alg)

        return description, alg

    def _get_state_alg_raw(self, state: str) -> Optional[Tuple[str, Alg | str]]:
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

        #################### Cross
        match state:
            case "xy--x" "--y-y" "-yyy-" "y-yy-" "x---x":
                return "Cross", "R' U2 (R U R' U) R"

        #################### 4 corners
        match state:
            case "x-y-x" "-y-y-" "-yy-y" "-yyy-" "x---x":
                return "4 Corners", "M' U' M U2' M' U' M"

            #################### "Shape L"
            # match state:
            case "x---x" "y-yy-" "y-yy-" "----y" "xyy-x":
                return "Shape L", "r U 2 R' U' R U' r'"

        return None

    def _algs_db(self):

        """
        Credits: https://cubingcheatsheet.com/algs3x_oll.html


        encoding
           "l1l2l3"  "u1u2u2"  "r1r2r3" "f1f2f3"

               u1  u2  u3
           l3             r1
           l2      Y      r2
           l1             r3
               d3  d2  d1

        All are clockwise, so they can be rotated if needed

        Example:  27 Sune

           "---" "y--" "y--" "y--"

               Y   --  --
           --      Y      Y
           --  Y   Y  Y   --
           --  Y   Y      --
               --  --  Y

        Whitespaces are ignored.


        :return:
        """



        res: list[Tuple[str, str, str]] = [

            #Cross
            ("--- y-- y-- y--", "27 SUNE", "(R U R' U) (R U2 R')"),

            ("--y --y --- --y", "26 Anti Sune", "(L' U' L U') (L' U2 L)"),
            ("--- y-y --- y-y", "21 H", "F (R U R' U') (R U R' U') (R U R' U') F'"),
            ("y-y --y --- y---", "22 Pi", "R U2 (R2' U' R2 U') (R2' U2 R)"),
            ("--- --- --- y-y", "23 HEADLIGHTS", "R2 D (R' U2 R) D' (R' U2 R')"),
            ("--- y--- --- --y", "24 T", "(r U R' U') (r' F R F')"),
            ("--y --- --- y---", "25 Bowtie", "F' (r U R' U') (r' F R)"),

            # T
            ("--- yy- --- -yy", "33 SHOELACES", "(R U R' U') (R' F R F')"),
            ("y-y -y- --- -y-", "45 Suit Up", "F (R U R' U') F'"),

            # Square
            ("yy- yy- y-- ---", "05 LEFTY SQUARE", "r' U2 (R U R' U) r"),
            ("-yy --- --y -yy", "6 Righty Square", "r U2 (R' U' R U') r'"),

            # C
            ("--y -y- y-- -y-", "34 City", "(R U R2' U') (R' F R U) R U' F'"),
            ("-y- --- yyy ---", "46 Seein' Headlights", "R' U' (R' F R F') U R"),

            # W
            ("--- -y- yy- --y", "36 WARIO", "(R' U' R U') (R' U R U) l U' R' U x"),
            ("--- y--- -yy -y-", "38 MARIO", "(R U R' U) (R U' R' U') (R' F R F')"),
            # Corners
            ("--- --- -y- -y-", "28 Stealth", "(r U R' U') M (U R U' R')"),
            ("--- -y- --- -y-", "57 Mummy", "(R U R' U') M' (U R U' r')"),

            # P
            ("-y- y-- --- -yy", "31 Couch", "(R' U' F) (U R U' R') F' R"),
            ("-y- yy- --- --y", "32 Anti Couch", "S (R U R' U') (R' F R f')"),
            ("--- -y- yyy ---", "43 Anti P", "f' (L' U' L U) f"),
            ("yyy -y- --- ---", "44 P", "f (R U R' U') f'"),
            # I
            ("y-y -yy --- yy-", "51 Bottlecap", "f (R U R' U') (R U R' U') f'"),
            ("y-y -y- y-y -y-", "56 Streetlights", "F (R U R' U') R F' (r U R' U') r'"),
            ("-y- y-- yyy --y", "52 Rice Cooker", "(R U R' U) R d' R U' R' F'"),
            ("yyy --- yyy ---", "55 HIGHWAY", "y (R' F R U) (R U' R2' F') R2 U' R' (U R U R')"),
            # Fish
            ("--y --y -y- -yy", "9 Kite", "(R U R' U') R' F (R2 U R' U') F'"),
            ("y-- yy- -y- y--", "10 ANTI KITE", "(R U R' U) (R' F R F') (R U2' R')"),
            ("-y- -y- y-- --y", "35 Fish Salad", "(R U2 R') (R' F R F') (R U2 R')"),
            ("--- --- yy- -yy", "37 Mounted Fish", "F (R U' R' U') (R U R') F'"),
            # L Big
            ("", "13 Gun", "F (U R U' R2) F' (R U R U') R'"),
            ("", "14 Anti Gun", "(R' F R) U (R' F' R) y' (R U' R')"),
            ("", "15 SQUEEGEE", "(r' U' r) (R' U' R U) (r' U r)"),
            ("16 ANTI SQUEEGEE", "(r U r') (R U R' U') (r U' r')"),

            # L
            ("", "48 Breakneck", "F (R U R' U') (R U R' U') F'"),
            ("","47 Anti Breakneck", "F' (L' U' L U) (L' U' L U) F"),
            ("", "49 Right Back Squeezy", "r U' r2' U r2 U r2' U' r"),
            ("", "50 Right Front Squeezy", "r' U r2 U' r2' U' r2 U r'"),
            ("", "53 Frying Pan", "(r' U' R U') (R' U R U') R' U2 r"),
            ("", "54 Anti Frying Pan", "(r U R' U) (R U' R' U) R U2' r'"),
            # Y
            ("", "29 Spotted Chameleon", "y (R U R' U') (R U' R') (F' U' F) (R U R')"),
            ("", "30 Anti Spotted Chameleon", "y' F U (R U2 R' U') (R U2 R' U') F'"),
            ("", "41 Awkward Fish", "(R U R' U) (R U2' R') F (R U R' U') F'"),
            ("", "42 Lefty Awkward Fish", "(R' U' R U') (R' U2 R) F (R U R' U') F'"),
            # Z
            ("", "7 Lightning", "(r U R' U) R U2 r'"),
            ("", "8 Reverse Lightning", "(r' U' R U') R' U2 r"),
            ("", "11 Downstairs", "r' (R2 U R' U R U2 R') U M'"),
            ("", "12 Upstairs", "M' (R' U' R U' R' U2 R) U' M"),
            ("", "40 Anti Fung", "R' F (R U R' U') F' U R"),
            ("", "39 FUNG", "L F' (L' U' L U) F U' L'"),
            # Dot
            ("", "01 RUNWAY", "(R U2 R') (R' F R F') U2 (R' F R F')"),
            ("", "02 ZAMBONI", "F (R U R' U') F' f (R U R' U') f'"),
            ("", "03 ANTI NAZI", "f (R U R' U') f' U' F (R U R' U') F'"),
            ("", "04 NAZI", "f (R U R' U') f' U F (R U R' U') F'"),
            ("", "18 Crown", "(r U R' U) (R U2 r') (r' U' R U') (R' U2 r)"),
            ("", "19 BUNNY", "M U (R U R' U') M' (R' F R F')"),
            ("", "17 SLASH", "(R U R' U) (R' F R F') U2' (R' F R F')"),
            ("", "20 X", "M U (R U R' U') M2' (U R U' r')")

        ]
