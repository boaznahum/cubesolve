"""
GUITestTimeout - Exception raised when a GUI test exceeds its timeout.
"""


class GUITestTimeout(Exception):
    """
    Exception raised when a GUI test exceeds its timeout.

    This exception is raised by the test runner when a test does not complete
    within the specified timeout period.
    """
    pass
