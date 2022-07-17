from contextlib import contextmanager
from typing import Any

import pyglet  # type: ignore
from pyglet.window import key  # type: ignore

from cube.app.app_state import ApplicationAndViewState
from . import algs
from . import config
from .algs import Alg, Algs
from .app.abstract_ap import AbstractApp
from .app_exceptions import AppExit
from .main_g_abstract import AbstractWindow
from .model.cube_boy import FaceName
from .operator.cube_operator import Operator
from .solver import Solver, SolveStep

good = Algs.seq_alg("good")

# noinspection PyProtectedMember
key0 = key._0


def handle_keyboard_input(window: AbstractWindow, value: int, modifiers: int):
    # print(f"{hex(value)}=")
    done = False
    app: AbstractApp = window.app
    op: Operator = app.op

    if config.KEYBOAD_INPUT_DEBUG:
        def debug(*_s):
            print("key board handler:", *_s)
    else:
        def debug(*_s):
            pass

    debug(f"In _handle_input , value:{value}  {hex(value)} {key.symbol_string(value)} "
          f"modifiers:{hex(modifiers)} "
          f"{key.modifiers_string(modifiers)} ")

    if key.LSHIFT <= value <= key.ROPTION:
        debug(f"In _handle_input , Only modifiers, decided to quit")
        return

    vs: ApplicationAndViewState = app.vs

    cube = app.cube

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

            case key.C:
                if modifiers & key.MOD_ALT:
                    app.vs.reset()
                    app.vs.set_projection(window.width, window.height)
                    return True, True

            case key.F10:
                vs.toggle_shadows_mode(FaceName.L)
                window.viewer.reset()
                return True, False
            case key.F11:
                vs.toggle_shadows_mode(FaceName.D)
                window.viewer.reset()
                return True, False
            case key.F12:
                vs.toggle_shadows_mode(FaceName.B)
                window.viewer.reset()
                return True, False

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
                    vs.single_step_mode_stop_pressed = True
                    op.abort()

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
                cube.cqr.print_dist()

            case key.W:
                app.cube.front.corner_top_right.annotate(False)
                app.cube.front.corner_top_left.annotate(True)
                op.play(Algs.AN)

            case key.P:

                if modifiers & key.MOD_CTRL:
                    recording = op.toggle_recording()
                    if recording is not None:  # recording stopped
                        vs.last_recording = recording

                elif modifiers & key.MOD_ALT:
                    vs.last_recording = None

                else:
                    recording = vs.last_recording
                    if recording is not None:
                        op.play_seq(recording, inv)

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

                nn = cube.n_slices

                mid = 1 + nn // 2  # == 3 on 5

                end = nn

                ml = 1
                if modifiers & key.MOD_CTRL:
                    ml = 2

                # on odd cube
                swap_faces = [Algs.M[1:mid - 1].prime * ml + Algs.F.prime * 2 + Algs.M[1:mid - 1] * ml +
                              Algs.M[mid + 1:end].prime * ml + Algs.F * 2 + Algs.M[mid + 1:end] * ml
                              ]
                op.play(Algs.seq_alg(None, *swap_faces))

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
                op.play(Algs.seq_alg(None, *cum))

                rotate_on_second = Algs.M[mid + 1:nn]  # E is from right to left
                cum = [rotate_on_cell.prime * ml,
                       on_front_rotate,
                       rotate_on_second.prime * ml,
                       on_front_rotate.prime,
                       rotate_on_cell * ml,
                       on_front_rotate,
                       rotate_on_second * ml,
                       on_front_rotate.prime]
                op.play(Algs.seq_alg(None, *cum))

            case key.R:
                if modifiers & key.MOD_CTRL:
                    op.play(algs.Algs.Rw, inv)
                else:
                    op.play(_slice_alg(algs.Algs.R), inv)

            case key.L:
                op.play(_slice_alg(algs.Algs.L), inv)

            case key.U:
                op.play(_slice_alg(algs.Algs.U), inv)

            case key.F:
                op.play(_slice_alg(algs.Algs.F), inv)

            case key.S:
                op.play(_slice_alg(algs.Algs.S), inv)

            case key.B:
                op.play(_slice_alg(algs.Algs.B), inv)

            case key.D:
                _last_face = FaceName.D
                op.play(_slice_alg(algs.Algs.D), inv)

            case key.X:  # Alt/Ctrl was handled in both
                if not modifiers & (key.MOD_CTRL | key.MOD_ALT):
                    op.play(algs.Algs.X, inv)

            case key.M:
                op.play(_slice_alg(algs.Algs.M), inv)

            case key.Y:
                # Alt/Ctrl was handled in both
                if not modifiers & (key.MOD_CTRL | key.MOD_ALT):
                    op.play(algs.Algs.Y, inv)

            case key.E:
                op.play(_slice_alg(algs.Algs.E), inv)

            case key.Z:
                # Alt/Ctrl was handled in both
                if not modifiers & (key.MOD_CTRL | key.MOD_ALT):
                    op.play(algs.Algs.Z, inv)

            case key.C:

                if not (modifiers & key.MOD_ALT):
                    app.reset()
                if modifiers and key.MOD_CTRL:
                    app.vs.reset()
                    app.vs.set_projection(window.width, window.height)

            case key._0:
                if modifiers & (key.MOD_SHIFT | key.MOD_ALT):
                    with vs.w_animation_speed(4):
                        if modifiers & key.MOD_ALT:
                            # Failed on [5:5]B
                            # [{good} [3:3]R [3:4]D S [2:2]L]

                            alg = Algs.R[3:3] + Algs.D[3:4] + Algs.S + Algs.L[2:2]  # + Algs.B[5:5]
                            op.play(alg, inv),  # animation=False)

                        else:
                            alg = Algs.B[5:5]
                            op.play(alg, inv)
                else:
                    # same as Test 0
                    scramble_key = value - key0
                    alg = Algs.scramble(app.cube.size, scramble_key)

                    with _wait_cursor(window):
                        op.play(alg, inv, animation=False)

            case key._1:

                _scramble_key = None
                _scramble_n = None

                if modifiers & (key.MOD_SHIFT | key.MOD_ALT):
                    if modifiers and key.MOD_SHIFT:  # test -1
                        _scramble_key = -1
                    else:
                        _scramble_key = value - key0

                    _scramble_n = 5
                else:
                    # same as Test 1
                    _scramble_key = value - key0

                animation = modifiers & key.MOD_CTRL

                _scramble(window, inv, _scramble_key, _scramble_n, animation)

            case key.F9:
                _scramble(window, False, config.SCRAMBLE_KEY_FOR_F9, None, False)

            case key._2 | key._3 | key._4 | key._5 | key._6 | key._7 | key._8 | key._9:

                # print(f"{modifiers & key.MOD_CTRL=}  {modifiers & key.MOD_ALT=}")
                if modifiers & key.MOD_CTRL:
                    # noinspection PyProtectedMember
                    big_alg: algs.SeqAlg = Algs.scramble(app.cube.size, value - key._0)
                    good = algs.SeqAlg("good")
                    for a in big_alg.algs:
                        try:
                            with _wait_cursor(window):
                                op.play(a, animation=False)
                            good = good + a
                        except:
                            from .model.cube_queries import CubeQueries
                            cube.cqr.print_dist()
                            print("Failed on", a)
                            print(good)
                            raise
                elif modifiers & key.MOD_ALT:
                    print("Rerunning good:", good)
                    for a in good.algs:
                        try:
                            with _wait_cursor(window):
                                op.play(a, animation=False)
                            from .model.cube_queries import CubeQueries
                            cube.cqr.print_dist()
                        except:
                            print(good)
                            raise

                else:
                    # to match test int
                    # noinspection PyProtectedMember
                    alg = Algs.scramble(app.cube.size, value - key._0)
                    with _wait_cursor(window):
                        op.play(alg, inv, animation=False)

            case key.COMMA:

                # unod doesn't support None, it can oly dsibale global animation
                _animation = solver_animation is not False

                op.undo(animation=_animation)

            case key.SLASH:
                # solution = slv.solution().simplify()
                # op.play(solution)
                slv.solve(animation=solver_animation)

            case key.F1:
                if modifiers & key.MOD_CTRL:
                    slv.solve(what=SolveStep.L1x, animation=solver_animation)
                else:
                    slv.solve(what=SolveStep.L1, animation=solver_animation)

            case key.F2:
                slv.solve(what=SolveStep.L2, animation=solver_animation)

            case key.F3:

                if modifiers & key.MOD_CTRL:
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
                    _last_test_key, last_test_size = vs.get_last_scramble_test()
                    _run_test(window, _last_test_key, last_test_size, True, animation=solver_animation)
                elif modifiers & key.MOD_CTRL:
                    _last_test_key, last_test_size = vs.get_last_scramble_test()
                    _scramble(window, inv, _last_test_key, last_test_size, False)
                else:

                    with _wait_cursor(window):
                        app.run_tests(1, config.TEST_NUMBER_OF_SCRAMBLE_ITERATIONS)

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


def _scramble(window: AbstractWindow, _inv: bool, _scramble_key: Any, _n=None, _animation=False):
    app = window.app
    op = window.app.op

    op.reset()

    _alg = Algs.scramble(app.cube.size, _scramble_key, _n)

    print(f"Running scramble, key={_scramble_key}, n={_n}, alg={_alg}")

    with _wait_cursor(window):
        op.play(_alg, _inv, animation=_animation)


def _run_test(window: AbstractWindow, scramble_key,
              scramble_size, debug: bool,
              animation):
    app = window.app

    with _wait_cursor(window):
        app.run_single_test(scramble_key, scramble_size, debug, animation)


@contextmanager
def _wait_cursor(window: AbstractWindow):
    cursor = window.get_system_mouse_cursor(window.CURSOR_WAIT)
    window.set_mouse_cursor(cursor)
    try:  # test
        yield None

    finally:
        window.set_mouse_cursor(None)
