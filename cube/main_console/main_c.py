import sys
import traceback

import keyboard

import viewer
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


def main():
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
                case "'":
                    inv = not inv
                    not_operation = True
                    break
                case "R":
                    op.play(Algs.R, inv)
                    break
                case "L":
                    op.play(Algs.L, inv)
                    break
                case "U":
                    op.play(Algs.U, inv)
                    break
                case "F":
                    op.play(Algs.F, inv)
                    break
                case "B":
                    op.play(Algs.B, inv)
                    break
                case "D":
                    op.play(Algs.D, inv)
                    break

                case "X":
                    op.play(Algs.X, inv)
                    break

                case "Y":
                    op.play(Algs.Y, inv)
                    break

                case "M":
                    op.play(Algs.M, inv)
                    break

                case "A":

                    alg: Alg = get_alg()
                    op.play(alg, inv)
                    break

                case "C":
                    op.reset()
                    break

                case "0":
                    alg: Alg = Algs.scramble(cube_size)
                    op.play(alg, inv)
                    break

                case "1" | "2" | "3" | "4" | "5" | "6":
                    # to match test int
                    alg: Alg = Algs.scramble(cube_size, int(value))
                    op.play(alg, inv)
                    break

                case "<":
                    op.undo()
                    break

                case "?":
                    slv.solve()
                    break

                case "T":
                    # test
                    for s in range(0, 50):
                        op.reset()
                        alg: Alg = Algs.scramble(s)
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

                case "\x03" | "Q":
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
