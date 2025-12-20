"""Exception raised when PLL detects edge swap parity on even cube.

This is different from EvenCubeEdgeParityException (OLL edge orientation parity):
- OLL parity: 1 or 3 edges have wrong orientation (flipped)
- PLL swap parity: 2 edges need to swap but it's an impossible permutation

Both can occur on even cubes (4x4, 6x6) due to the additional degrees of freedom
in edge pairing that can create states unreachable on a standard 3x3.
"""


class EvenCubeEdgeSwapParityException(Exception):
    """Raised when PLL detects edge swap parity.

    The solver orchestrator should catch this and apply the appropriate
    parity fix algorithm that swaps two edge slices on the real cube.
    """
    pass
