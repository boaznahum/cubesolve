# claude document this class
from cube.domain.model.Cube import Cube
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.tracker.FacesTrackerHolder import FacesTrackerHolder
from cube.domain.solver.protocols import SolverElementsProvider


class ShadowCubeHelper(SolverHelper):
    def __init__(self, slv: SolverElementsProvider):
        super().__init__(slv, "ShadowCubeHelper")

    def create_shadow_cube_from_faces_and_cube(self, th: FacesTrackerHolder) -> Cube:
        """

        @:param this is the source folder usually big cube
        claude: fix this it was copied from cage, but it conatis too much

        Create shadow 3x3 and solve using DualOperator.

        DualOperator wraps both the shadow cube and real operator:
        - Solver logic operates on shadow cube (op.cube returns shadow)
        - Moves are played on BOTH cubes (shadow direct, real via operator)
        - Annotations are mapped from shadow pieces to real pieces
        - User sees full animation with h1/h2/h3 text and visual markers!

        This replaces the old approach of collecting history and playing at once.
        """
        from cube.domain.model.Cube import Cube

        # Create shadow 3x3 cube
        shadow_cube = Cube(size=3, sp=self.cube.sp)
        shadow_cube.is_even_cube_shadow = self.cube.is_even
        self._copy_state_to_shadow(shadow_cube, th)

        assert shadow_cube.match_original_scheme, f"Shadow cube must match color scheme, face_colors={th.get_face_colors()}"

        assert shadow_cube.is_sanity(force_check=True), "Shadow cube invalid before solving"


        return shadow_cube

    def _copy_state_to_shadow(
        self,
        shadow: "Cube",
        th: FacesTrackerHolder,
        fix_non_3x3_edges: bool = True
    ) -> None:
        """Copy corner/edge state from big cube to shadow 3x3.

        For even cubes during L1 solving, some edges may be non-3x3 (scrambled).
        These can be replaced with valid reference colors to pass sanity checks.
        Odd cubes don't need this fix - their edges are always 3x3-valid.

        Args:
            shadow: The shadow 3x3 cube to populate.
            th: Face tracker holder providing face→color mapping.
            fix_non_3x3_edges: If True, replace non-3x3 edges with valid reference
                colors for even cubes. Should always be True for production use,
                but can be False for testing/debugging.
        """
        # Step 1: Get colors from even cube as 3x3 snapshot
        # NOTE: This uses POSITION-based keys (F, L, U, R, D, B) which may not
        # match reference layout after rotations
        colors_3x3 = self._cube.get_3x3_colors()

        # Step 2: Override centers with face_colors mapping from trackers
        modified = colors_3x3.with_centers(th.get_face_colors())

        # Step 3: For even cubes, fix non-3x3 edges
        # - Keep 3x3-valid edges (is3x3=True) with their actual colors
        # - Replace non-3x3 edges with unused valid color-pairs from BOY layout
        # This ensures all 12 edges have valid, unique color-pairs for sanity check
        if self._cube.is_even and fix_non_3x3_edges:
            modified = modified.with_fixed_non_3x3_edges(
                cube=self._cube,
                reference_scheme=self._cube.original_scheme
            )
        # Note: Odd cubes don't need this fix - their edges are always 3x3-valid

        # Step 4: Verify BOY layout (centers only)
        assert modified.matches_scheme(self._cube.original_scheme), \
            "Shadow cube colors must match color scheme"

        # Step 5: Apply to shadow cube (includes sanity check)
        shadow.set_3x3_colors(modified)
