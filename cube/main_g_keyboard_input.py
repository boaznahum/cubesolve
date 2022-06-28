import traceback
from contextlib import contextmanager

import pyglet  # type: ignore
from pyglet.window import key  # type: ignore

from .import config
from .algs import algs
from .algs.algs import Alg, Algs
from .app_exceptions import AppExit
from .app_state import ApplicationAndViewState
from .operator.cube_operator import Operator
from .main_g_abstract import AbstractWindow, AbstractApp
from .model.cube_boy import FaceName
from .solver import Solver, SolveStep

good = Algs.bigAlg("good")







def handle_keyboard_input(window: AbstractWindow, value: int, modifiers: int):
    # print(f"{hex(value)}=")
    done = False
    app: AbstractApp = window.app
    op: Operator = app.op

    debug = config.KEYBOAD_INPUT_DEBUG

    if debug:
        print(f"In _handle_input , {value}  {hex(value)} {chr(ord('A') + (value - key.A))} ")

    vs: ApplicationAndViewState = app.vs

    def handle_in_both_modes():
        """

        :return: (True if was handled, True no-op : no need redrawing)
        """
        match value:

            case key.SPACE:
                if modifiers & key.MOD_CTRL:
                    vs.single_step_mode = not vs.single_step_mode
                else:
                    vs.paused_on_single_step_mode = None

                return True, False

            case key.NUM_ADD:
                vs.inc_speed()
                return True, False

            case key.NUM_SUBTRACT:
                vs.dec_speed()
                return True, False

            case key.X:
                if modifiers & key.MOD_CTRL:
                    vs.alpha_x -= vs.alpha_delta
                    return True, True

                elif modifiers & key.MOD_ALT:
                    vs.alpha_x += vs.alpha_delta
                    return True, True

            case key.Y:
                if modifiers & key.MOD_CTRL:
                    vs.alpha_y -= vs.alpha_delta
                    return True, True
                elif modifiers & key.MOD_ALT:
                    vs.alpha_y += vs.alpha_delta
                    return True, True

            case key.Z:
                if modifiers & key.MOD_CTRL:
                    vs.alpha_z -= vs.alpha_delta
                    return True, True
                elif modifiers & key.MOD_ALT:
                    vs.alpha_z += vs.alpha_delta
                    return True, True

            case key.UP:
                if modifiers & key.MOD_CTRL:
                    vs.dec_fov_y()  # zoom in
                    vs.set_projection(window.width, window.height)
                    return True, True
                else:
                    vs.change_offset(0, 1, 0)
                    return True, True

            case key.DOWN:
                if modifiers & key.MOD_CTRL:
                    vs.inc_fov_y()  # zoom out
                    vs.set_projection(window.width, window.height)
                    return True, True
                else:
                    vs.change_offset(0, -1, 0)
                    return True, True

            case key.UP:
                if modifiers & key.MOD_CTRL:
                    vs.dec_fov_y()  # zoom in
                    vs.set_projection(window.width, window.height)
                    return True, True
                elif modifiers == 0:
                    vs.change_offset(0, 1, 0)
                    return True, True

            case key.DOWN:
                if modifiers & key.MOD_CTRL:
                    vs.inc_fov_y()  # zoom out
                    vs.set_projection(window.width, window.height)
                    return True, True
                elif modifiers == 0:
                    vs.change_offset(0, -1, 0)
                    return True, True

            case key.RIGHT:
                if modifiers == 0:
                    vs.change_offset(1, 0, 0)
                    return True, True

            case key.LEFT:
                if modifiers == 0:
                    vs.change_offset(-1, 0, 0)
                    return True, True

        return False, None

    no_operation: bool = False

    if window.animation_running or op.is_animation_running:

        if debug:
            print(f"Keyboard input, in animation mode")

        handled, _no_operation = handle_in_both_modes()

        if debug:
            print(f"Handled by 'handle_in_both_modes()={handled}, {_no_operation=}")

        if handled:

            no_operation = _no_operation

        else:
            #
            # print(f"{value==key.S}")
            match value:

                case key.Q:
                    op.abort()  # solver will not try to check state
                    window.close()
                    raise AppExit

                case key.S:
                    op.abort()  # doesn't work, we can't catch it, maybe pyglet ignore it, because it is in handler

        if not no_operation:
            if debug:
                print("keyboard input 'animation mode' decide to update_gui_elements")
            window.update_gui_elements()
        else:
            if debug:
                print("keyboard input 'animation mode' decide not to update_gui_elements")

        return False

    slv: Solver = app.slv

    inv = modifiers & key.MOD_SHIFT

    alg: Alg

    def _slice_alg(r: algs.SliceAbleAlg):
        return vs.slice_alg(app.cube, r)

    global good
    # noinspection PyProtectedMember

    handled, no_operation = handle_in_both_modes()

    if debug:
        print(f"keyboard input 'main' handle_in_both_modes return {handled=} {no_operation}")

    if not handled:

        no_operation = False

        solver_animation = False if (modifiers & key.MOD_SHIFT) else None

        # noinspection PyProtectedMember
        match value:

            case key.I:
                print(f"{vs.alpha_x + vs.alpha_x_0=} {vs.alpha_y+vs.alpha_y_0=} {vs.alpha_z+vs.alpha_z_0=}")
                no_operation = True
                from model.cube_queries import CubeQueries
                CubeQueries.print_dist(app.cube)

            case key.W:
                app.cube.front.corner_top_right.annotate(False)
                app.cube.front.corner_top_left.annotate(True)
                op.op(Algs.AN)

            case key.P:
                op.op(Algs.RD)

            case key.O:
                if modifiers & key.MOD_CTRL:
                    config.SOLVER_DEBUG = not config.SOLVER_DEBUG
                elif modifiers & key.MOD_ALT:
                    config.CHECK_CUBE_SANITY = not config.CHECK_CUBE_SANITY
                else:
                    op.toggle_animation_on()

            case key.EQUAL:
                app.vs.cube_size += 1
                app.cube.reset(app.vs.cube_size)
                op.reset()
                window.viewer.reset()

            case key.MINUS:
                if vs.cube_size > 3:
                    app.vs.cube_size -= 1
                app.cube.reset(app.vs.cube_size)
                op.reset()
                window.viewer.reset()

            case key.BRACKETLEFT:
                if modifiers and key.MOD_ALT:
                    vs.slice_start = vs.slice_stop = 0

                elif modifiers and key.MOD_SHIFT:
                    if vs.slice_start:
                        vs.slice_start -= 1
                    else:
                        vs.slice_start = 0
                    if vs.slice_start < 1:
                        vs.slice_start = 1

                else:
                    if vs.slice_start:
                        vs.slice_start += 1
                    else:
                        vs.slice_start = 1
                    if vs.slice_start > vs.slice_stop:
                        vs.slice_start = vs.slice_stop

            case key.BRACKETRIGHT:
                if modifiers and key.MOD_SHIFT:
                    vs.slice_stop -= 1
                    if vs.slice_stop < vs.slice_start:
                        vs.slice_stop = vs.slice_start
                else:
                    vs.slice_stop += 1
                    if vs.slice_stop > app.cube.size:
                        vs.slice_stop = app.cube.size

            case key.A:

                nn = slv.cube.n_slices

                mid = 1 + nn // 2  # == 3 on 5

                end = nn

                ml = 1
                if modifiers & key.MOD_CTRL:
                    ml = 2

                # on odd cube
                swap_faces = [Algs.M[1:mid - 1].prime * ml + Algs.F.prime * 2 + Algs.M[1:mid - 1] * ml +
                              Algs.M[mid + 1:end].prime * ml + Algs.F * 2 + Algs.M[mid + 1:end] * ml
                              ]
                op.op(Algs.bigAlg(None, *swap_faces))

                # communicator 1
                rotate_on_cell = Algs.M[mid]
                rotate_on_second = Algs.M[1:mid - 1]  # E is from right to left
                on_front_rotate = Algs.F.prime

                cum = [rotate_on_cell.prime * ml,
                       on_front_rotate,
                       rotate_on_second.prime * ml,
                       on_front_rotate.prime,
                       rotate_on_cell * ml,
                       on_front_rotate,
                       rotate_on_second * ml,
                       on_front_rotate.prime]
                op.op(Algs.bigAlg(None, *cum))

                rotate_on_second = Algs.M[mid + 1:nn]  # E is from right to left
                cum = [rotate_on_cell.prime * ml,
                       on_front_rotate,
                       rotate_on_second.prime * ml,
                       on_front_rotate.prime,
                       rotate_on_cell * ml,
                       on_front_rotate,
                       rotate_on_second * ml,
                       on_front_rotate.prime]
                op.op(Algs.bigAlg(None, *cum))

            case key.R:
                # _last_face = FaceName.R
                op.op(_slice_alg(algs.Algs.R), inv)
                # op.op(algs.Algs.R, inv)

            case key.L:
                op.op(_slice_alg(algs.Algs.L), inv)

            case key.U:
                op.op(_slice_alg(algs.Algs.U), inv)

            case key.F:
                op.op(_slice_alg(algs.Algs.F), inv)

            case key.S:
                op.op(_slice_alg(algs.Algs.S), inv)

            case key.B:
                op.op(_slice_alg(algs.Algs.B), inv)

            case key.D:
                _last_face = FaceName.D
                op.op(_slice_alg(algs.Algs.D), inv)

            case key.X:  # Alt/Ctrl was handled in both
                if not modifiers & (key.MOD_CTRL | key.MOD_ALT):
                    op.op(algs.Algs.X, inv)

            case key.M:
                op.op(_slice_alg(algs.Algs.M), inv)

            case key.Y:
                # Alt/Ctrl was handled in both
                if not modifiers & (key.MOD_CTRL | key.MOD_ALT):
                    op.op(algs.Algs.Y, inv)

            case key.E:
                op.op(_slice_alg(algs.Algs.E), inv)

            case key.Z:
                # Alt/Ctrl was handled in both
                if not modifiers & (key.MOD_CTRL | key.MOD_ALT):
                    op.op(algs.Algs.Z, inv)

            case key.C:

                if not (modifiers & key.MOD_ALT):
                    op.reset()
                    app.reset()
                if modifiers and key.MOD_CTRL:
                    app.vs.reset()
                    app.vs.set_projection(window.width, window.height)

            case key._0:
                with vs.w_animation_speed(4):
                    if modifiers & key.MOD_ALT:
                        # Failed on [5:5]B
                        # [{good} [3:3]R [3:4]D S [2:2]L]

                        alg = Algs.R[3:3] + Algs.D[3:4] + Algs.S + Algs.L[2:2]  # + Algs.B[5:5]
                        op.op(alg, inv),  # animation=False)

                    elif modifiers & key.MOD_CTRL:
                        alg = Algs.B[5:5]
                        op.op(alg, inv)
                    else:
                        alg = Algs.scramble(app.cube.size, n=100)

                        op.op(alg, inv)

            case key._1:

                if modifiers and key.MOD_SHIFT:  # test -1
                    scramble_key = -1
                else:
                    scramble_key = value - key._0

                alg = Algs.scramble(app.cube.size, scramble_key, 5)

                with _wait_cursor(window):
                    op.op(alg, inv, animation=False)

            case key._2 | key._3 | key._4 | key._5 | key._6:

                # print(f"{modifiers & key.MOD_CTRL=}  {modifiers & key.MOD_ALT=}")
                if modifiers & key.MOD_CTRL:
                    # noinspection PyProtectedMember
                    big_alg: algs.BigAlg = Algs.scramble(app.cube.size, value - key._0)
                    good = algs.BigAlg("good")
                    for a in big_alg.algs:
                        try:
                            with _wait_cursor(window):
                                op.op(a, animation=False)
                            good = good + a
                        except:
                            from model.cube_queries import CubeQueries
                            CubeQueries.print_dist(app.cube)
                            print("Failed on", a)
                            print(good)
                            raise
                elif modifiers & key.MOD_ALT:
                    print("Rerunning good:", good)
                    for a in good.algs:
                        try:
                            with _wait_cursor(window):
                                op.op(a, animation=False)
                            from model.cube_queries import CubeQueries
                            CubeQueries.print_dist(app.cube)
                        except:
                            print(good)
                            raise

                else:
                    # to match test int
                    # noinspection PyProtectedMember
                    alg = Algs.scramble(app.cube.size, value - key._0)
                    with _wait_cursor(window):
                        op.op(alg, inv, animation=False)

            case key.COMMA:
                op.undo()

            case key.SLASH:
                # solution = slv.solution().simplify()
                # op.op(solution)
                slv.solve(animation=solver_animation)

            case key.F1:
                slv.solve(what=SolveStep.L1, animation=solver_animation)

            case key.F2:
                slv.solve(what=SolveStep.L2, animation=solver_animation)

            case key.F3:

                if modifiers and key.MOD_CTRL:
                    slv.solve(what=SolveStep.L3x, animation=solver_animation)
                else:
                    slv.solve(what=SolveStep.L3, animation=solver_animation)

            case key.F4:

                slv.solve(what=SolveStep.NxNCenters, animation=solver_animation)

            case key.F5:

                n0 = op.count
                slv.solve(what=SolveStep.NxNEdges, animation=solver_animation)
                window._last_edge_solve_count = op.count - n0

            case key.T:
                if modifiers & key.MOD_ALT:
                    scramble_key = 26
                    n = None

                    op.reset()  # also reset cube
                    alg = Algs.scramble(app.cube.size, scramble_key, n)
                    op.op(alg, animation=False)
                    slv.solve(animation=False, debug=False)
                    assert slv.is_solved
                else:

                    with _wait_cursor(window):
                        nn = config.TEST_NUMBER_OF_SCRAMBLE_ITERATIONS
                        ll = 0
                        count = 0
                        n_loops = 0
                        for s in range(-1, nn):
                            print(str(s + 2) + f"/{nn + 1}, ", end='')
                            ll += 1
                            if ll > 15:
                                print()
                                ll = 0

                            op.reset()  # also reset cube
                            if s == -1:
                                scramble_key = -1
                                n = 5
                            else:
                                scramble_key = s
                                n = None

                            alg = Algs.scramble(app.cube.size, scramble_key, n)

                            op.op(alg, animation=False)

                            # noinspection PyBroadException
                            try:
                                c0 = op.count
                                slv.solve(animation=False, debug=False)
                                assert slv.is_solved
                                count += op.count - c0
                                n_loops += 1

                            except Exception:
                                print(f"Failure on scramble key={scramble_key}, n={n} ")
                                traceback.print_exc()
                                raise
                        print()
                        print(f"Count={count}, average={count / n_loops}")

            case key.Q:
                window.close()
                return

            case _:
                return False

    # no need to redraw, on_draw is called after any event

    if not no_operation:
        if debug:
            print("keyboard input main decide to update gui elements")
        window.update_gui_elements()
    else:
        if debug:
            print("keyboard input main decide not to update gui elements")

    return done


@contextmanager
def _wait_cursor(window: AbstractWindow):
    cursor = window.get_system_mouse_cursor(window.CURSOR_WAIT)
    window.set_mouse_cursor(cursor)
    try:  # test
        yield None

    finally:
        window.set_mouse_cursor(None)
