"""
Pyglet AppWindow implementation.

Provides the pyglet-specific AppWindow that inherits from pyglet.window.Window
and uses AppWindowBase for shared logic.
"""

import traceback

try:
    import pyglet
    from pyglet import gl
except ImportError as e:
    raise ImportError("pyglet is required: pip install pyglet") from e

from cube import config
from cube.app.abstract_ap import AbstractApp
from cube.app.app_exceptions import AppExit, RunStop, OpAborted
from cube.animation.animation_manager import AnimationWindow
from cube.gui.factory import GUIBackend
from cube.gui.backends.pyglet.window import _PYGLET_TO_KEYS, _convert_modifiers, _convert_mouse_buttons
from cube.main_window import main_g_keyboard_input, main_g_mouse
from cube.main_window.app_window_base import AppWindowBase, TextLabel
from cube.viewer.viewer_g import GCubeViewer
from cube.viewer.viewer_g_ext import GViewerExt


class PygletAppWindow(pyglet.window.Window, AnimationWindow):
    """Pyglet-specific AppWindow implementation.

    Implements the AppWindow protocol (verified via @runtime_checkable).
    Combines pyglet.window.Window for rendering/events with AnimationWindow
    for animation support.

    Note: Cannot inherit from AppWindow Protocol due to metaclass conflict
    with pyglet.window.Window. Protocol compliance is runtime-checked.
    """

    def __init__(
        self,
        app: AbstractApp,
        width: int,
        height: int,
        title: str,
        backend: GUIBackend,
    ):
        """Initialize the Pyglet AppWindow.

        Args:
            app: Application instance (cube, operator, solver)
            width: Window width in pixels
            height: Window height in pixels
            title: Window title
            backend: GUI backend for rendering
        """
        # Store app before super().__init__() because pyglet triggers on_resize
        self._app = app
        self._vs = app.vs
        self._backend = backend
        self._renderer = backend.renderer

        # Initialize pyglet window
        super().__init__(width, height, title, resizable=True)

        # Animation manager connection
        self._animation_manager = app.am
        if self._animation_manager:
            self._animation_manager.set_window(self)

        # Initialize renderer
        self._renderer.setup()
        gl.glEnable(gl.GL_DEPTH_TEST)

        # Create viewer
        self._viewer = GCubeViewer(app.cube, app.vs, renderer=self._renderer)

        # Text labels (built by _update_status_text/_update_animation_text)
        self._status_labels: list[TextLabel] = []
        self._animation_labels: list[TextLabel] = []
        self.text: list[pyglet.text.Label] = []
        self.animation_text: list[pyglet.text.Label] = []

        # Initial GUI update
        self.update_gui_elements()

    @property
    def app(self) -> AbstractApp:
        """Access the application instance."""
        return self._app

    @property
    def viewer(self) -> GCubeViewer:
        """Access the cube viewer."""
        return self._viewer

    @property
    def renderer(self):
        """Access the renderer."""
        return self._renderer

    @property
    def animation_running(self) -> bool:
        """Check if animation is currently running."""
        return bool(self._animation_manager and self._animation_manager.animation_running())

    def run(self) -> None:
        """Run the main event loop."""
        self._backend.event_loop.run()

    def update_gui_elements(self) -> None:
        """Update all GUI elements."""
        self._viewer.update()

        if self._animation_manager:
            self._animation_manager.update_gui_elements()

        self._update_animation_text()

        if not self.animation_running:
            self._update_status_text()

    def _request_redraw(self) -> None:
        """Request window redraw."""
        # Pyglet handles this automatically via on_draw
        pass

    # === Pyglet Event Handlers ===

    def on_draw(self):
        """Pyglet draw event."""
        if self._vs.skip_next_on_draw:
            self._vs.skip_next_on_draw = False
            return

        self.clear()
        self._draw_axis()
        self._viewer.draw()
        self._draw_text()
        self._draw_animation()

    def on_resize(self, width, height):
        """Pyglet resize event."""
        gl.glViewport(0, 0, width, height)
        self._app.vs.set_projection(width, height, self._renderer)

    def on_key_press(self, symbol, modifiers):
        """Pyglet key press event."""
        try:
            abstract_symbol = _PYGLET_TO_KEYS.get(symbol, symbol)
            abstract_mods = _convert_modifiers(modifiers)
            main_g_keyboard_input.handle_keyboard_input(self, abstract_symbol, abstract_mods)

        except (AppExit, RunStop, OpAborted) as e:
            if config.GUI_TEST_MODE and isinstance(e, AppExit):
                self.close()
                raise
            else:
                self._app.set_error("Asked to stop")
                self.update_gui_elements()

        except Exception as e:
            if config.GUI_TEST_MODE and config.QUIT_ON_ERROR_IN_TEST_MODE:
                self.close()
                raise
            else:
                traceback.print_exc()
                msg = str(e)
                self._app.set_error(f"Error: {msg}" if msg else "Error occurred")
                self.update_gui_elements()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """Pyglet mouse drag event."""
        abstract_buttons = _convert_mouse_buttons(buttons)
        abstract_mods = _convert_modifiers(modifiers)
        return main_g_mouse.on_mouse_drag(self, x, y, dx, dy, abstract_buttons, abstract_mods)

    def on_mouse_press(self, x, y, button, modifiers):
        """Pyglet mouse press event."""
        abstract_mods = _convert_modifiers(modifiers)
        return main_g_mouse.on_mouse_press(self, self._app.vs, x, y, abstract_mods)

    def on_mouse_release(self, x, y, button, modifiers):
        """Pyglet mouse release event."""
        return main_g_mouse.on_mouse_release()

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """Pyglet mouse scroll event."""
        return main_g_mouse.on_mouse_scroll(self, scroll_y)

    # === Key Injection ===

    def inject_key(self, key: int, modifiers: int = 0) -> None:
        """Inject a single key press."""
        self.on_key_press(key, modifiers)

    def inject_key_sequence(self, sequence: str, process_events: bool = True) -> None:
        """Inject a sequence of key presses."""
        from pyglet.window import key

        char_map = {
            '0': key._0, '1': key._1, '2': key._2, '3': key._3, '4': key._4,
            '5': key._5, '6': key._6, '7': key._7, '8': key._8, '9': key._9,
            'R': key.R, 'L': key.L, 'U': key.U, 'D': key.D, 'F': key.F, 'B': key.B,
            'r': key.R, 'l': key.L, 'u': key.U, 'd': key.D, 'f': key.F, 'b': key.B,
            '/': key.SLASH, '?': key.SLASH,
            'q': key.Q, 'Q': key.Q,
            ' ': key.SPACE,
            ',': key.COMMA, '<': key.COMMA,
            '+': key.NUM_ADD, '-': key.NUM_SUBTRACT,
        }

        for char in sequence:
            symbol = char_map.get(char)
            if symbol is not None:
                self.on_key_press(symbol, 0)
                if process_events:
                    pyglet.app.platform_event_loop.step(0.0)

    # === Text Rendering ===

    def _update_status_text(self) -> None:
        """Build status text labels."""
        from cube.algs import Algs

        app = self._app
        slv = app.slv
        cube = app.cube
        vs = app.vs
        op = app.op

        def _b(b: bool) -> str:
            return "On" if b else "Off"

        self.text.clear()
        y = 10

        self.text.append(pyglet.text.Label(f"Status:{slv.status}", x=10, y=y, font_size=10))
        y += 20

        h = Algs.simplify(*op.history(remove_scramble=True))
        self.text.append(pyglet.text.Label(
            f"History(simplified): #{h.count()}  {str(h)[-120:]}", x=10, y=y, font_size=10
        ))
        y += 20

        hist = op.history()
        self.text.append(pyglet.text.Label(
            f"History: #{Algs.count(*hist)}  {str(h)[-70:]}", x=10, y=y, font_size=10
        ))
        y += 20

        s = f"Recording: {_b(op.is_recording)}"
        if vs.last_recording:
            s += f", #{Algs.count(*vs.last_recording)}  {str(vs.last_recording)[-70:]}"
        self.text.append(pyglet.text.Label(s, x=10, y=y, font_size=10))
        y += 20

        self.text.append(pyglet.text.Label(
            "R L U S/Z/F B D  M/X/R E/Y/U (SHIFT-INv), ?-Solve, Clear, Q 0-9 scramble, <undo",
            x=10, y=y, font_size=10
        ))
        y += 20

        s = f"Sanity:{cube.is_sanity(force_check=True)}"
        if app.error:
            s += f", Error:{app.error}"
        self.text.append(pyglet.text.Label(s, x=10, y=y, font_size=10, color=(255, 0, 0, 255), bold=True))
        y += 20

        s = f"Animation:{_b(op.animation_enabled)}, [{vs.get_speed_index}] {vs.get_speed.get_speed()}"
        s += f", Sanity check:{_b(config.CHECK_CUBE_SANITY)}, Debug={_b(slv.is_debug_config_mode)}"
        s += f", SS Mode:{_b(vs.single_step_mode)}"
        self.text.append(pyglet.text.Label(s, x=10, y=y, font_size=10, color=(255, 255, 0, 255), bold=True))
        y += 20

        s = f"Solver:{slv.name}, S={cube.size}, Is 3x3:{'Yes' if cube.is3x3 else 'No'}"
        s += f", Slices  [{vs.slice_start}, {vs.slice_stop}]"
        s += f", {vs.slice_alg(cube, Algs.L)}, {vs.slice_alg(cube, Algs.M)}"
        self.text.append(pyglet.text.Label(s, x=10, y=y, font_size=10, color=(0, 255, 0, 255), bold=True))
        y += 20

        if vs.paused_on_single_step_mode:
            self.text.append(pyglet.text.Label(
                f"PAUSED: {vs.paused_on_single_step_mode}. press space",
                x=10, y=y, font_size=15, color=(0, 255, 0, 255), bold=True
            ))

    def _update_animation_text(self) -> None:
        """Build animation text labels."""
        vs = self._app.vs
        self.animation_text.clear()

        at = vs.animation_text
        for i in range(3):
            prop = config.ANIMATION_TEXT[i]
            line = at.get_line(i)
            if line:
                x = prop[0]
                y = self.height - prop[1]
                size = prop[2]
                color = prop[3]
                bold = prop[4]
                self.animation_text.append(pyglet.text.Label(
                    line, x=x, y=y, font_size=size, color=color, bold=bold
                ))

    def _draw_axis(self) -> None:
        """Draw the reference axis."""
        GViewerExt.draw_axis(self._app.vs, self._renderer)

    def _draw_text(self) -> None:
        """Draw text labels with OpenGL orthographic projection."""
        gl.glPushAttrib(gl.GL_TRANSFORM_BIT)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glOrtho(0, self.width, 0, self.height, -1.0, 1.0)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()

        for t in self.text:
            t.draw()
        for t in self.animation_text:
            t.draw()

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glPopAttrib()

    def _draw_animation(self) -> None:
        """Draw animation frame."""
        if self._animation_manager:
            self._animation_manager.draw()
