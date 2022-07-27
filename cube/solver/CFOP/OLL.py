import re
from typing import Tuple, Optional

from cube.algs import Alg, Algs
from cube.app_exceptions import InternalSWError
from cube.model import FaceName, Part
from cube.model.cube_face import Face
from cube.solver.common.advanced_even_oll_big_cube_parity import AdvancedEdgeEdgeParity
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
        self._oll_parity = AdvancedEdgeEdgeParity(slv)

        self._algs_db: list[Tuple[str, str, str]] = []

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

        if self._check_and_do_oll_edge_parity():
            if self.is_solved:
                # in some rare cases, after OLL parity, OLL is solved, and this is a state we don't know to detect
                return

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

            # if r == 3:
            #     break  # don't rotate again, we failed to found

            self.play(Algs.Y)

        if alg is None:
            raise InternalSWError(f"Unknown OLL state:\n {state}")

        self.debug(f"Found OLL alg '{description}' {alg}")

        self.play(alg)

        assert self.is_solved

    def _check_and_do_oll_edge_parity(self) -> bool:
        """
        Assume 'yellow' on top
        :return:
        """

        up = self.cube.up
        n_edges = sum(e.match_face(up) for e in up.edges)

        if n_edges not in [0, 2, 4]:
            if self.cube.n_slices % 2 == 0:
                self.debug(f"Found OLL(Edge Parity)")
                self._oll_parity.do_full_even_edge_parity()
                return True
            else:
                # on odd cube it should be soled by edges
                raise InternalSWError("Edge parity on odd cube")

        return False

    def _encode_state(self) -> str:

        """
                encoding
           "l1l2l3"  "b1b2b3"  "r1r2r3" "f1f2f3"

               b1  b2  b3
           l3             r1
           l2      Y      r2
           l1             r3
               f3  f2  f1

        All are clockwise, so they can be rotated if needed

        Example:  27 Sune

           "---" "y--" "y--" "y--"

               Y   --  --
           --      Y      Y
           --  Y   Y  Y   --
           --  Y   Y      --
               --  --  Y

        :return:
        """

        cube = self.cube
        c = cube
        back = c.back
        right = c.right
        left = c.left
        front = c.front
        yellow = c.up.color

        def e(face: Face, *parts: Part):
            s = ""

            for p in parts:
                if p.get_face_edge(face).color == yellow:
                    s += "y"
                else:
                    s += "-"

            return s

        s1 = e(left, left.corner_top_right, left.edge_top, left.corner_top_left)
        s2 = e(back, back.corner_top_right, back.edge_top, back.corner_top_left)
        s3 = e(right, right.corner_top_right, right.edge_top, right.corner_top_left)
        s4 = e(front, front.corner_top_right, front.edge_top, front.corner_top_left)

        return "\n".join([s1, s2, s3, s4])

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

        dbs: list[tuple[str, str, str]] = self._get_algs_db()

        for d in dbs:

            st0 = d[0]

            st = re.sub(r'\s+', "", st0)
            st = st.lower()

            assert len(st) == 12, str((st0, d[1]))
            assert st.count("y") + st.count("-") == 12, str((st0, d[1]))

            if st == state:
                return d[1], d[2]

        return None

    def _get_algs_db(self) -> list[Tuple[str, str, str]]:

        """
        Credits: https://cubingcheatsheet.com/algs3x_oll.html


        encoding
           "l1l2l3"  "b1b2b2"  "r1r2r3" "f1f2f3"

               b1  b2  b3
           l3             r1
           l2      Y      r2
           l1             r3
               f3  f2  f1

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

        if self._algs_db:
            return self._algs_db

        self._algs_db = [

            # Cross
            ("--- y-- y-- y--", "27 SUNE", "(R U R' U) (R U2 R')"),

            ("--y --y --- --y", "26 Anti Sune", "(L' U' L U') (L' U2 L)"),
            ("--- y-y --- y-y", "21 H", "F (R U R' U') (R U R' U') (R U R' U') F'"),
            ("y-y --y --- y--", "22 Pi", "R U2 (R2' U' R2 U') (R2' U2 R)"),
            ("--- --- --- y-y", "23 HEADLIGHTS", "R2 D (R' U2 R) D' (R' U2 R')"),
            ("--- y-- --- --y", "24 T", "(r U R' U') (r' F R F')"),
            ("--y --- --- y--", "25 Bowtie", "F' (r U R' U') (r' F R)"),

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
            ("--- y-- -yy -y-", "38 MARIO", "(R U R' U) (R U' R' U') (R' F R F')"),
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
            ("--- yy- y-- yy-", "13 Gun", "F (U R U' R2) F' (R U R U') R'"),
            ("--y -yy --- -yy", "14 Anti Gun", "(R' F R) U (R' F' R) y' (R U' R')"),
            ("y-- yy- y-- -y-", "15 SQUEEGEE", "(r' U' r) (R' U' R U) (r' U r)"),
            ("--y -y- --y -yy", "16 ANTI SQUEEGEE", "(r U r') (R U R' U') (r U' r')"),

            # L
            ("y-y --y -y- yy-", "48 Breakneck", "F (R U R' U') (R U R' U') F'"),
            ("-y- y-- y-y -yy", "47 Anti Breakneck", "F' (L' U' L U) (L' U' L U) F"),
            ("yyy --y --- yy-", "49 Right Back Squeezy", "r U' r2' U r2 U r2' U' r"),
            ("yyy -yy --- y--", "50 Right Front Squeezy", "r' U r2 U' r2' U' r2 U r'"),
            ("yyy -y- y-y ---", "53 Frying Pan", "(r' U' R U') (R' U R U') R' U2 r"),
            ("yyy --- y-y -y-", "54 Anti Frying Pan", "(r U R' U) (R U' R' U) R U2' r'"),
            # Y
            ("y-- -y- -yy ---", "29 Spotted Chameleon", "y (R U R' U') (R U' R') (F' U' F) (R U R')"),
            ("-y- --y --- yy-", "30 Anti Spotted Chameleon", "y' F U (R U2 R' U') (R U2 R' U') F'"),
            ("--- y-y -y- -y-", "41 Awkward Fish", "(R U R' U) (R U2' R') F (R U R' U') F'"),
            ("--- -y- -y- y-y", "42 Lefty Awkward Fish", "(R' U' R U') (R' U2 R) F (R U R' U') F'"),
            # Z
            ("--- y-- yy- yy-", "7 Lightning", "(r U R' U) R U2 r'"),
            ("--- -yy -yy --y", "8 Reverse Lightning", "(r' U' R U') R' U2 r"),
            ("-y- yy- y-- y--", "11 Downstairs", "r' (R2 U R' U R U2 R') U M'"),
            ("-y- --y --y -yy", "12 Upstairs", "M' (R' U' R U' R' U2 R) U' M"),
            ("y-- -yy --- -y-", "40 Anti Fung", "R' F (R U R' U') F' U R"),
            ("--- yy- --y -y-", "39 FUNG", "L F' (L' U' L U) F U' L'"),
            # Dot
            ("yyy -y- yyy -y-", "01 RUNWAY", "(R U2 R') (R' F R F') U2 (R' F R F')"),
            ("yyy -yy -y- yy-", "02 ZAMBONI", "F (R U R' U') F' f (R U R' U') f'"),
            ("yy- yy- yy- -y-", "03 ANTI NAZI", "f (R U R' U') f' U' F (R U R' U') F'"),
            ("-yy -y- -yy -yy", "04 NAZI", "f (R U R' U') f' U F (R U R' U') F'"),
            ("-y- -y- -y- yyy", "18 Crown", "(r U R' U) (R U2 r') (r' U' R U') (R' U2 r)"),
            ("yy- -y- -yy -y-", "19 BUNNY", "M U (R U R' U') M' (R' F R F')"),
            ("yy- -yy -y- -y-", "17 SLASH", "(R U R' U) (R' F R F') U2' (R' F R F')"),
            ("-y- -y- -y- -y-", "20 X", "M U (R U R' U') M2' (U R U' r')")

        ]

        return self._algs_db
