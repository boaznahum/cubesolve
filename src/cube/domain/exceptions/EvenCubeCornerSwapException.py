"""
Even Cube Corner Swap Exception (PLL Parity)
============================================

Raised when an even-sized cube (4x4, 6x6, etc.) has corner parity - an
"impossible" 3x3 state where exactly 2 corners need to be swapped.


What is Corner Parity?
----------------------
On a real 3x3 cube, corners can only be permuted in certain ways. You can
NEVER have exactly 2 corners that need swapping (with all others in place).
Corner swaps always come in pairs or cycles.

On a 4x4 (or any even cube), the reduction process can create a state where
the "virtual 3x3" has exactly 2 corners out of position - an impossible
state for a real 3x3.


Where Detected
--------------
- L3Corners (lines ~100-108): After positioning corners, if exactly 2 are
  in position on an even cube → does a corner swap, then raises this exception
- See: src/cube/domain/solver/beginner/L3Corners.py


How Handled
-----------
Unlike edge parity, the fix is done IN L3Corners before raising the exception.
The exception just signals the orchestrator to retry the solve (the swap
algorithm already fixed it).


Flow
----
1. Orchestrator calls solver_3x3.solve_3x3()
2. L3Corners detects 2 corners in position (impossible 3x3 state)
3. L3Corners does the corner swap fix itself
4. L3Corners raises EvenCubeCornerSwapException
5. Orchestrator catches exception and retries solve_3x3()
6. Now the cube is in a valid 3x3 state → solve completes
"""


class EvenCubeCornerSwapException(Exception):
    """
    Raised when an even cube has corner parity (PLL parity).

    This exception signals that the cube had corner parity which has
    already been fixed by the swap algorithm. The orchestrator should
    catch this and retry the solve.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
