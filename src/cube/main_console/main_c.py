import sys
import traceback
from dataclasses import dataclass

import keyboard

from . import viewer
from .keys import Keys
from cube.algs import Algs, Alg
from cube.model import Cube
from cube.operator import Operator
from cube.solver import Solver, Solvers


@dataclass
class ConsoleResult:
    """Result from running the console application."""
    cube: Cube
    operator: Operator
    solver: Solver


class _Input:
    """Input handler that supports both keyboard and injected sequences."""

    def __init__(self, key_sequence: str | None = None, use_keyboard: bool = True) -> None:
        super().__init__()
        self._replay: list[str] = []
        self._use_keyboard = use_keyboard

        if key_sequence:
            self._replay.extend([*key_sequence])

    def get_input(self) -> str:
        if self._replay:
            return self._replay.pop(0)

        if not self._use_keyboard:
            raise StopIteration("No more input in sequence")

        while True:
            if sys.stdin.isatty():
                value = keyboard.read_event(suppress=True).name
                print(f"{value=}  {type(value)=}")
            else:
                value = input()

            if value:
                break

        if len(value) > 1:
            self._replay.extend([*value[1:]])
        return value[0]


def run(
    key_sequence: str | None = None,
    cube_size: int = 3,
    debug: bool = False
) -> ConsoleResult:
    """
    Run the console cube application.

    Parameters
    ----------
    key_sequence : str | None
        Optional key sequence to inject. If None, reads from keyboard.
        Must end with 'Q' to quit when provided.
    cube_size : int
        Size of the cube (default 3).
    debug : bool
        Enable debug output (default False).

    Returns
    -------
    ConsoleResult
        Contains the cube, operator, and solver after execution.

    Examples
    --------
    Run with injected keys:
        result = run(Keys.F + Keys.R + Keys.QUIT)
        assert not result.cube.solved  # Cube is scrambled

    Scramble and solve:
        result = run(Keys.SCRAMBLE_1 + Keys.SOLVE + Keys.QUIT)
        assert result.cube.solved
    """
    use_keyboard = key_sequence is None
    inp = _Input(key_sequence=key_sequence, use_keyboard=use_keyboard)

    cube: Cube = Cube(cube_size)
    op: Operator = Operator(cube)
    slv: Solver = Solvers.default(op)

    if debug:
        viewer.plot(cube)
        print("Status=", slv.status)

    done = False
    inv = False

    while not done:
        while True:
            not_operation = False

            if debug:
                print(f"Count={op.count}, History={op.history_as_alg().to_printable()}")
                print(f"(iv={inv}) Please enter a command:")
                print(f" '-inv R L U F B D  M,X(R), Y(U) ?solve Algs, Clear Q")
                print(f" 1scramble1, 0scramble-random <undo, Test")

            try:
                value = inp.get_input()
            except StopIteration:
                done = True
                break

            if debug:
                print(value.upper())

            value = value.upper()
            match value:
                case Keys.INV:
                    inv = not inv
                    not_operation = True
                    break
                case Keys.R:
                    op.play(Algs.R, inv)
                    break
                case Keys.L:
                    op.play(Algs.L, inv)
                    break
                case Keys.U:
                    op.play(Algs.U, inv)
                    break
                case Keys.F:
                    op.play(Algs.F, inv)
                    break
                case Keys.B:
                    op.play(Algs.B, inv)
                    break
                case Keys.D:
                    op.play(Algs.D, inv)
                    break

                case Keys.X:
                    op.play(Algs.X, inv)
                    break

                case Keys.Y:
                    op.play(Algs.Y, inv)
                    break

                case Keys.M:
                    op.play(Algs.M, inv)
                    break

                case Keys.ALGS:
                    alg: Alg = _get_alg()
                    op.play(alg, inv)
                    break

                case Keys.CLEAR:
                    op.reset()
                    break

                case Keys.SCRAMBLE_RANDOM:
                    alg = Algs.scramble(cube_size)
                    op.play(alg, inv)
                    break

                case Keys.SCRAMBLE_1 | Keys.SCRAMBLE_2 | Keys.SCRAMBLE_3 | Keys.SCRAMBLE_4 | Keys.SCRAMBLE_5 | Keys.SCRAMBLE_6:
                    alg = Algs.scramble(cube_size, int(value))
                    op.play(alg, inv)
                    break

                case Keys.UNDO:
                    op.undo()
                    break

                case Keys.SOLVE:
                    slv.solve()
                    break

                case Keys.TEST:
                    for s in range(0, 50):
                        op.reset()
                        alg = Algs.scramble(s)
                        op.play(alg)

                        try:
                            slv.solve()
                            assert slv.is_solved
                        except Exception:
                            print(f"Failure on {s}")
                            traceback.print_exc()
                            break
                    break

                case Keys.CTRL_C | Keys.QUIT:
                    done = True
                    break

        if not done and not not_operation:
            inv = False
            if debug:
                viewer.plot(cube)
                print("Status=", slv.status)

    return ConsoleResult(cube=cube, operator=op, solver=slv)


def _get_alg() -> Alg:
    """Interactive algorithm selection (for keyboard mode only)."""
    print("Algs:")
    _algs = Algs.lib()

    for i, a in enumerate(_algs):
        print("", i + 1, "):", str(a))

    index = input("Alg index:")
    return _algs[int(index) - 1]


def main() -> None:
    """Entry point for command-line usage."""
    key_sequence = sys.argv[1] if len(sys.argv) > 1 else None
    run(key_sequence=key_sequence, debug=True)


if __name__ == '__main__':
    main()
