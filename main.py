from cube import Cube, CubeView
import viewer

import msvcrt


def main():
    interactive: bool = True

    c: Cube = Cube()

   # c: CubeView = _c.view()

    viewer.plot(c)

    if not interactive:

        c.front.rotate()

        print("\n")

        viewer.plot(c)

        return

    else:
        done = False
        inv = False
        history = ""
        while not done:

            while True:

                modifier = False
                print(f"History={history}")
                print(f"(iv={inv}) Please enter a command 'R L U F B D  M,X(R), Y(U) Q:")

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
                        history += "R" + inc + " "
                        c.right.rotate(n)
                        inv = False
                        break
                    case b"L":
                        history += "L" + inc + " "
                        c.left.rotate(n)
                        break
                    case b"U":
                        history += "U" + inc + " "
                        c.up.rotate(n)
                        inv = False
                        break
                    case b"F":
                        history += "F" + inc + " "
                        c.front.rotate(n)
                        inv = False
                        break
                    case b"B":
                        history += "B" + inc + " "
                        c.back.rotate(n)
                        inv = False
                        break
                    case b"D":
                        history += "D" + inc + " "
                        c.down.rotate(n)
                        inv = False
                        break

                    case b"D":
                        history += "D" + inc + " "
                        c.down.rotate(n)
                        inv = False
                        break

                    case b"X":
                        history += "X" + inc + " "
                        c.x_rotate(n)
                        inv = False
                        break

                    case b"M":
                        history += "M" + inc + " "
                        c.m_rotate(n)
                        inv = False
                        break

                    case b"Y":
                        history += "Y" + inc + " "
                        c.y_rotate(n)
                        inv = False
                        break


                    case b"\x03" | b"Q":
                        done = True
                        break

            print("DONE=", done)
            if not done and not modifier:
                viewer.plot(c)


if __name__ == '__main__':
    main()
