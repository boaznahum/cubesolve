# Solver TODOs

- Make sure all queries use new context manager in Operator that suspends animation and undoes operations

find ead code in solvers

bug !!!
        try:
                solution = kociemba.solve(cube_string)
            except ValueError as e:
                # Invalid cube string usually means edge parity on even cubes
                # The orchestrator will catch this, fix parity, and retry
                if debug:
                    self.debug("Invalid cube state (likely parity):", str(e))
                    #it is a bug we must not reach here orchstrator must handle it
                raise EvenCubeEdgeParityException(
                    "Kociemba: Invalid cube state - likely edge parity on even cube"
                ) from e


why we need bith solve and  solve_3x3 ??
same as for status_3x3


