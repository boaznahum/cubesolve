import traceback

import pyglet
#pyglet.options["debug_graphics_batch"] = True

import glooey
from pyglet.window import key

import algs
import viewer as text_viewer
from algs import Alg, Algs
from cube import Cube
from cube_operator import Operator
from solver import Solver
from viewer_g import GCubeViewer


class Screen:

    def __init__(self) -> None:
        super().__init__()
        self.batch = None
        self.window = None
        # self.status: glooey.Label | None = None
        self.status: pyglet.text.Label | None = None

        self.alpha_x: float = 0
        self.alpha_y: float = 0
        self.alpha_z: float = 0
        self.alpha_delta = 0.1
        self.cube = None


def _create_initial_gui() -> Screen:
    window = pyglet.window.Window(720, 480, "Cube")
    batch = pyglet.graphics.Batch()

    s: Screen = Screen()
    s.window = window
    s.batch = batch

    gui = glooey.Gui(window, batch=batch)

    grid = glooey.Grid()

    ph = glooey.Placeholder()
    grid.add(0, 0, ph)

    ph = glooey.Placeholder()
    grid.add(0, 1, ph)

    hbox1 = glooey.HBox()
    hbox1.hide()
    grid.add(0, 1, hbox1)
    hbox2 = glooey.HBox()
    grid.add(1, 0, hbox2)

    hbox3 = glooey.HBox()
    grid.add(1, 0, hbox2)

    grid.add(1, 1, hbox3)

    gui.add(grid)

    # s.status = pyglet.text.Label("Status", x=360, y=300, font_size=36, batch=batch)
    s.status = pyglet.text.Label("Status", x=360, y=300, font_size=36, batch=batch)

    # document = pyglet.text.decode_text('Hello, world.')
    # layout = pyglet.text.layout.TextLayout(document, 100, 20, batch=batch)

    @window.event
    def on_draw():
        window.clear()
        batch.draw()

    return s


def main():


    c: Cube = Cube()

    op: Operator = Operator(c)

    slv: Solver = Solver(op)

    s: Screen = _create_initial_gui()
    s.cube = c

    viewer: GCubeViewer = GCubeViewer(s.batch, c)

    @s.window.event
    def on_key_press(symbol, modifiers):
        done = _handle_input(symbol, modifiers, op, viewer, slv, s)
        if done:
            s.window.close()

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


def _handle_input(value: int, modifiers: int, op: Operator, viewer: GCubeViewer,
                  slv: Solver, s: Screen) -> bool:
    done = False
    not_operation = False

    inv = modifiers & key.MOD_SHIFT

    match value:

        case key.EQUAL:
            print("Flipping...")
            s.window.flip()

        case key.I:
            print(f"{s.alpha_x=} {s.alpha_y=} {s.alpha_z=}")

        case key.R:
            op.op(algs.Algs.R, inv)
        case key.L:
            op.op(algs.Algs.L, inv)

        case key.U:
            op.op(algs.Algs.U, inv)

        case key.F:
            op.op(algs.Algs.F, inv)

        case key.B:
            op.op(algs.Algs.B, inv)

        case key.D:
            op.op(algs.Algs.D, inv)

        case key.X:
            if modifiers & key.MOD_CTRL:
                s.alpha_x -= s.alpha_delta
            elif modifiers & key.MOD_ALT:
                s.alpha_x += s.alpha_delta
            else:
                op.op(algs.Algs.X, inv)

        case key.Y:
            if modifiers & key.MOD_CTRL:
                s.alpha_y -= s.alpha_delta
            elif modifiers & key.MOD_ALT:
                s.alpha_y += s.alpha_delta
            else:
                op.op(algs.Algs.Y, inv)

        case key.Z:
            if modifiers & key.MOD_CTRL:
                s.alpha_z -= s.alpha_delta
            elif modifiers & key.MOD_ALT:
                s.alpha_z += s.alpha_delta

        case "M":
            op.op(algs.Algs.M, inv)

        case "A":

            alg: Alg = get_alg()
            op.op(alg, inv)

        case key.C:
            op.reset()
            s.alpha_z = s.alpha_y = s.alpha_x = 0

        case "0":
            alg: Alg = Algs.scramble()
            op.op(alg, inv)

        case "1" | "2" | "3" | "4" | "5" | "6":
            # to match test int
            alg: Alg = Algs.scramble(int(value))
            op.op(alg, inv)

        case "<":
            op.undo()

        case key.SLASH:
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

        case key.Q:
            return True

        # case _:
        #     return False

    #    if not not_operation:
    # print("Updating ....")
    viewer.update(s.alpha_x, s.alpha_y, s.alpha_z)
    s.status.text = "Status:" + slv.status
    s.window.flip()
   # text_viewer.plot(s.cube)

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
