"""Sanity check helpers for LBL solver.

This module contains methods that verify solver correctness during execution.
All methods here are only used for debugging/validation, not core solving logic.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Generator

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.tracker._face_trackers import FaceTracker


class SanityChecker:
    """Helper class for LBL solver sanity checks.

    Provides methods to verify that previous rows remain solved during solving operations.
    Used to catch bugs where solving a new row accidentally corrupts already-solved rows.

    Attributes:
        cube: The cube being solved
        enabled: Whether sanity checks are enabled
    """

    __slots__ = ["cube", "enabled"]

    def __init__(self, cube: Cube, enabled: bool) -> None:
        """Create sanity checker.

        Args:
            cube: The cube being solved
            enabled: Whether sanity checks are enabled (from config.lbl_sanity_check)
        """
        self.cube = cube
        self.enabled = enabled

    def _format_piece_info(self, piece) -> str:
        """Format detailed information about a piece for debugging.

        Returns string like:
          CenterSlice @ idx=(3,7): expected=RED, actual=BLUE [face=F]
          EdgeWing @ idx=(2,5): expected=[RED,GREEN], actual=[BLUE,GREEN] [faces=F,R] (1/2 wrong)
        """
        from cube.domain.model.PartSlice import CenterSlice, EdgeWing

        # Determine piece type
        if isinstance(piece, CenterSlice):
            piece_type = "CenterSlice"
        elif isinstance(piece, EdgeWing):
            piece_type = "EdgeWing"
        else:
            piece_type = type(piece).__name__

        # Get index
        idx = piece.index if hasattr(piece, 'index') else "?"

        # Collect edge information
        edges = piece._edges
        expected_colors = [edge.face.color for edge in edges]
        actual_colors = [edge.color for edge in edges]
        face_names = [edge.face.name.name for edge in edges]

        # Count wrong edges
        wrong_count = sum(1 for exp, act in zip(expected_colors, actual_colors) if exp != act)

        # Format colors
        if len(edges) == 1:
            # Center slice - single color
            expected_str = f"{expected_colors[0].name}"
            actual_str = f"{actual_colors[0].name}"
            faces_str = f"face={face_names[0]}"
        else:
            # Edge wing - multiple colors
            expected_str = f"[{','.join(c.name for c in expected_colors)}]"
            actual_str = f"[{','.join(c.name for c in actual_colors)}]"
            faces_str = f"faces={','.join(face_names)}"

        # Build info string
        info = f"{piece_type} @ idx={idx}: expected={expected_str}, actual={actual_str} [{faces_str}]"

        if len(edges) > 1:
            info += f" ({wrong_count}/{len(edges)} wrong)"

        return info

    def _get_destroyed_pieces_in_row(self, l1_tracker: FaceTracker, face_row: int) -> list[tuple[object, str]]:
        """Get all unsolved pieces in a row with their details.

        Returns:
            List of (piece, formatted_info) tuples for pieces that don't match their faces
        """
        from cube.domain.solver.direct.lbl._common import _get_row_pieces

        destroyed: list[tuple[object, str]] = []
        for piece in _get_row_pieces(self.cube, l1_tracker, face_row):
            if not piece.match_faces:
                info = self._format_piece_info(piece)
                destroyed.append((piece, info))
        return destroyed

    def sanity_check_previous_are_solved(self, l1_tracker: FaceTracker, face_row: int, op_name: str,
                                         row_solved_checker) -> None:
        """Check that all previous rows are still solved.

        Args:
            l1_tracker: Layer 1 face tracker
            face_row: Distance from L1 face (0=closest, n_slices-1=farthest)
            op_name: Name of the operation (for error messages)
            row_solved_checker: Callable that takes (l1_tracker, face_row) and returns bool
        """
        if self.enabled:
            for prev_face_row in range(face_row):
                if not row_solved_checker(l1_tracker, prev_face_row):
                    # Collect destroyed pieces with details
                    destroyed = self._get_destroyed_pieces_in_row(l1_tracker, prev_face_row)

                    # Format detailed error message
                    error_lines = [
                        "",
                        "=" * 80,
                        "SANITY CHECK FAILED: Previous row corrupted",
                        f"  Operation: {op_name}",
                        f"  Working on row: {face_row}",
                        f"  Corrupted row: {prev_face_row}",
                        f"  Destroyed pieces: {len(destroyed)}",
                        "-" * 80,
                    ]

                    for _, info in destroyed:
                        error_lines.append(f"  • {info}")

                    error_lines.append("=" * 80)
                    error_lines.append("")

                    raise AssertionError("\n".join(error_lines))

    @contextmanager
    def with_sanity_check_previous_are_solved(
        self,
        l1_tracker: FaceTracker,
        face_row: int,
        operation_name: str,
        row_solved_checker
    ) -> Generator[None, None, None]:
        """Context manager that performs before/after sanity checks.

        Checks that previous rows are solved before and after the operation.
        If an exception occurs during the operation, the after check is skipped.

        IMPORTANT PATTERN - Exception-aware context manager:
        =====================================================
        This context manager uses a subtle but powerful Python pattern:
        Code AFTER yield only runs if the with-block completes normally.

        Execution flow:
        1. Code BEFORE yield: Always runs (setup/before-check)
        2. yield: Transfers control to the with-block
        3. Code AFTER yield: Only runs if with-block completes WITHOUT exception

        If an exception is raised in the with-block:
        - Execution does NOT continue after yield
        - Exception propagates immediately
        - After-check is skipped (preventing cascading errors)

        Why this matters here:
        - User presses abort button → exception raised
        - Without this pattern: after-check would also fail, creating second error
        - With this pattern: after-check is skipped, only original exception shown

        Note: If you need cleanup that ALWAYS runs (even on exception), use
        try-finally around yield. Here we intentionally want to skip the
        after-check on exceptions.

        Args:
            l1_tracker: Layer 1 face tracker
            face_row: Current row index being worked on
            operation_name: Description of the operation (e.g., "removing piece from face")
            row_solved_checker: Callable that takes (l1_tracker, face_row) and returns bool

        Usage:
            with self._sanity.with_sanity_check_previous_are_solved(tracker, row, "operation", self._row_solved):
                # Your code here
                pass
        """
        # Before check - always runs
        self.sanity_check_previous_are_solved(l1_tracker, face_row, f"before {operation_name}", row_solved_checker)

        yield

        # After check - only runs if no exception occurred during yield
        # (If user pressed abort, execution never reaches here)
        self.sanity_check_previous_are_solved(l1_tracker, face_row, f"after {operation_name}", row_solved_checker)
