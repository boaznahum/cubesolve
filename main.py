import msvcrt

import algs
import viewer
from algs import Alg
from cube import Cube
from cube_operator import Operator


def main():
    interactive: bool = True

    c: Cube = Cube()

    op: Operator = Operator(c)

    viewer.plot(c)

    if not interactive:

        op.op(algs.Algs.R)

        print("\n")

        viewer.plot(c)

        h = op.history
        print(f"History={h}")

        return

    else:
        done = False
        inv = False
        history = ""
        while not done:

            while True:

                modifier = False
                print(f"History={op.history}")
                print(f"(iv={inv}) Please enter a command 'R L U F B D  M,X(R), Y(U) A(algs) Q:")

                value = msvcrt.getch()
                print(value.upper())
                print(value.upper() == b"R")

                n = 1 if not inv else -1
                inc = "" if not inv else "'"
                match value.upper():
                    case b"'":
                        inv = not inv
                        modifier = True
                        break
                    case b"R":
                        op.op(algs.Algs.R, inv)
                        inv = False
                        break
                    case b"L":
                        op.op(algs.Algs.L, inv)
                        inv = False
                        break
                    case b"U":
                        op.op(algs.Algs.U, inv)
                        inv = False
                        break
                    case b"F":
                        op.op(algs.Algs.F, inv)
                        inv = False
                        break
                    case b"B":
                        op.op(algs.Algs.B, inv)
                        inv = False
                        break
                    case b"D":
                        op.op(algs.Algs.D, inv)
                        inv = False
                        break

                    case b"X":
                        op.op(algs.Algs.M, inv)
                        inv = False
                        break

                    case b"Y":
                        op.op(algs.Algs.R, inv)
                        inv = False
                        break

                    case b"A":

                        alg: Alg = get_alg()

                        history += str(alg) + inc + " "
                        alg.play(c, inv)
                        inv = False
                        break

                    case b"\x03" | b"Q":
                        done = True
                        break

            print("DONE=", done)
            if not done and not modifier:
                viewer.plot(c)


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
