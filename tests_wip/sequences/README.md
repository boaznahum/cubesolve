# Seed Sequence Files

This directory contains pre-generated seed sequences for reproducible testing.

## File Format

Seed files are simple text files with one seed per line:

```
# Generated: 2025-01-15 10:30:45
# Base seed: 1234567890
# Count: 100
1234567890
987654321
...
```

Lines starting with `#` are comments and are ignored.

## Generating Seed Files

Use the `generate_seed_file.py` script:

```bash
# Generate 100 seeds
python -m tests_wip.generate_seed_file failures_8x 100

# Generate 50 seeds with specific base seed (reproducible)
python -m tests_wip.generate_seed_file edge_cases 50 12345
```

This creates files like `failures_8x_100.txt` in this directory.

## Using Seed Files in Tests

Edit `tests_wip/big_lbl_2/conftest.py`:

```python
# Load first 50 seeds from failures_8x_100.txt
SEED_SEQUENCE_CONFIG = ("failures_8x_100", 50)

# Or disable
SEED_SEQUENCE_CONFIG = None
```

Seeds from files are prefixed with `seq_` in test names (e.g., `seq_1234567890`).

## Listing Available Files

```python
from tests_wip.seed_sequences import list_seed_files

for filename, count in list_seed_files():
    print(f"{filename}: {count} seeds")
```

## Duplicate Handling

The test framework automatically eliminates duplicate seeds to avoid test name conflicts.
If a seed from a file matches a predefined seed or random seed, only the first occurrence
is used.
