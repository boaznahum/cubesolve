import msvcrt
import sys

import algs
import viewer
from algs import Alg, Algs
from cube import Cube
from cube_operator import Operator
from solver import Solver

_terminal: bool = sys.stdin.isatty()


# print(f"{_terminal=}")
# print(f"{sys.stdin.isatty()=}")


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

        if _terminal:
            value = msvcrt.getch()
            return value.decode("utf-8")
        else:
            return input()


def main():

    inp: _Input = _Input(*sys.argv[1:])

    c: Cube = Cube()

    op: Operator = Operator(c)

    slv: Solver = Solver(op)

    viewer.plot(c)
    print("Status=", slv.status)

    done = False
    inv = False
    while not done:

        while True:

            not_operation = False  # if not_operation is true then no need to replot
            print(f"Count={op.count}, History={op.history}")
            print(f"(iv={inv}) Please enter a command:")
            print(f" 'inv R L U F B D  M,X(R), Y(U) ?solve Algs Clear Q")
            print(f" 1scramble1, 0scramble-random <undo")

            value = inp.get_input()
            print(value.upper())

            # the 'break' is to quit the input loop
            match value.upper():
                case "'":
                    inv = not inv
                    not_operation = True
                    break
                case "R":
                    op.op(algs.Algs.R, inv)
                    break
                case "L":
                    op.op(algs.Algs.L, inv)
                    break
                case "U":
                    op.op(algs.Algs.U, inv)
                    break
                case "F":
                    op.op(algs.Algs.F, inv)
                    break
                case "B":
                    op.op(algs.Algs.B, inv)
                    break
                case "D":
                    op.op(algs.Algs.D, inv)
                    break

                case "X":
                    op.op(algs.Algs.X, inv)
                    break

                case "Y":
                    op.op(algs.Algs.Y, inv)
                    break

                case "M":
                    op.op(algs.Algs.M, inv)
                    break

                case "A":

                    alg: Alg = get_alg()
                    op.op(alg, inv)
                    break

                case "C":
                    op.reset()
                    break

                case "1":
                    alg: Alg = Algs.scramble1()
                    op.op(alg, inv)
                    break

                case "0":
                    alg: Alg = Algs.scramble()
                    op.op(alg, inv)
                    break

                case "<":
                    op.undo()
                    break

                case "?":
                    slv.solve()
                    break

                case "\x03" | "Q":
                    done = True
                    break

        # print("DONE=", done)
        if not done and not not_operation:
            inv = False  # consumed
            viewer.plot(c)
            print("Status=", slv.status)


def get_alg() -> Alg:
    print("Algs:")
    _algs = algs.Algs.lib()

    for i, a in enumerate(_algs):
        print("", i + 1, "):", str(a))

    index = input("Alg index:")

    return _algs[int(index) - 1]

    pass


if __name__ == '__main__':
    main()
