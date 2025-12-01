from contextlib import contextmanager
from typing import Any

from cube.app.app_state import ApplicationAndViewState
from cube import algs
from cube import config
from cube.algs import Alg, Algs
from cube.app.abstract_ap import AbstractApp
from cube.app.app_exceptions import AppExit
from .main_g_abstract import AbstractWindow
from cube.model.cube_boy import FaceName
from cube.operator.cube_operator import Operator
from cube.solver import Solver, SolveStep
from cube.gui.types import Keys, Modifiers

good = Algs.seq_alg("good")


def handle_keyboard_input(window: AbstractWindow, value: int, modifiers: int):
    # print(f"{hex(value)}=")
    done = False
    app: AbstractApp = window.app
    op: Operator = app.op
    vs: ApplicationAndViewState = app.vs

    def debug(*_s):
        vs.debug(config.KEYBOAD_INPUT_DEBUG, "key board handler:", *_s)

    debug(f"In _handle_input , value:{value}  {hex(value)} "
          f"modifiers:{hex(modifiers)} ")

    # Skip if only modifier keys are pressed
    if Keys.LSHIFT <= value <= Keys.RMETA:
        debug(f"In _handle_input , Only modifiers, decided to quit")
        return

    cube = app.cube

    def handle_in_both_modes():
        """

        :return: (True if was handled, True no-op : no need redrawing)
        """
        match value:

            case Keys.SPACE:
                if modifiers & Modifiers.CTRL:
                    vs.single_step_mode = not vs.single_step_mode
                else:
                    vs.paused_on_single_step_mode = None

                return True, False

            case Keys.NUM_ADD:
                vs.inc_speed()
                return True, False

            case Keys.NUM_SUBTRACT:
                vs.dec_speed()
                return True, False

            case Keys.X:
                if modifiers & Modifiers.CTRL:
                    vs.alpha_x -= vs.alpha_delta
                    return True, True

                elif modifiers & Modifiers.ALT:
                    vs.alpha_x += vs.alpha_delta
                    return True, True

            case Keys.Y:
                if modifiers & Modifiers.CTRL:
                    vs.alpha_y -= vs.alpha_delta
                    return True, True
                elif modifiers & Modifiers.ALT:
                    vs.alpha_y += vs.alpha_delta
                    return True, True

            case Keys.Z:
                if modifiers & Modifiers.CTRL:
                    vs.alpha_z -= vs.alpha_delta
                    return True, True
                elif modifiers & Modifiers.ALT:
                    vs.alpha_z += vs.alpha_delta
                    return True, True

            case Keys.UP:
                if modifiers & Modifiers.CTRL:
                    vs.dec_fov_y()  # zoom in
                    vs.set_projection(window.width, window.height, window.renderer)
                    return True, True
                else:
                    vs.change_offset(0, 1, 0)
                    return True, True

            case Keys.DOWN:
                if modifiers & Modifiers.CTRL:
                    vs.inc_fov_y()  # zoom out
                    vs.set_projection(window.width, window.height, window.renderer)
                    return True, True
                else:
                    vs.change_offset(0, -1, 0)
                    return True, True

            case Keys.UP:
                if modifiers & Modifiers.CTRL:
                    vs.dec_fov_y()  # zoom in
                    vs.set_projection(window.width, window.height, window.renderer)
                    return True, True
                elif modifiers == 0:
                    vs.change_offset(0, 1, 0)
                    return True, True

            case Keys.DOWN:
                if modifiers & Modifiers.CTRL:
                    vs.inc_fov_y()  # zoom out
                    vs.set_projection(window.width, window.height, window.renderer)
                    return True, True
                elif modifiers == 0:
                    vs.change_offset(0, -1, 0)
                    return True, True

            case Keys.RIGHT:
                if modifiers == 0:
                    vs.change_offset(1, 0, 0)
                    return True, True

            case Keys.LEFT:
                if modifiers == 0:
                    vs.change_offset(-1, 0, 0)
                    return True, True

            case Keys.C:
                if modifiers & Modifiers.ALT:
                    app.vs.reset()
                    app.vs.set_projection(window.width, window.height, window.renderer)
                    return True, True

            case Keys.F10:
                vs.toggle_shadows_mode(FaceName.L)
                window.viewer.reset()
                return True, False
            case Keys.F11:
                vs.toggle_shadows_mode(FaceName.D)
                window.viewer.reset()
                return True, False
            case Keys.F12:
                vs.toggle_shadows_mode(FaceName.B)
                window.viewer.reset()
                return True, False

            case Keys.BACKSLASH:
                app.switch_to_next_solver()
                op.reset()
                return True, False

        return False, None

    no_operation: Any = False

    if window.animation_running or op.is_animation_running:

        debug(f"Keyboard input, in animation mode")

        handled, _no_operation = handle_in_both_modes()

        debug(f"Handled by 'handle_in_both_modes()={handled}, {_no_operation=}")

        if handled:

            no_operation = _no_operation

        else:
            #
            # print(f"{value==Keys.S}")
            match value:

                case Keys.Q:
                    op.abort()  # solver will not try to check state
                    window.close()
                    raise AppExit

                case Keys.S:
                    vs.single_step_mode_stop_pressed = True
                    op.abort()

        if not no_operation:
            debug("keyboard input 'animation mode' decide to update_gui_elements")
            window.update_gui_elements()
        else:
            debug("keyboard input 'animation mode' decide not to update_gui_elements")

        return False

    slv: Solver = app.slv

    inv = modifiers & Modifiers.SHIFT

    alg: Alg

    def _slice_alg(r: algs.SliceAbleAlg):
        return vs.slice_alg(app.cube, r)

    global good
    # noinspection PyProtectedMember

    handled, no_operation = handle_in_both_modes()

    debug(f"keyboard input 'main' handle_in_both_modes return {handled=} {no_operation}")

    if not handled:

        no_operation = False

        solver_animation = False if (modifiers & Modifiers.SHIFT) else None

        # operator animation doesn't support turn on, it can only turn off
        op_animation = solver_animation is not False

        # noinspection PyProtectedMember
        match value:

            case Keys.I:
                vs.debug(True, f"{vs.alpha_x + vs.alpha_x_0=} {vs.alpha_y+vs.alpha_y_0=} {vs.alpha_z+vs.alpha_z_0=}")
                no_operation = True
                cube.cqr.print_dist()

            case Keys.W:
                app.cube.front.corner_top_right.annotate(False)
                app.cube.front.corner_top_left.annotate(True)
                op.play(Algs.AN)

            case Keys.P:

                if modifiers & Modifiers.CTRL:
                    recording = op.toggle_recording()
                    if recording is not None:  # recording stopped
                        vs.last_recording = recording

                elif modifiers & Modifiers.ALT:
                    vs.last_recording = None

                else:
                    recording = vs.last_recording
                    if recording is not None:
                        op.play_seq(recording, inv)

            case Keys.O:
                if modifiers & Modifiers.CTRL:
                    # todo: Don't modify config, see also in solver, directly use config
                    config.SOLVER_DEBUG = not config.SOLVER_DEBUG
                elif modifiers & Modifiers.ALT:
                    config.CHECK_CUBE_SANITY = not config.CHECK_CUBE_SANITY
                else:
                    op.toggle_animation_on()

            case Keys.EQUAL:
                app.vs.cube_size += 1
                app.cube.reset(app.vs.cube_size)
                op.reset()
                window.viewer.reset()

            case Keys.MINUS:
                if vs.cube_size > 3:
                    app.vs.cube_size -= 1
                app.cube.reset(app.vs.cube_size)
                op.reset()
                window.viewer.reset()

            case Keys.BRACKETLEFT:
                if modifiers and Modifiers.ALT:
                    vs.slice_start = vs.slice_stop = 0

                elif modifiers and Modifiers.SHIFT:
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

            case Keys.BRACKETRIGHT:
                if modifiers and Modifiers.SHIFT:
                    vs.slice_stop -= 1
                    if vs.slice_stop < vs.slice_start:
                        vs.slice_stop = vs.slice_start
                else:
                    vs.slice_stop += 1
                    if vs.slice_stop > app.cube.size:
                        vs.slice_stop = app.cube.size

            case Keys.A:

                nn = cube.n_slices

                mid = 1 + nn // 2  # == 3 on 5

                end = nn

                #  https://speedcubedb.com/a/6x6/6x6L2E
                # 3R' U2 3L F2 3L' F2 3R2 U2 3R U2 3R' U2 F2 3R2 F2

                slices = [ 2, 4,5 ]

                # noinspection PyPep8Naming
                Rs = Algs.R[slices]
                # noinspection PyPep8Naming
                Ls = Algs.L[slices]

                # noinspection PyPep8Naming
                U = Algs.U
                # noinspection PyPep8Naming
                F = Algs.F

                alg = Rs.prime + U*2 + Ls + F*2 + Ls.prime + F*2 + Rs*2 + U*2 + Rs + U*2+Rs.p + U*2 + F*2
                alg += Rs*2 + F*2

                op.play(alg, inv, op_animation)


            case Keys.R:
                if modifiers & Modifiers.CTRL:
                    op.play(algs.Algs.Rw, inv)
                else:
                    op.play(_slice_alg(algs.Algs.R), inv)

            case Keys.L:
                if modifiers & Modifiers.CTRL:
                    op.play(algs.Algs.Lw, inv)
                else:
                    op.play(_slice_alg(algs.Algs.L), inv)

            case Keys.U:
                if modifiers & Modifiers.CTRL:
                    op.play(algs.Algs.Uw, inv)
                else:
                    op.play(_slice_alg(algs.Algs.U), inv)

            case Keys.F:
                if modifiers & Modifiers.CTRL:
                    op.play(algs.Algs.Fw, inv)
                else:
                    op.play(_slice_alg(algs.Algs.F), inv)

            case Keys.S:
                op.play(_slice_alg(algs.Algs.S), inv)

            case Keys.B:
                if modifiers & Modifiers.CTRL:
                    op.play(algs.Algs.Bw, inv)
                else:
                    op.play(_slice_alg(algs.Algs.B), inv)

            case Keys.D:
                _last_face = FaceName.D
                if modifiers & Modifiers.CTRL:
                    op.play(algs.Algs.Dw, inv)
                else:
                    op.play(_slice_alg(algs.Algs.D), inv)

            case Keys.X:  # Alt/Ctrl was handled in both
                if not modifiers & (Modifiers.CTRL | Modifiers.ALT):
                    op.play(algs.Algs.X, inv)

            case Keys.M:
                op.play(_slice_alg(algs.Algs.M), inv)

            case Keys.Y:
                # Alt/Ctrl was handled in both
                if not modifiers & (Modifiers.CTRL | Modifiers.ALT):
                    op.play(algs.Algs.Y, inv)

            case Keys.E:
                op.play(_slice_alg(algs.Algs.E), inv)

            case Keys.Z:
                # Alt/Ctrl was handled in both
                if not modifiers & (Modifiers.CTRL | Modifiers.ALT):
                    op.play(algs.Algs.Z, inv)

            case Keys.C:

                if not (modifiers & Modifiers.ALT):
                    app.reset()
                if modifiers and Modifiers.CTRL:
                    app.vs.reset()
                    app.vs.set_projection(window.width, window.height, window.renderer)

            case Keys._0:
                if modifiers & (Modifiers.SHIFT | Modifiers.ALT):
                    with vs.w_animation_speed(4):
                        if modifiers & Modifiers.ALT:
                            # Failed on [5:5]B
                            # [{good} [3:3]R [3:4]D S [2:2]L]

                            alg = Algs.R[3:3] + Algs.D[3:4] + Algs.S + Algs.L[2:2]  # + Algs.B[5:5]
                            op.play(alg, inv)

                        else:
                            alg = Algs.B[5:5]
                            op.play(alg, inv)
                else:
                    # same as Test 0
                    scramble_key = value - Keys._0
                    alg = Algs.scramble(app.cube.size, scramble_key)

                    with _wait_cursor(window):
                        op.play(alg, inv, animation=False)

            case Keys._1:

                _scramble_key = None
                _scramble_n = None

                if modifiers & (Modifiers.SHIFT | Modifiers.ALT):
                    if modifiers and Modifiers.SHIFT:  # test -1
                        _scramble_key = -1
                    else:
                        _scramble_key = value - Keys._0

                    _scramble_n = 5
                else:
                    # same as Test 1
                    _scramble_key = value - Keys._0

                animation = modifiers & Modifiers.CTRL

                _scramble(window, inv, _scramble_key, _scramble_n, animation)

            case Keys.F9:
                _scramble(window, False, config.SCRAMBLE_KEY_FOR_F9, None, False)

            case Keys._2 | Keys._3 | Keys._4 | Keys._5 | Keys._6 | Keys._7 | Keys._8 | Keys._9:

                # print(f"{modifiers & Modifiers.CTRL=}  {modifiers & Modifiers.ALT=}")
                if modifiers & Modifiers.CTRL:
                    # noinspection PyProtectedMember
                    seq_length = None
                    big_alg: algs.SeqAlg = Algs.scramble(app.cube.size, value - Keys._0, seq_length)
                    # print("Running alg:", [*big_alg.algs])
                    # print("Simplified: ", [*big_alg.simplify().algs])

                    good = algs.SeqAlg("good")

                    for a in big_alg.algs:
                        try:
                            with _wait_cursor(window):
                                op.play(a, animation=True)
                            good = good + a
                        except:
                            cube.cqr.print_dist()
                            print("Failed on", a)
                            print(good)
                            raise
                elif modifiers & Modifiers.ALT:
                    vs.debug(True, "Rerunning good:", good)
                    for a in good.algs:
                        try:
                            with _wait_cursor(window):
                                op.play(a, animation=False)
                            cube.cqr.print_dist()
                        except:
                            print(good)
                            raise

                else:
                    # to match test int
                    # noinspection PyProtectedMember
                    # alg = Algs.scramble(app.cube.size, value - Keys._0)
                    with _wait_cursor(window):
                        app.scramble(value - Keys._0, None, animation=False, verbose=True)
                        # op.play(alg, inv, animation=False)

            case Keys.COMMA:

                # undo doesn't support None, it can oly disable global animation
                _animation = solver_animation is not False

                op.undo(animation=_animation)

            case Keys.SLASH:
                # solution = slv.solution().simplify()
                # op.play(solution)
                slv.solve(animation=solver_animation)

            case Keys.F1:
                if modifiers & Modifiers.CTRL:
                    slv.solve(what=SolveStep.L1x, animation=solver_animation)
                else:
                    slv.solve(what=SolveStep.L1, animation=solver_animation)

            case Keys.F2:
                slv.solve(what=SolveStep.L2, animation=solver_animation)

            case Keys.F3:

                if modifiers & Modifiers.CTRL:
                    slv.solve(what=SolveStep.L3x, animation=solver_animation)
                else:
                    slv.solve(what=SolveStep.L3, animation=solver_animation)

            case Keys.F4:

                slv.solve(what=SolveStep.NxNCenters, animation=solver_animation)

            case Keys.F5:

                n0 = op.count
                slv.solve(what=SolveStep.NxNEdges, animation=solver_animation)
                window._last_edge_solve_count = op.count - n0

            case Keys.T:
                if modifiers & Modifiers.ALT:
                    _last_test_key, last_test_size = vs.get_last_scramble_test()
                    _run_test(window, _last_test_key, last_test_size, config.SOLVER_DEBUG, animation=solver_animation)
                elif modifiers & Modifiers.CTRL:
                    _last_test_key, last_test_size = vs.get_last_scramble_test()
                    _scramble(window, inv, _last_test_key, last_test_size, False)
                else:

                    with _wait_cursor(window):
                        app.run_tests(1, config.TEST_NUMBER_OF_SCRAMBLE_ITERATIONS)

            case Keys.Q:
                window.close()
                return

            case _:
                return False

    # no need to redraw, on_draw is called after any event

    if not no_operation:
        debug("keyboard input main decide to update gui elements")
        window.update_gui_elements()
    else:
        debug("keyboard input main decide not to update gui elements")

    return done


def _scramble(window: AbstractWindow, inv: Any, _scramble_key: Any, _n=None, _animation: Any = False):
    """

    :param window:
    :param inv: an object converted to bool
    :param _scramble_key:
    :param _n:
    :param _animation:
    :return:
    """
    app = window.app
    # op = window.app.op
    #
    # op.reset()
    #
    # _alg = Algs.scramble(app.cube.size, _scramble_key, _n)
    #
    # print(f"Running scramble, key={_scramble_key}, n={_n}, alg={_alg}")

    with _wait_cursor(window):
        app.scramble(_scramble_key, _n, animation=_animation)
        #op.play(_alg, _inv, animation=_animation)


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
