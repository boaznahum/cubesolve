"""Even cube edge parity exception.

Raised when an even-sized cube (4x4, 6x6, etc.) has edge parity
that requires a special algorithm to fix.
"""


class EvenCubeEdgeParityException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
