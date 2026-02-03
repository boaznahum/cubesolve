"""
Edge-to-Edge Commutator for NxN cubes.

This helper provides commutator algorithms for edge solving
in the layer-by-layer approach.
"""
from cube.domain.algs import Alg, Algs
from cube.domain.model import EdgeWing
from cube.domain.model.Slice import Slice
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.solver.protocols import SolverElementsProvider


class E2ECommutator(SolverHelper):
    """
    Edge-to-Edge Commutator - executes commutator algorithms for edge solving.

    This helper provides shared commutator functionality for edge solvers.
    """

    D_LEVEL = 3

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv, "E2EComm")
        self._logger.set_level(E2ECommutator.D_LEVEL)

    def try_right_or_left_edge_to_edge_commutator_by_wings(self,
                                                           target_wing: EdgeWing,
                                                           source_wing: EdgeWing | None) -> bool:

        cube = self.cube
        # current we only support front
        target_edge = target_wing.parent
        target_face = cube.front
        assert target_edge.on_face(target_face)

        face_row_index_on_target_edge = target_edge.get_face_ltr_index_from_edge_slice_index(target_face,
                                                                                             target_wing.index)

        assert target_edge in [cube.fl, cube.fr]

        is_target_right_edge = target_edge is cube.fr

        if is_target_right_edge:
            required_source_wing_face_column_index = cube.inv(face_row_index_on_target_edge)
        else:
            required_source_wing_face_column_index = face_row_index_on_target_edge

        source_wing_edge = cube.fu
        if source_wing is not None:
            assert source_wing.parent is source_wing_edge
            source_wing_index = source_wing.index
            face_column_on_source_edge = source_wing.parent.get_face_ltr_index_from_edge_slice_index(
                target_face, source_wing_index)
        else:
            face_column_on_source_edge = required_source_wing_face_column_index
            source_wing_index = source_wing_edge.get_edge_slice_index_from_face_ltr_index(target_face, face_column_on_source_edge)

        source_wing = source_wing_edge.get_slice(source_wing_index)

        with self._logger.tab(
                    lambda: f"Trying commutator from wing {source_wing.parent_name_and_index} to wing {target_wing.parent_name_and_index}"):

            self.debug(lambda: f"required_source_wing_face_column_index: {required_source_wing_face_column_index}")
            self.debug(lambda: f"face_column_on_source_edge: {face_column_on_source_edge}")

            if required_source_wing_face_column_index != face_column_on_source_edge:
                self.debug(lambda: "❌❌ Source index and target don't match")
                assert source_wing is not None, "We calculate it it must be equal"
                return False  # can't perform

            self.do_right_or_left_commutator_by_source_ltr_index(
                face_column_on_source_edge, is_target_right_edge
            )

            return True

    def do_right_or_left_commutator_by_source_ltr_index(self,
                                                        source_ltr_index_on_fu: int,
                                                        is_right: bool) -> None:
        """
        Execute the actual commutator algorithm.

        Args:
            source_ltr_index_on_fu: The LTR index on the FU (front-up) edge (0-based)
            is_right: True for right edge target, False for left edge target
        """
        from cube.domain.model import EdgePosition
        from cube.domain.model.FaceName import FaceName

        cube = self.cube
        front = cube.front
        n_slices = cube.n_slices

        # Derive source_wing from FU edge
        fu_edge = cube.fu
        source_wing_index = fu_edge.get_edge_slice_index_from_face_ltr_index(front, source_ltr_index_on_fu)
        source_wing = fu_edge.get_slice(source_wing_index)

        # Derive target_wing from FR or FL edge
        target_edge = cube.fr if is_right else cube.fl
        target_position = EdgePosition.RIGHT if is_right else EdgePosition.LEFT
        target_ltr_index = cube.sized_layout.map_wing_face_ltr_index_by_edge_position(
            EdgePosition.TOP, target_position, source_ltr_index_on_fu
        )
        target_wing_index = target_edge.get_edge_slice_index_from_face_ltr_index(front, target_ltr_index)
        target_wing = target_edge.get_slice(target_wing_index)

        # Get slice name between L and R (which is M)
        slice_name = cube.layout.get_slice_sandwiched_between_face_and_opposite(FaceName.L)

        # Compute slice index from face coordinates
        # The source is on FU edge, so we use the column index on the front face
        the_slice: Slice = cube.sized_layout.get_slice(slice_name)
        # For FU edge, LTR index corresponds to column on front face, row is n_slices-1 (top)
        slice_index = the_slice.compute_slice_index(FaceName.F, (0, source_ltr_index_on_fu), n_slices)

        # Get slice algorithm and apply index (1-based for algorithm)
        slice_alg = Algs.of_slice(slice_name)
        alg_index = slice_index + 1

        # Lazy computation of third_wing from BU edge - the 3-cycle is: FU → FL/FR → BU → FU
        # Only computed when animation is on (additional_markers factory is called lazily)
        def get_third_wing() -> EdgeWing:
            # Use FaceWalkingInfo to properly compute the BU edge index from slice_index
            # M slice cycle: F → U → B → D, entry edge for B is BU
            walking_info = cube.sized_layout.create_walking_info(slice_name)
            b_face_info = walking_info.get_face_info(cube.back)
            bu_wing_index = b_face_info.compute_slice_index_on_entry_edge(slice_index)
            return cube.bu.get_slice(bu_wing_index)

        alg: Alg
        if is_right:

            # U R
            # U' [k]M'
            # U R'
            # U' [k]M

            alg = Algs.seq(Algs.U, Algs.R,
                           Algs.U.prime, slice_alg[alg_index].prime,
                           Algs.U, Algs.R.prime,
                           Algs.U.prime, slice_alg[alg_index]
                           )
        else:
            #  U' L'
            #  U [k]M'
            #  U' L
            #  U [k]M
            alg = Algs.seq(
                Algs.U.prime, Algs.L.prime,
                Algs.U, slice_alg[alg_index].prime,
                Algs.U.prime, Algs.L,
                Algs.U + slice_alg[alg_index]
            )

        # Get marker factory for at-risk marker (third wing in 3-cycle)
        mf = cube.sp.marker_factory

        with self.annotate(([source_wing], AnnWhat.Moved),
                           ([target_wing], AnnWhat.FixedPosition),
                           additional_markers=[(get_third_wing, AnnWhat.Moved, mf.at_risk)],
                           h2=lambda: f"3-cycle: {source_wing.parent_name_index_colors}"
                              f" → {target_wing.parent_name_and_index}"
                              f" → {get_third_wing().parent_name_and_index}",

                           ):
            # 3-cycle: FU → FL/FR → BU → FU
            # U R U' [2]M' U R' U' [2]M
            self.op.play(alg)
