"""
Cube Solver Testing Framework.

This module provides backend-agnostic testing utilities that work with
all GUI backends (pyglet, tkinter, console, headless).
"""

from cube.testing.TestRunner import TestRunner, TestResult
from cube.testing.TestSequences import TestSequences

__all__ = ["TestRunner", "TestResult", "TestSequences"]
