"""
Input handling package - Commands and keyboard event processing.

This package implements a command pattern with generator-based event processing
to enable both interactive GUI and automated testing.
"""

from .commands import Command, CommandResult, AppContext
from .keyboard_generator import keyboard_event_generator, KeyEvent

__all__ = [
    'Command',
    'CommandResult',
    'AppContext',
    'keyboard_event_generator',
    'KeyEvent',
]
