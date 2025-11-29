"""
Cube Solver Testing Framework.

This module provides backend-agnostic testing utilities that work with
all GUI backends (pyglet, tkinter, console, headless).
"""

from cube.testing.test_runner import TestRunner, TestResult
from cube.testing.test_sequences import TestSequences

__all__ = ["TestRunner", "TestResult", "TestSequences"]
