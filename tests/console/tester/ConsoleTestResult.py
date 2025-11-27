"""Result class for console tests."""

from dataclasses import dataclass


@dataclass
class ConsoleTestResult:
    """Result of a console test run."""
    success: bool
    message: str = ""
    error: Exception | None = None
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
