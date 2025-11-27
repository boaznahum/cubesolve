"""
Main entry point for the GUI application.

This file decides which backend to use. Currently defaults to pyglet.
To add support for other backends (e.g., tkinter), create a main_tkinter.py
and update this file to select based on command-line arguments or config.
"""
from cube import main_pyglet


if __name__ == '__main__':
    # Default to pyglet backend
    main_pyglet.main()
