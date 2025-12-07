"""Internal software error exception.

Raised when an unexpected internal error occurs in the domain layer.
This typically indicates a bug in the code rather than invalid user input.
"""


class InternalSWError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
