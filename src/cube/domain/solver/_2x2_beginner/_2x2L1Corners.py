from cube.domain.algs import Algs, Alg, WholeCubeAlg
from cube.domain.exceptions import InternalSWError
from cube.domain.geometric.Face2FaceTranslator import Face2FaceTranslator
from cube.domain.model import Corner, PartColorsID, Color
from cube.domain.model.Face import Face
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.solver.protocols import SolverElementsProvider


def _cid(colors: PartColorsID) -> str:
    """Format a corner colors_id as short color names, e.g. 'Wh,Bl,Re'."""
    return ",".join(c.value for c in colors)


class _2x2L1Corners(SolverHelper):
    """Layer 1 corner solver for 2x2 cubes (beginner method).

    IMPORTANT — No face colors:
        A 2x2 cube has no center pieces, so faces have no inherent color.
        This solver must NEVER access ``Face.color``, ``self.white_face``,
        ``cube.color_2_face()``, or any other API that reads face colors
        (even through a ``FacesColorsProvider``).

        Instead, the solver works entirely with *corner sticker colors*
        (``Part.face_color``, ``Part.is_face_color``, ``Part.colors_id``)
        and the configured start color (``self.cmn.white``).

        The caller (``_L1``) sets up a ``FacesColorsProvider`` for its own
        bookkeeping, but this class does not rely on it.
    """

    __slots__: list[str] = []

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv, "_2x2L1Corners")


    def is_corners(self) -> bool:
        """Check if Layer 1 corners are solved.

        Checks directly — no U rotations or cube moves needed:
        1. All 4 top-layer corners have white facing up
        2. Adjacent corners share the same side color
        """

        white_color: Color = self.cmn.white
        cube = self.cube
        up: Face = cube.up

        # All 4 corners on up face must have white facing up
        if not all(c.face_color(up) == white_color
                   for c in [cube.flu, cube.fru, cube.bru, cube.blu]):
            return False

        # Adjacent corners must share side colors
        return (cube.flu.face_color(cube.front) == cube.fru.face_color(cube.front)
                and cube.fru.face_color(cube.right) == cube.bru.face_color(cube.right)
                and cube.bru.face_color(cube.back) == cube.blu.face_color(cube.back)
                and cube.blu.face_color(cube.left) == cube.flu.face_color(cube.left))


    def solve(self) -> None:
        """Solve Layer 1 corners using the beginner method."""

        if self.is_corners():
            return

        with self.ann.annotate(h1="Doing L1 Corners"):
            self._do_corners()

    def _do_corners(self) -> None:
        """Solve all four L1 corners using a reference-corner approach.

        Algorithm:
          1. Find the face with the most white stickers facing it (prefer up).
          2. Bring that face to up via whole-cube rotation.
          3. Pick a corner on up that already has white facing up as reference.
          4. U-rotate the reference corner to FLU.
          5. Fix FRU three times, rotating U between fixes.
        """

        white_color: Color = self.cmn.white
        cube = self.cube

        with self._logger.tab(lambda: f"Doing L1 {white_color} Corners"):

            # Step 1: Find face with most white stickers facing it
            best_face: Face = self._find_best_white_face(white_color)

            # Step 2: Bring to up if not already
            if best_face is not cube.up:
                with self._logger.tab(lambda: f"Bringing {best_face} to up"):
                    result: list[tuple[WholeCubeAlg, int, Alg]] = \
                        Face2FaceTranslator.derive_whole_cube_alg_source_to_target(
                            cube.layout, best_face.name, cube.up.name)
                    assert result
                    self.op.play(result[0][2].simplify())

            # Step 3: Pick reference corner — one already on up with white facing up
            ref_corner: Corner = self._find_reference_corner_on_up(white_color)
            ref_id: PartColorsID = ref_corner.colors_id

            # Step 4: Bring reference to FLU (just U rotation)
            with self._logger.tab(lambda: f"Reference {_cid(ref_id)} to FLU"):
                self._u_rotate_corner_to_flu(ref_corner)

            # Step 5: Fix FRU 3 times with U between
            for _ in range(2):
                self._solve_fru_corner(white_color)
                self.op.play(Algs.U)

            # third time
            self._solve_fru_corner(white_color)

    def _find_best_white_face(self, white_color: Color) -> Face:
        """Find the face with the most corners having white facing it.

        On ties, prefers the current up face (avoids whole-cube rotation).
        """
        cube = self.cube
        best_face: Face = cube.up
        best_count: int = 0

        for face in cube.faces:
            corners: list[Corner] = [face.corner_top_left, face.corner_top_right,
                                     face.corner_bottom_left, face.corner_bottom_right]
            count: int = sum(1 for c in corners if c.face_color(face) == white_color)
            # Prefer up face on ties (no rotation needed)
            if count > best_count or (count == best_count and face is cube.up):
                best_count = count
                best_face = face

        return best_face

    def _find_reference_corner_on_up(self, white_color: Color) -> Corner:
        """Find a corner on up face with white facing up."""
        up: Face = self.cube.up
        for corner in [up.corner_bottom_left, up.corner_bottom_right,
                       up.corner_top_left, up.corner_top_right]:
            if corner.face_color(up) == white_color:
                return corner
        raise InternalSWError("No corner with white facing up after face selection")

    def _u_rotate_corner_to_flu(self, corner: Corner) -> None:
        """Bring a corner on the up face to FLU with just a U rotation."""
        cube = self.cube
        if corner is cube.flu:
            pass
        elif corner is cube.fru:
            self.op.play(Algs.U)
        elif corner is cube.bru:
            self.op.play(Algs.U * 2)
        elif corner is cube.blu:
            self.op.play(Algs.U.prime)
        else:
            raise InternalSWError(f"Corner {corner} not on up face")

    def _is_fru_solved(self, white_color: Color) -> bool:
        """Check whether the FRU corner is correctly solved relative to the FLU reference.

        Determines the expected FRU corner by reading the front-face color from
        FLU, then finds the corner that has both white and front colors (but not
        the third FLU color). Returns True only if that corner is at FRU with
        the correct color orientation.

        Returns False early if FLU doesn't have exactly 3 distinct colors
        (e.g. during initial positioning before the reference corner is set).
        """

        cube = self.cube
        front = cube.front
        front_color: Color = cube.flu.face_color(front)
        flu_other_color_set = self.cube.flu.colors_id - {white_color, front_color}


        if len(flu_other_color_set) > 1:
            return False

        assert len(flu_other_color_set) == 1

        flu_other_color = next(iter(flu_other_color_set))

        def is_fru_target(c: Corner) -> bool:
            cid = c.colors_id
            return white_color in cid and front_color in cid and flu_other_color not in cid

        source_corner: Corner = self.cube.cqr.find_corner(is_fru_target)

        if source_corner is not cube.fru:
            return False

        if source_corner.face_color(front) != front_color:
            return False

        if source_corner.face_color(cube.up) != white_color:
            return False

        return True




    def _solve_fru_corner(self, white_color: Color) -> None:
        """Solve the FRU corner while preserving the FLU reference corner.

        Identifies which corner belongs at FRU by reading the front-face color
        from the FLU reference corner, then finding the corner with white and
        front colors (excluding the third FLU color).

        Moves the target corner to FRD (bringing it down from top if needed),
        then applies one of two insertion algorithms depending on whether white
        faces front or right. If white faces down, an extra setup move flips it
        to a side face first.
        """

        if self._is_fru_solved(white_color):
            return

        # find the right corner
        front_color: Color = self.cube.flu.face_color(self.cube.front)
        flu_other_color_set = self.cube.flu.colors_id - { white_color , front_color}
        assert len(flu_other_color_set) == 1
        flu_other_color = next(iter(flu_other_color_set))

        def is_fru_target(c: Corner) -> bool:
            cid = c.colors_id
            return white_color in cid and front_color in cid and flu_other_color not in cid

        source_corner: Corner = self.cube.cqr.find_corner(is_fru_target)

        # no faces so we cannot check for match

        source_corner_id: PartColorsID = source_corner.colors_id

        with self.ann.annotate(
                (source_corner_id, AnnWhat.Moved), (self.cube.fru, AnnWhat.FixedPosition),
                h2=lambda: f"Bringing {_cid(source_corner_id)} to FRU"
        ), self._logger.tab(lambda : f"Solving FRU <-- {_cid(source_corner_id)}"):


            _source_corner: Corner | None = None

            # source corner
            def sc() -> Corner:
                nonlocal _source_corner
                if not _source_corner or _source_corner.colors_id != source_corner_id:
                    _source_corner = self.cube.find_corner_by_colors(source_corner_id)
                assert _source_corner
                return _source_corner

            wf: Face = self.cube.up


            # now bring source cornet into under it  FRD

            if sc().on_face(wf):
                self.debug(f"LO-Corners C1. source {sc()} is on top")
                self._bring_top_corner_to_f_r_d(sc())
            else:
                self.debug(f"LO-Corners C2. source {sc()} is on bottom")
                self._bring_bottom_corner_to_f_r_d(sc())

            # Now source is on FRD
            assert self.cube.frd is sc()

            # is the white is on the down
            if sc().face_color(wf.opposite) == white_color:
                self.debug(f"{white_color} is on bottom")
                self.op.play(Algs.R.prime + Algs.D.prime * 2 + Algs.R + Algs.D)
                assert self.cube.front.corner_bottom_right is sc()
                assert sc().face_color(wf.opposite) != white_color

            if sc().face_color(wf.cube.front) == white_color:
                self.op.play(Algs.D.prime + Algs.R.prime + Algs.D + Algs.R)
            else:
                self.op.play(Algs.D + Algs.F + Algs.D.prime + Algs.F.prime)

            assert self._is_fru_solved(white_color)

    def _bring_top_corner_to_f_r_d(self, c: Corner) -> None:
        """Bring a top-layer corner down to FRD.

        Preserves top layer (except FRU slot).
        Doesn't preserve bottom layer.
        """

        wf: Face = self.cube.up
        assert c.on_face(wf)

        saved_id = c.colors_id

        if wf.corner_bottom_right is c:
            self.op.play(-Algs.R + -Algs.D + Algs.R)

        elif wf.corner_top_right is c:
            self.op.play(-Algs.B + -Algs.D + Algs.B)

        elif wf.corner_top_left is c:
            self.op.play(Algs.B + -Algs.D + - Algs.B)

        elif wf.corner_bottom_left is c:
            self.op.play(-Algs.F + -Algs.D + Algs.F)

        else:
            raise ValueError(f"{c} is not on {wf}")

        c = self.cube.find_corner_by_colors(saved_id)
        # now it is on bottom
        self._bring_bottom_corner_to_f_r_d(c)

    def _bring_bottom_corner_to_f_r_d(self, c: Corner) -> None:
        """Bring a bottom-layer corner to FRD via D rotations.

        Doesn't preserve bottom layer.
        """

        f: Face = self.cube.down
        assert c.on_face(f)

        if f.corner_top_right is c:
            pass  # nothing to do

        elif f.corner_bottom_right is c:
            self.op.play(-Algs.D)

        elif f.corner_bottom_left is c:
            self.op.play(-Algs.D * 2)

        elif f.corner_top_left is c:
            self.op.play(Algs.D)

        else:
            raise ValueError(f"{c} is not on {f}")
