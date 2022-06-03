class AppExit(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class RunStop(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class OpAborted(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class EvenCubeEdgeParityException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class EvenCubeCornerSwapException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InternalSWError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
