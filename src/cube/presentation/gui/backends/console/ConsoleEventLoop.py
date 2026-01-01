"""
Console event loop implementation.

Provides an input-based event loop for console mode.
"""

import sys
from typing import Callable

from cube.presentation.gui.protocols import EventLoop


class ConsoleEventLoop(EventLoop):
    """Console event loop using keyboard/stdin input.

    In console mode, the event loop reads from keyboard or stdin
    and processes key presses until quit is requested.
    """

    def __init__(self) -> None:
        self._running = False
        self._has_exit = False
        self._key_handler: Callable[[str], bool] | None = None
        self._key_sequence: list[str] = []
        self._use_keyboard = True

    @property
    def running(self) -> bool:
        """Whether the event loop is currently running."""
        return self._running

    @property
    def has_exit(self) -> bool:
        """Whether the event loop has been signaled to exit."""
        return self._has_exit

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
            # Read single key from THIS console only (not globally)
            # Windows: msvcrt, Linux: termios
            if sys.stdin.isatty():
                try:
                    # Windows
                    import msvcrt
                    ch = msvcrt.getwch()
                    return ch.upper()
                except ImportError:
                    # Linux/Unix - use termios for raw single-char input
                    import termios
                    import tty
                    fd = sys.stdin.fileno()
                    old_settings = termios.tcgetattr(fd)
                    try:
                        tty.setraw(fd)
                        ch = sys.stdin.read(1)
                        return ch.upper()
                    finally:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

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
        self._has_exit = True

    def schedule_once(self, callback: Callable[[float], None], delay: float) -> None:
        """Schedule a callback - not supported in console mode.

        Args:
            callback: Function receiving elapsed time since scheduling.
            delay: Delay in seconds.
        """
        # Console mode doesn't support scheduled callbacks
        # Just call immediately with 0 elapsed time
        callback(0.0)

    def schedule_interval(self, callback: Callable[[float], None], interval: float) -> None:
        """Schedule a repeating callback - not supported in console mode.

        Args:
            callback: Function receiving time since last call.
            interval: Interval in seconds.
        """
        # Console mode doesn't support intervals - no animation
        pass

    def unschedule(self, callback: Callable[[float], None]) -> None:
        """Unschedule a callback - no-op in console mode.

        Args:
            callback: Previously scheduled function to remove.
        """
        pass

    def call_soon(self, callback: Callable[[], None]) -> None:
        """Schedule a callback to run as soon as possible - calls immediately.

        Args:
            callback: Function to call (no arguments).
        """
        callback()

    def get_time(self) -> float:
        """Get current time in seconds.

        Returns:
            Time in seconds (monotonic).
        """
        import time
        return time.monotonic()

    def step(self, timeout: float = 0.0) -> bool:
        """Process pending events without blocking - no-op in console mode.

        Args:
            timeout: Maximum time to wait for events.

        Returns:
            False (no events processed in console mode).
        """
        return False

    def idle(self) -> float:
        """Process pending scheduled callbacks - no-op in console mode.

        Returns:
            0.0 (no pending callbacks).
        """
        return 0.0

    def notify(self) -> None:
        """Wake up the event loop - no-op in console mode."""
        pass
