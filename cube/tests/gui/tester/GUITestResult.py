"""
GUITestResult - Result object for GUI test execution.
"""


class GUITestResult:
    """
    Result of a GUI test run.

    Attributes
    ----------
    success : bool
        Whether the test passed.
    error : Exception | None
        Exception that occurred, if any.
    message : str
        Descriptive message about the test result.
    """

    def __init__(self, success: bool, error: Exception | None = None, message: str = ""):
        """
        Initialize test result.

        Parameters
        ----------
        success : bool
            Whether the test passed.
        error : Exception | None, optional
            Exception that occurred, if any.
        message : str, optional
            Descriptive message about the test result.
        """
        self.success = success
        self.error = error
        self.message = message

    def __str__(self):
        """String representation using ASCII characters for Windows console compatibility."""
        if self.success:
            return f"[PASS] Test passed: {self.message}"
        else:
            return f"[FAIL] Test failed: {self.message}\n  Error: {self.error}"
