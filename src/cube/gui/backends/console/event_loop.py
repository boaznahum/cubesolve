"""
Console event loop implementation.

Provides an input-based event loop for console mode.
"""

import sys
from typing import Callable

from cube.gui.protocols.event_loop import EventLoop


class ConsoleEventLoop(EventLoop):
    """Console event loop using keyboard/stdin input.

    In console mode, the event loop reads from keyboard or stdin
    and processes key presses until quit is requested.
    """

    def __init__(self) -> None:
        self._running = False
        self._key_handler: Callable[[str], bool] | None = None
        self._key_sequence: list[str] = []
        self._use_keyboard = True

    def set_key_handler(self, handler: Callable[[str], bool]) -> None:
        """Set the key press handler.

        Args:
            handler: Function that takes a key string and returns True to quit.
        """
        self._key_handler = handler

    def inject_sequence(self, sequence: str) -> None:
        """Inject a key sequence to be processed.

        Args:
            sequence: String of keys to inject.
        """
        self._key_sequence.extend(list(sequence))

    def set_use_keyboard(self, use: bool) -> None:
        """Enable or disable keyboard input.

        Args:
            use: If False, only injected sequences are processed.
        """
        self._use_keyboard = use

    def _get_input(self) -> str | None:
        """Get the next input key.

        Returns:
            The key string or None if no input available.
        """
        if self._key_sequence:
            return self._key_sequence.pop(0)

        if not self._use_keyboard:
            return None

        try:
            # Try keyboard library if available and running in a terminal
            if sys.stdin.isatty():
                try:
                    import keyboard
                    event = keyboard.read_event(suppress=True)
                    return event.name
                except ImportError:
                    pass

            # Fall back to input()
            value = input()
            if value:
                # If multiple characters, queue the rest
                if len(value) > 1:
                    self._key_sequence.extend(list(value[1:]))
                return value[0]

        except (EOFError, KeyboardInterrupt):
            return None

        return None

    def run(self) -> None:
        """Run the event loop until stopped."""
        self._running = True

        while self._running:
            key = self._get_input()

            if key is None:
                if not self._use_keyboard:
                    # No more input in sequence-only mode
                    break
                continue

            if self._key_handler:
                should_quit = self._key_handler(key.upper())
                if should_quit:
                    break

    def stop(self) -> None:
        """Stop the event loop."""
        self._running = False

    def schedule_once(self, callback: Callable[[], None], delay: float) -> None:
        """Schedule a callback - not supported in console mode.

        Args:
            callback: Function to call.
            delay: Delay in seconds.
        """
        # Console mode doesn't support scheduled callbacks
        # Just call immediately
        callback()

    def schedule_interval(
        self, callback: Callable[[float], bool | None], interval: float
    ) -> int:
        """Schedule a repeating callback - not supported in console mode.

        Args:
            callback: Function to call.
            interval: Interval in seconds.

        Returns:
            Schedule ID (always 0 in console mode).
        """
        # Console mode doesn't support intervals - no animation
        return 0

    def unschedule(self, schedule_id: int) -> None:
        """Unschedule a callback - no-op in console mode.

        Args:
            schedule_id: The schedule ID to cancel.
        """
        pass
