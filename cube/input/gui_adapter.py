"""
GUI adapter for the command-based input system.

This module provides the integration layer between pyglet's event system
and the command generator. It can be used as a drop-in replacement for
the existing keyboard handler.
"""

from typing import TYPE_CHECKING

from cube.app.app_exceptions import AppExit
from .keyboard_generator import keyboard_event_generator, KeyEvent
from .commands import CommandResult

if TYPE_CHECKING:
    from cube.main_window.main_g_abstract import AbstractWindow


class KeyboardInputAdapter:
    """
    Adapter that integrates the command generator with pyglet's GUI.

    This replaces the monolithic handle_keyboard_input function with
    a cleaner command-based approach.

    Usage in Window.on_key_press:
        def on_key_press(self, symbol, modifiers):
            return self.input_adapter.handle_key_press(symbol, modifiers)
    """

    def __init__(self, window: 'AbstractWindow'):
        """
        Initialize the adapter.

        Args:
            window: The window this adapter handles input for
        """
        self.window = window

    def handle_key_press(self, symbol: int, modifiers: int) -> bool:
        """
        Handle a key press event.

        This is called by pyglet's on_key_press event handler.

        Args:
            symbol: The key symbol
            modifiers: Modifier keys pressed

        Returns:
            True if the key was handled, False otherwise
        """
        # Create a single key event
        event = KeyEvent(symbol, modifiers)

        # Check if animation is running
        animation_running = (
            self.window.animation_running or
            self.window.app.op.is_animation_running
        )

        # Generate commands from this event
        # (Generator will yield 0 or 1 commands for a single event)
        for cmd in keyboard_event_generator([event], animation_running):
            try:
                # Execute the command
                result = self._execute_command(cmd)

                # Handle result
                if result.should_quit:
                    return True

                if result.error:
                    # Could show error in GUI status bar
                    print(f"Command error: {result.error}")

                if result.needs_viewer_reset:
                    self.window.viewer.reset()

                if result.needs_redraw:
                    self.window.update_gui_elements()

                return True  # Key was handled

            except AppExit:
                # Quit command raises this
                raise

        # No command was generated for this key
        return False

    def _execute_command(self, cmd) -> CommandResult:
        """
        Execute a command with proper context.

        Args:
            cmd: The command to execute

        Returns:
            CommandResult from the command
        """
        # Create context wrapper that provides both app and window
        context = _AppContextWrapper(self.window.app, self.window)

        # Execute command
        return cmd.execute(context)


class _AppContextWrapper:
    """
    Wrapper that makes Window+App look like AppContext.

    This allows commands to access both app state and window,
    while tests can use just app (with window=None).
    """

    def __init__(self, app, window):
        self._app = app
        self._window = window

    @property
    def cube(self):
        return self._app.cube

    @property
    def op(self):
        return self._app.op

    @property
    def vs(self):
        return self._app.vs

    @property
    def slv(self):
        return self._app.slv

    @property
    def window(self):
        return self._window


def handle_keyboard_input_new(window: 'AbstractWindow', symbol: int, modifiers: int):
    """
    New keyboard handler using command pattern.

    This is a drop-in replacement for the old handle_keyboard_input function.
    It can be used to gradually migrate from the old system.

    Args:
        window: The window
        symbol: Key symbol
        modifiers: Modifier keys

    Usage:
        # In main_g_keyboard_input.py, replace:
        # def handle_keyboard_input(window, value, modifiers):
        # with:
        # from cube.input.gui_adapter import handle_keyboard_input_new
        # handle_keyboard_input = handle_keyboard_input_new
    """
    adapter = KeyboardInputAdapter(window)
    adapter.handle_key_press(symbol, modifiers)
