# Profiling Guide

This directory contains tools and results for measuring cube solver performance.

## Directory Structure

```
profiling/
├── README.md           # This file - instructions and tool overview
├── scripts/            # Python scripts for benchmarking
│   └── compare_visibility.py  # Compare has_visible_presentation impact
└── progress/           # Results from optimization work (chronological)
    └── YYYY-MM-DD_description.md
```

## Available Tools

### 1. Solver Profiler (in tests/performance/)

Comprehensive profiling with cProfile support.

```bash
# Full profiling run
python -m tests.performance.profile_solvers

# Quick benchmark (timing only, no cProfile)
python -m tests.performance.profile_solvers --quick

# Specific solver
python -m tests.performance.profile_solvers --solver LBL

# Specific sizes
python -m tests.performance.profile_solvers --sizes 3,5,7

# Compare cache on vs off
python -m tests.performance.profile_solvers --compare-cache

# Save JSON report
python -m tests.performance.profile_solvers --output report.json
```

### 2. Visibility Comparison (in profiling/scripts/)

Measures impact of `has_visible_presentation` flag on performance.

```bash
# Default run (3x3, 4x4, 5x5 with LBL, CFOP, Kociemba)
python -m profiling.scripts.compare_visibility

# Custom sizes
python -m profiling.scripts.compare_visibility --sizes 3,5,7

# More runs for accuracy
python -m profiling.scripts.compare_visibility --runs 10

# Output as markdown (for documentation)
python -m profiling.scripts.compare_visibility --markdown
```

### 3. Face Rotation Profiler (in tests/performance/)

Profile individual face rotation performance.

```bash
python -m tests.performance.profile_face_rotate
```

### 4. Scramble Profiler (in tests/performance/)

Profile scramble generation.

```bash
python -m tests.performance.profile_scramble
```

## Key Metrics

| Metric | Description | Good Value |
|--------|-------------|------------|
| **Avg time (ms)** | Average solve time | Lower is better |
| **Moves/sec** | Throughput | Higher is better |
| **Slowdown** | Ratio of slow/fast config | 1.0x = no impact |

## When to Profile

1. **Before optimization**: Establish baseline
2. **After optimization**: Verify improvement
3. **After refactoring**: Ensure no regression
4. **New solver/algorithm**: Compare to existing

## Recording Results

After making performance-related changes:

1. Run relevant profiling scripts
2. Create a new file in `progress/` with format: `YYYY-MM-DD_description.md`
3. Include:
   - Description of the change
   - Before/after metrics
   - Key findings

## Environment Notes

- Always run with `CUBE_QUIET_ALL=1` to suppress debug output
- Close other applications for consistent results
- Run multiple times (5-10) to get stable averages
- Use `--quick` flag for faster iteration during development
