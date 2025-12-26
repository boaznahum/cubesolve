"""
Communicator Helper for NxN Big Cubes.

Provides the block commutator algorithm for any source/target face pair.
Unlike NxNCenters which only supports Front as target and Up/Back as source,
this helper supports all 30 face pair combinations.

Coordinate system: Bottom-Up, Left-to-Right (BULR)
- (0,0) is at bottom-left
- Y increases upward
- X increases rightward
"""

from typing import Tuple, TypeAlias

from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.solver.common.SolverElement import SolverElement
from cube.domain.solver.protocols import SolverElementsProvider

Point: TypeAlias = Tuple[int, int]
Block: TypeAlias = Tuple[Point, Point]


class CommunicatorHelper(SolverElement):
    """
    Helper for the block commutator algorithm on NxN cubes.

    Supports any source/target face pair (30 combinations).
    Executes the commutator WITHOUT first positioning faces.
    Optionally preserves cube state (cage preservation).
    """

    def __init__(self, solver: SolverElementsProvider) -> None:
        super().__init__(solver)

    @property
    def n_slices(self) -> int:
        return self.cube.n_slices

    def do_communicator(
        self,
        source: Face,
        target: Face,
        target_block: Block,
        source_block: Block | None = None,
        preserve_state: bool = True
    ) -> bool:
        """
        Execute block commutator to move pieces from source to target.

        The commutator is: [M', F, M', F', M, F, M, F']
        This is BALANCED (2 F + 2 F' = 0), so corners return to their position.

        Args:
            source: Source face (where pieces come from)
            target: Target face (where pieces go to)
            target_block: Block coordinates on target face ((y0,x0), (y1,x1)) in BULR
            source_block: Block coordinates on source face, defaults to target_block
            preserve_state: If True, preserve cube state (edges and corners return)

        Returns:
            True if communicator was executed, False if not needed

        Raises:
            ValueError: If source and target are the same face
            ValueError: If blocks cannot be mapped with 0-3 rotations
        """
        if source is target:
            raise ValueError("Source and target must be different faces")

        if source_block is None:
            source_block = target_block

        # TODO: Implement the communicator algorithm
        # 1. Validate blocks can be mapped with 0-3 rotations
        # 2. Compute the algorithm for this source/target pair
        # 3. Execute the algorithm using self.op.play()
        # 4. If preserve_state, undo any setup moves

        raise NotImplementedError("do_communicator not yet implemented")
