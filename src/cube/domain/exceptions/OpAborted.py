"""Operation aborted exception.

Raised when a solver operation is aborted by user request or timeout.
"""


class OpAborted(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
