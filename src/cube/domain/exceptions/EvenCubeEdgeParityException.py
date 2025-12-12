"""
Even Cube Edge Parity Exception (OLL Parity)
============================================

Raised when an even-sized cube (4x4, 6x6, etc.) has edge parity - an
"impossible" 3x3 state where a single edge appears flipped.


What is Edge Parity?
--------------------
On a real 3x3 cube, edges always flip in PAIRS - you can never have just
ONE edge flipped. It's physically impossible.

On a 4x4 (or any even cube), each "edge" is made of 2+ wing pieces that
get paired during reduction::

    Before reduction:     After reduction (paired):
      [Wing A] [Wing B]        [Edge AB]

The wings can end up in the "wrong" relative orientation::

    Correct pairing:        Parity (wrong pairing):
      [↑] [↑]                   [↑] [↓]
      looks: ↑ correct          looks: ↑ but internally broken!

When you finish reduction and try to solve as 3x3, the L3 cross step
finds an impossible state: 1 or 3 edges oriented correctly (instead of
0, 2, or 4).


Where Detected
--------------
- L3Cross._do_yellow_cross() at line ~96-99: Checks if edge count is
  not in [0, 2, 4] on an even cube → raises this exception
- See: src/cube/domain/solver/beginner/L3Cross.py


Where Fixed
-----------
- BeginnerReducer.fix_edge_parity() → NxNEdges.do_even_full_edge_parity_on_any_edge()
- Uses a special algorithm that flips internal slice orientations
  without breaking the reduction
- See: src/cube/domain/solver/beginner/NxNEdges.py


Flow
----
1. Orchestrator calls reducer.reduce() → cube reduced to virtual 3x3
2. Orchestrator calls solver_3x3.solve_3x3()
3. L3Cross detects impossible state → raises EvenCubeEdgeParityException
4. Orchestrator catches exception → calls reducer.fix_edge_parity()
5. Orchestrator retries solve_3x3() → now succeeds
"""


class EvenCubeEdgeParityException(Exception):
    """
    Raised when an even cube has edge parity (OLL parity).

    This exception signals that the cube is in an impossible 3x3 state
    due to edge parity from the reduction phase. The orchestrator should
    catch this and call the reducer's fix_edge_parity() method.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
