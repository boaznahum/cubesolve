"""
Pyglet AppWindow implementation.

Provides the pyglet-specific AppWindow that inherits from pyglet.window.Window
and uses AppWindowBase for shared logic.
"""

try:
    import pyglet
    from pyglet import gl
except ImportError as e:
    raise ImportError("pyglet2 backend requires: pip install 'pyglet>=2.0'") from e

from cube.application import config
from cube.application.AbstractApp import AbstractApp
from cube.application.exceptions.app_exceptions import AppExit
from cube.application.animation.AnimationManager import AnimationWindow
from cube.presentation.gui.factory import GUIBackend
from cube.presentation.gui.backends.pyglet2.PygletWindow import _PYGLET_TO_KEYS, _convert_modifiers, _convert_mouse_buttons
from cube.presentation.gui.backends.pyglet2 import main_g_mouse
from cube.presentation.gui.backends.pyglet2.AppWindowBase import AppWindowBase, TextLabel
from cube.presentation.gui.backends.pyglet2.ModernGLRenderer import ModernGLRenderer
from cube.presentation.gui.Command import Command, CommandContext
from cube.presentation.gui.key_bindings import lookup_command
from cube.presentation.viewer.GCubeViewer import GCubeViewer
from cube.presentation.viewer.GViewerExt import GViewerExt


