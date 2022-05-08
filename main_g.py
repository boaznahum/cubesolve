# noinspection PyCompatibility
import math
import msvcrt
import sys
import traceback
from typing import Tuple

import glooey
import pyglet
from pyglet import shapes
from pyglet.graphics import Batch
from pyglet.window import Window, key

import algs
from algs import Alg, Algs
from cube import Cube
from cube_operator import Operator
from solver import Solver
from viewer_g import GCubeViewer

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
            value = value.decode("utf-8")
        else:
            value = input()

        if len(value) > 1:
            self._replay.extend([*value[1:]])
        return value[0]


def _create_initial_gui() -> Tuple[Batch, Window]:
    window = pyglet.window.Window(720, 480, "Cube")
    batch = pyglet.graphics.Batch()

    @window.event
    def on_draw():
        batch.draw()

    return batch, window


def main():
    c: Cube = Cube()

    op: Operator = Operator(c)

    slv: Solver = Solver(op)

    batch: Batch
    window: Window
    batch, window = _create_initial_gui()

    viewer: GCubeViewer = GCubeViewer(batch, c)

    @window.event
    def on_key_press(symbol, modifiers):
        done = _handle_input(symbol, op, viewer, slv)
        if done:
            window.close()


    pyglet.app.run()


    # viewer.plot()
    # print("Status=", slv.status)
    #
    # done = False
    # inv = False
    # while not done:
    #
    #     while True:
    #         not_operation = False  # if not_operation is true then no need to replot
    #         print(f"Count={op.count}, History={op.history}")
    #         print(f"(iv={inv}) Please enter a command:")
    #         print(f" 'inv R L U F B D  M,X(R), Y(U) ?solve Algs Clear Q")
    #         print(f" 1scramble1, 0scramble-random <undo, Test")
    #
    #         value = inp.get_input()
    #         print(value.upper())
    #
    #         # the 'break' is to quit the input loop


def _handle_input(value: int, op: Operator, viewer: GCubeViewer, slv: Solver) -> bool:
    inv = False

    done = False
    not_operation = False

    print(value)
    match value:
        case "'":
            inv = not inv
            not_operation = True
        case key.R:
            op.op(algs.Algs.R, inv)
        case "L":
            op.op(algs.Algs.L, inv)
        case "U":
            op.op(algs.Algs.U, inv)

        case "F":
            op.op(algs.Algs.F, inv)

        case "B":
            op.op(algs.Algs.B, inv)

        case "D":
            op.op(algs.Algs.D, inv)

        case "X":
            op.op(algs.Algs.X, inv)

        case "Y":
            op.op(algs.Algs.Y, inv)

        case "M":
            op.op(algs.Algs.M, inv)

        case "A":

            alg: Alg = get_alg()
            op.op(alg, inv)

        case "C":
            op.reset()

        case "0":
            alg: Alg = Algs.scramble()
            op.op(alg, inv)

        case "1" | "2" | "3" | "4" | "5" | "6":
            # to match test int
            alg: Alg = Algs.scramble(int(value))
            op.op(alg, inv)

        case "<":
            op.undo()

        case "?":
            slv.solve()

        case "T":
            # test
            for s in range(0, 50):
                op.reset()
                alg: Alg = Algs.scramble(s)
                op.op(alg)

                # noinspection PyBroadException
                try:
                    slv.solve()
                    assert slv.is_solved

                except Exception:
                    print(f"Failure on {s}")
                    traceback.print_exc()
                    break

        case "\x03" | "Q":
            done = True

    if not done and not not_operation:
        inv = False  # consumed
        viewer.plot()
        print("Status=", slv.status)

    return done

    # print("DONE=", done)


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
