"""Even cube corner swap exception.

Raised when an even-sized cube (4x4, 6x6, etc.) has corner parity
that requires a special algorithm to fix.
"""


class EvenCubeCornerSwapException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