class PygletAppWindow(pyglet.window.Window, AnimationWindow):
    """Pyglet-specific AppWindow implementation (AppWindow protocol).

    Combines pyglet.window.Window for rendering/events with AnimationWindow
    for animation support.

    Note: Cannot inherit from AppWindow protocol due to metaclass conflict
    with pyglet.window.Window. Protocol compliance is verified at runtime
    via @runtime_checkable.
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

        # Initialize to None - will be set after super().__init__()
        # (pyglet calls on_resize during __init__ before we can create the renderer)
        self._modern_renderer: ModernGLRenderer | None = None

        # Initialize pyglet window (uses OpenGL 3.3 core profile on pyglet 2.0)
        super().__init__(width, height, title, resizable=True)

        # Animation manager connection
        self._animation_manager = app.am
        if self._animation_manager:
            self._animation_manager.set_window(self)

        # Initialize modern GL renderer (replaces legacy GL rendering)
        self._modern_renderer = ModernGLRenderer()
        self._modern_renderer.setup()
        gl.glEnable(gl.GL_DEPTH_TEST)

        # Set up perspective projection
        self._modern_renderer.set_perspective(width, height, fov_y=45.0, near=0.1, far=100.0)

        # Create viewer
        # TODO: GCubeViewer uses legacy display lists - needs migration to modern GL
        # For now, viewer is disabled to test axis rendering
        self._viewer: GCubeViewer | None = None
        # self._viewer = GCubeViewer(app.cube, app.vs, renderer=self._renderer)

        # Text labels (built by _update_status_text/_update_animation_text)
        self._status_labels: list[TextLabel] = []
        self._animation_labels: list[TextLabel] = []
        self.text: list[pyglet.text.Label] = []
        self.animation_text: list[pyglet.text.Label] = []

        # State for keyboard handler (used by Command handlers)
        self._last_edge_solve_count: int = 0

        # Initial GUI update
        self.update_gui_elements()

    @property
    def app(self) -> AbstractApp:
        """Access the application instance."""
        return self._app

    @property
    def viewer(self) -> GCubeViewer | None:
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
        if self._viewer:
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
        import math

        if self._vs.skip_next_on_draw:
            self._vs.skip_next_on_draw = False
            return

        self.clear()

        # Set up view transform (camera position)
        vs = self._app.vs
        self._modern_renderer.load_identity()

        # Apply offset translation (camera distance)
        offset = vs.offset
        self._modern_renderer.translate(float(offset[0]), float(offset[1]), float(offset[2]))

        # Apply rotation (convert from radians to degrees)
        self._modern_renderer.rotate(math.degrees(vs.alpha_x_0), 1, 0, 0)
        self._modern_renderer.rotate(math.degrees(vs.alpha_y_0), 0, 1, 0)
        self._modern_renderer.rotate(math.degrees(vs.alpha_z_0), 0, 0, 1)

        # Draw axis using modern GL renderer
        self._modern_renderer.draw_axis(length=5.0)

        # Draw test cube to prove rendering works
        self._modern_renderer.draw_cube(size=50.0)

        # TODO: Modern GL migration in progress
        # Legacy GL calls disabled - they fail in OpenGL 3.3 core profile
        # self._viewer.draw()    # Uses glBegin/glEnd - needs migration
        # self._draw_animation() # Uses legacy GL - needs migration

        # Pyglet 2.0's label drawing uses modern GL internally
        for t in self.text:
            t.draw()
        for t in self.animation_text:
            t.draw()

    def on_resize(self, width, height):
        """Pyglet resize event."""
        gl.glViewport(0, 0, width, height)
        # Update projection for modern GL renderer (if initialized)
        if self._modern_renderer:
            self._modern_renderer.set_perspective(width, height, fov_y=45.0, near=0.1, far=100.0)

    def on_key_press(self, symbol, modifiers):
        """Pyglet native key press event.

        Called by pyglet framework. Converts native keys to abstract Keys
        and calls handle_key() - the protocol method.
        """
        abstract_symbol = _PYGLET_TO_KEYS.get(symbol, symbol)
        abstract_mods = _convert_modifiers(modifiers)
        self.handle_key(abstract_symbol, abstract_mods)

    def handle_key(self, symbol: int, modifiers: int) -> None:
        """Protocol method - handle abstract key press.

        Implements: `AppWindowBase.handle_key`

        Args:
            symbol: Key code (from Keys enum) - already converted to abstract
            modifiers: Modifier flags (from Modifiers)
        """
        cmd = lookup_command(symbol, modifiers, self.animation_running)
        if cmd:
            self.inject_command(cmd)

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

    def inject_command(self, command: Command) -> None:
        """Inject a command directly.

        Preferred method for testing and automation - bypasses key handling
        and directly executes the command. Type-safe with IDE autocomplete.

        Args:
            command: Command enum value to execute

        Example:
            window.inject_command(Command.SCRAMBLE_1)
            window.inject_command(Command.SOLVE_ALL)
            window.inject_command(Command.QUIT)
        """
        import traceback

        try:
            ctx = CommandContext.from_window(self)
            result = command.execute(ctx)
            if not result.no_gui_update:
                self.update_gui_elements()
        except AppExit:
            if config.GUI_TEST_MODE:
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
                error_text = "Some error occurred:"
                if msg:
                    error_text += msg
                self._app.set_error(error_text)
                self.update_gui_elements()

    # === Text Rendering ===

    def _update_status_text(self) -> None:
        """Build status text labels."""
        from cube.domain.algs import Algs

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
        self.text.append(pyglet.text.Label(s, x=10, y=y, font_size=10, color=(255, 0, 0, 255), weight='bold'))
        y += 20

        s = f"Animation:{_b(op.animation_enabled)}, [{vs.get_speed_index}] {vs.get_speed.get_speed()}"
        s += f", Sanity check:{_b(config.CHECK_CUBE_SANITY)}, Debug={_b(slv.is_debug_config_mode)}"
        s += f", SS Mode:{_b(vs.single_step_mode)}"
        self.text.append(pyglet.text.Label(s, x=10, y=y, font_size=10, color=(255, 255, 0, 255), weight='bold'))
        y += 20

        s = f"Solver:{slv.name}, S={cube.size}, Is 3x3:{'Yes' if cube.is3x3 else 'No'}"
        s += f", Slices  [{vs.slice_start}, {vs.slice_stop}]"
        s += f", {vs.slice_alg(cube, Algs.L)}, {vs.slice_alg(cube, Algs.M)}"
        self.text.append(pyglet.text.Label(s, x=10, y=y, font_size=10, color=(0, 255, 0, 255), weight='bold'))
        y += 20

        if vs.paused_on_single_step_mode:
            self.text.append(pyglet.text.Label(
                f"PAUSED: {vs.paused_on_single_step_mode}. press space",
                x=10, y=y, font_size=15, color=(0, 255, 0, 255), weight='bold'
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
                # pyglet 2.0 uses weight='bold' instead of bold=True
                weight = 'bold' if bold else 'normal'
                self.animation_text.append(pyglet.text.Label(
                    line, x=x, y=y, font_size=size, color=color, weight=weight
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
