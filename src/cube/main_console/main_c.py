import sys
import traceback

import keyboard

from . import viewer
from .keys import Keys
from cube.algs import Algs, Alg
from cube.model import Cube
from cube.operator import Operator
from cube.solver import Solver, Solvers

_terminal: bool = sys.stdin.isatty()


print(f"{_terminal=}")
print(f"{sys.stdin.isatty()=}")


class _Input:

    def __init__(self, *replay: str) -> None:
        super().__init__()

        _replay: list[str] = []

        if replay:
            for r in replay:
                _replay.extend([*r])

            print(f"{_replay=}")

        self._replay = _replay

    def get_input(self) -> str:

        if self._replay:
            return self._replay.pop(0)

        while True:

            if _terminal:
                value = keyboard.read_event(suppress=True).name
                print(f"{value=}  {type(value)=}")
            else:
                value = input()
                #print(f"{value=}  {type(value)=}")  # str

            if value:
                break

        if len(value) > 1:
            self._replay.extend([*value[1:]])
        return value[0]


def main() -> None:
    inp: _Input = _Input(*sys.argv[1:])

    cube_size: int = 3
    cube: Cube = Cube(3)

    op: Operator = Operator(cube)

    slv: Solver = Solvers.default(op)

    viewer.plot(cube)
    print("Status=", slv.status)

    done = False
    inv = False
    while not done:

        while True:

            not_operation = False  # if not_operation is true, then no need to replot
            print(f"Count={op.count}, History={op.history_as_alg().to_printable()}")
            print(f"(iv={inv}) Please enter a command:")
            print(f" '-inv R L U F B D  M,X(R), Y(U) ?solve Algs, Clear Q")
            print(f" 1scramble1, 0scramble-random <undo, Test")

            value = inp.get_input()
            print(value.upper())

            # the 'break' is to quit the input loop
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
                    alg: Alg = get_alg()
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
                    # to match test int
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
                    # test
                    for s in range(0, 50):
                        op.reset()
                        alg = Algs.scramble(s)
                        op.play(alg)

                        # noinspection PyBroadException
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

        # print("DONE=", done)
        if not done and not not_operation:
            inv = False  # consumed
            viewer.plot(cube)
            print("Status=", slv.status)


def get_alg() -> Alg:
    print("Algs:")
    _algs = Algs.lib()

    for i, a in enumerate(_algs):
        print("", i + 1, "):", str(a))

    index = input("Alg index:")

    return _algs[int(index) - 1]

    pass


if __name__ == '__main__':
    main()
