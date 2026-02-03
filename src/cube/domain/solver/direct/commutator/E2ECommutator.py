"""
Edge-to-Edge Commutator for NxN cubes.

This helper provides commutator algorithms for edge solving
in the layer-by-layer approach.
"""
from cube.domain.algs import Alg, Algs
from cube.domain.model import EdgeWing
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
                face_column_on_source_edge, is_target_right_edge, source_wing, target_wing
            )

            return True

    def do_right_or_left_commutator_by_source_ltr_index(self,
                                                        source_ltr_index: int,
                                                        is_right: bool,
                                                        source_wing: EdgeWing,
                                                        target_wing: EdgeWing) -> None:
        """
        Execute the actual commutator algorithm.

        Args:
            source_ltr_index: The LTR index on the source edge (0-based)
            is_right: True for right edge target, False for left edge target
            source_wing: The source wing being moved
            target_wing: The target wing position
        """
        alg_index = source_ltr_index + 1  # one based
        alg: Alg
        if is_right:

            # U R
            # U' [2]M'
            # U R'
            # U' [2]M

            alg = Algs.seq(Algs.U, Algs.R,
                           Algs.U.prime, Algs.M[alg_index].prime,
                           Algs.U, Algs.R.prime,
                           Algs.U.prime, Algs.M[alg_index]
                           )
        else:
            #  U' L'
            #  U [1]M'
            #  U' L
            #  U [1]M
            alg = Algs.seq(
                Algs.U.prime, Algs.L.prime,
                Algs.U, Algs.M[alg_index].prime,
                Algs.U.prime, Algs.L,
                Algs.U + Algs.M[alg_index]
            )

        with self.annotate(([source_wing], AnnWhat.Moved),
                           ([target_wing], AnnWhat.FixedPosition),
                           h2=f"Bringing {source_wing.parent_name_index_colors}"
                              f" to {target_wing.parent_name_and_index}",

                           ):
            # U R U' [2]M' U R' U' [2]M
            self.op.play(alg)
