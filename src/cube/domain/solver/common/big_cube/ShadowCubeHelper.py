# claude document this class
from cube.domain.model.Cube import Cube
from cube.domain.solver.common.SolverElement import SolverElement
from cube.domain.solver.common.big_cube import FacesTrackerHolder
from cube.domain.solver.protocols import SolverElementsProvider


class ShadowCubeHelper(SolverElement):
    def __init__(self, slv: SolverElementsProvider):
        super().__init__(slv)

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

        assert shadow_cube.is_boy, f"Shadow cube must be valid boy pattern, face_colors={th.get_face_colors()}"

        return shadow_cube

    def _copy_state_to_shadow(self, shadow: "Cube", th: FacesTrackerHolder ) -> None:
        """Copy corner/edge state from even cube to shadow 3x3.

        Uses the type-safe Cube3x3Colors mechanism to transfer state.
        The even cube's edge/corner colors are extracted, centers are replaced
        with face_colors, and the result is applied to the shadow cube.
        """
        # Get colors from even cube as 3x3 snapshot
        colors_3x3 = self._cube.get_3x3_colors()

        # Override centers with face_colors mapping
        modified = colors_3x3.with_centers(th.get_face_colors())

        # Verify the modified colors represent a valid BOY layout
        assert modified.is_boy(self._cube.sp), \
            "Shadow cube colors must maintain BOY layout"

        # Apply to shadow cube (includes sanity check)
        shadow.set_3x3_colors(modified)
