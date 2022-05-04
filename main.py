import msvcrt
import sys

import algs
import viewer
from algs import Alg
from cube import Cube
from cube_operator import Operator
from solver import Solver

_terminal: bool = sys.stdin.isatty()

print(f"{_terminal=}")
print(f"{sys.stdin.isatty()=}")


def get_input() -> str:
    if _terminal:
        value = msvcrt.getch()
        return value.decode("utf-8")
    else:
        return input()


def main():
    c: Cube = Cube()

    op: Operator = Operator(c)

    slv: Solver = Solver(op)

    viewer.plot(c)
    print("Status=", slv.status)

    done = False
    inv = False
    history = ""
    while not done:

        while True:

            modifier = False
            print(f"History={op.history}")
            print(f"(iv={inv}) Please enter a command 'R L U F B D  M,X(R), Y(U) ?solve Algs Clear Q:")

            value = get_input()
            print(value.upper())
            print(value.upper() == b"R")

            n = 1 if not inv else -1
            inc = "" if not inv else "'"
            match value.upper():
                case "'":
                    inv = not inv
                    modifier = True
                    break
                case "R":
                    op.op(algs.Algs.R, inv)
                    inv = False
                    break
                case "L":
                    op.op(algs.Algs.L, inv)
                    inv = False
                    break
                case "U":
                    op.op(algs.Algs.U, inv)
                    inv = False
                    break
                case "F":
                    op.op(algs.Algs.F, inv)
                    inv = False
                    break
                case "B":
                    op.op(algs.Algs.B, inv)
                    inv = False
                    break
                case "D":
                    op.op(algs.Algs.D, inv)
                    inv = False
                    break

                case "X":
                    op.op(algs.Algs.X, inv)
                    inv = False
                    break

                case "Y":
                    op.op(algs.Algs.Y, inv)
                    inv = False
                    break

                case "M":
                    op.op(algs.Algs.M, inv)
                    inv = False
                    break

                case "A":

                    alg: Alg = get_alg()

                    history += str(alg) + inc + " "
                    alg.play(c, inv)
                    inv = False
                    break

                case "C":

                    op.reset()
                    inv = False
                    break

                case "?":

                    slv.solve()
                    inv = False
                    break

                case "\x03" | "Q":
                    done = True
                    break

        print("DONE=", done)
        if not done and not modifier:
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
