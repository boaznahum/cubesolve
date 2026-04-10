"""
Parity reporting comparison test.

For each (solver, cube_size, scramble_seed) combination:
  1. Scramble the cube
  2. Solve and capture SolverResults
  3. Write parity data to a JSON report file

Run this TWICE — once on the old commit and once on the new — then diff the reports.

Usage (must disable xdist with -o "addopts=" since report uses module-level state):

  # 1. On the OLD commit (baseline) — stash changes, run, rename report:
  git stash
  CUBE_QUIET_ALL=1 python -m pytest tests/solvers/test_parity_reporting.py -o "addopts=" -v
  mv tests/solvers/parity_report_*.json tests/solvers/parity_report_BEFORE.json
  git stash pop

  # 2. On the NEW commit (after changes):
  CUBE_QUIET_ALL=1 python -m pytest tests/solvers/test_parity_reporting.py -o "addopts=" -v
  mv tests/solvers/parity_report_*.json tests/solvers/parity_report_AFTER.json

  # 3. Compare:
  python tests/solvers/compare_parity_reports.py tests/solvers/parity_report_BEFORE.json tests/solvers/parity_report_AFTER.json
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.Solvers import Solvers
from cube.domain.solver.SolverName import SolverName
from cube.domain.solver.solver import SolverResults

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CUBE_SIZES = list(range(2, 10))  # 2..9
SCRAMBLE_SEEDS = list(range(10))  # 0..9

REPORT_DIR = Path(__file__).parent
SOLVER_NAMES = SolverName.user_visible()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sr_to_dict(sr: SolverResults) -> dict:
    """Serialize SolverResults parity info to a plain dict.

    Works on both old (scalar fields) and new (list-based) SolverResults.
    """
    d: dict = {
        "has_parity": sr.has_parity,
        "was_corner_swap": sr.was_corner_swap.name if sr.was_corner_swap else None,
        "was_even_edge_parity": sr.was_even_edge_parity.name if sr.was_even_edge_parity else None,
        "was_partial_edge_parity": sr.was_partial_edge_parity.name if sr.was_partial_edge_parity else None,
    }
    # New list-based API (only present after refactor)
    if hasattr(sr, "parities"):
        d["parities"] = [
            {"type": pt.value, "fix": fix.name}
            for pt, fix in sr.parities
        ]
    if hasattr(sr, "parity_summary"):
        d["summary"] = sr.parity_summary()
    return d


def _get_branch_name() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip().replace("/", "_")
    except Exception:
        return "unknown"


def _get_commit_hash() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Report collection
# ---------------------------------------------------------------------------

# Module-level accumulator — filled by parametrized tests, flushed by finalizer
_report_entries: dict[str, dict] = {}


def _run_one(solver_name: SolverName, cube_size: int, seed: int) -> dict:
    """Scramble → solve → return parity dict.  Returns skip-marker on unsupported."""
    skip = solver_name.meta.get_skip_reason(cube_size)
    if skip:
        return {"skipped": skip}

    app = AbstractApp.create_app(cube_size=cube_size)
    solver = Solvers.by_name(solver_name, app.op)
    app.scramble(seed, None, animation=False, verbose=False)

    if solver.is_solved:
        return {"skipped": "already solved after scramble"}

    sr: SolverResults = solver.solve(debug=False, animation=False)

    if not solver.is_solved:
        return {"error": "solver failed to solve"}

    return _sr_to_dict(sr)


# ---------------------------------------------------------------------------
# Parametrized test
# ---------------------------------------------------------------------------

_params = [
    pytest.param(sn, cs, seed, id=f"{sn.display_name}-{cs}x{cs}-s{seed}")
    for sn in SOLVER_NAMES
    for cs in CUBE_SIZES
    for seed in SCRAMBLE_SEEDS
]


@pytest.fixture(autouse=True, scope="module")
def _deterministic_geometry_config():
    """Provide a config factory with deterministic geometry for all tests in this module."""
    # Note: This fixture is currently unused (test class is commented out).
    # When re-enabled, tests should create AppConfig via:
    #   cfg = AppConfig()
    #   cfg.prevent_random_face_pick_up_in_geometry = True
    #   app = AbstractApp.create_app(config=cfg)
    pass


# @pytest.mark.slow
# class TestParityReporting:
#
#     @pytest.mark.parametrize("solver_name,cube_size,seed", _params)
#     def test_parity(self, solver_name: SolverName, cube_size: int, seed: int) -> None:
#         key = f"{solver_name.display_name}|{cube_size}|{seed}"
#         result = _run_one(solver_name, cube_size, seed)
#         _report_entries[key] = result
#
#         # The test itself always passes — we're collecting data, not asserting.
#         # But if the solver failed to solve, mark it.
#         if "error" in result:
#             pytest.fail(result["error"])
#
#
# # ---------------------------------------------------------------------------
# # Session-scoped finalizer: flush report to JSON
# # ---------------------------------------------------------------------------
#
# @pytest.fixture(autouse=True, scope="session")
# def _flush_report(request):
#     """After all tests, write the accumulated report to a JSON file."""
#     yield
#     if not _report_entries:
#         return
#
#     branch = _get_branch_name()
#     commit = _get_commit_hash()
#     report_path = REPORT_DIR / f"parity_report_{branch}.json"
#
#     report = {
#         "meta": {
#             "branch": branch,
#             "commit": commit,
#             "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
#             "cube_sizes": CUBE_SIZES,
#             "scramble_seeds": SCRAMBLE_SEEDS,
#             "solvers": [s.display_name for s in SOLVER_NAMES],
#         },
#         "results": _report_entries,
#     }
#
#     report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
#     print(f"\n=== Parity report written to {report_path} ===")
