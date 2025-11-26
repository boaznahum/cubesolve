# Testing Guide

This project uses **pytest** for testing. This guide covers the basics of running and writing tests.

## Running Tests

### From Command Line

```powershell
# Activate virtual environment first
.\.venv314\Scripts\Activate.ps1

# Run all tests (excludes slow tests by default)
pytest

# Run all tests with verbose output
pytest -v

# Run all tests including slow ones
pytest -m ""

# Run a specific test file
pytest tests/test_cube.py

# Run a specific test function
pytest tests/test_cube.py::test_scramble_and_solve

# Run a specific test class
pytest tests/test_simplify.py::TestFlatten

# Run a specific test method in a class
pytest tests/test_simplify.py::TestFlatten::test_flatten_slice_move

# Run tests matching a keyword/pattern
pytest -k "scramble"           # runs tests with "scramble" in name
pytest -k "boy or cube"        # runs tests with "boy" OR "cube" in name
pytest -k "not slow"           # exclude tests with "slow" in name
```

### Using pytest Markers

Markers are labels you can add to tests to categorize them:

```powershell
# Run only slow tests
pytest -m slow

# Run only benchmark tests
pytest -m benchmark

# Exclude slow tests (default in this project)
pytest -m "not slow"

# Combine markers
pytest -m "slow and not benchmark"
```

### Output Options

```powershell
# Verbose output (shows each test name)
pytest -v

# Very verbose (shows even more detail)
pytest -vv

# Show print statements (normally captured)
pytest -s

# Combine: verbose + show prints
pytest -vs

# Show local variables in tracebacks
pytest -l

# Stop on first failure
pytest -x

# Stop after N failures
pytest --maxfail=3

# Show slowest N tests
pytest --durations=10
```

### From PyCharm

1. Right-click on `tests` folder → "Run 'pytest in tests'"
2. Or use the run configurations:
   - **"pytest all tests"** - fast tests only
   - **"pytest all tests (with slow)"** - includes slow/benchmark tests
3. Right-click on any test file → "Run 'pytest in ...'"
4. Click the green play button next to any test function

## Writing Tests

### Basic Test Function

```python
def test_something():
    """Test description."""
    result = my_function()
    assert result == expected_value
```

- Test functions must start with `test_`
- Use `assert` statements to verify results
- Docstrings are optional but recommended

### Using Assertions

```python
def test_assertions_examples():
    # Basic equality
    assert 1 + 1 == 2

    # With error message
    assert result == expected, f"Expected {expected}, got {result}"

    # Boolean checks
    assert cube.solved
    assert not cube.is_empty

    # Check for None
    assert result is None
    assert result is not None

    # Check types
    assert isinstance(result, list)

    # Check collections
    assert item in my_list
    assert len(my_list) == 5

    # Check exceptions are raised
    import pytest
    with pytest.raises(ValueError):
        function_that_should_raise()

    # Check exception message
    with pytest.raises(ValueError, match="invalid size"):
        function_that_should_raise()
```

### Test Classes

Group related tests in a class (no need to inherit from anything):

```python
class TestCubeSolving:
    """Tests for cube solving functionality."""

    def test_solve_3x3(self):
        """Test solving a 3x3 cube."""
        cube = Cube(3)
        # ... test code

    def test_solve_5x5(self):
        """Test solving a 5x5 cube."""
        cube = Cube(5)
        # ... test code
```

### Parametrized Tests

Run the same test with different inputs:

```python
import pytest

@pytest.mark.parametrize("size", [3, 4, 5])
def test_cube_creation(size):
    """Test cube creation for different sizes."""
    cube = Cube(size)
    assert cube.size == size

# Multiple parameters
@pytest.mark.parametrize("size,expected", [
    (3, 9),
    (4, 16),
    (5, 25),
])
def test_face_count(size, expected):
    """Test face cell count."""
    cube = Cube(size)
    assert cube.face_cell_count == expected

# Multiple parameter sets (creates cartesian product)
@pytest.mark.parametrize("size", [3, 5])
@pytest.mark.parametrize("sanity", [True, False])
def test_with_combinations(size, sanity):
    """Runs 4 times: (3,True), (3,False), (5,True), (5,False)"""
    pass
```

### Fixtures

Fixtures provide reusable setup code:

```python
import pytest

@pytest.fixture
def cube():
    """Create a fresh cube for each test."""
    return Cube(3)

@pytest.fixture
def scrambled_cube(cube):
    """Create a scrambled cube."""
    alg = Algs.scramble(cube.size)
    alg.play(cube)
    return cube

# Using fixtures (just add as parameter)
def test_solve(scrambled_cube):
    """Test uses the scrambled_cube fixture."""
    solver = Solver(scrambled_cube)
    solver.solve()
    assert scrambled_cube.solved
```

### Fixture with Cleanup

```python
@pytest.fixture
def app():
    """Create app and cleanup after test."""
    app = AbstractApp.create_non_default(3, animation=False)
    yield app  # test runs here
    # cleanup code runs after test
    app.close()
```

### Auto-use Fixtures

Fixtures that run automatically for every test:

```python
@pytest.fixture(autouse=True)
def reset_config():
    """Reset config before each test."""
    original = config.CHECK_CUBE_SANITY
    yield
    config.CHECK_CUBE_SANITY = original
```

### Markers

Add markers to categorize tests:

```python
import pytest

@pytest.mark.slow
def test_large_cube():
    """This test is slow, skip with -m 'not slow'"""
    cube = Cube(10)
    # ...

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

@pytest.mark.skipif(sys.platform == "win32", reason="Linux only")
def test_linux_specific():
    pass

@pytest.mark.xfail(reason="Known bug, see issue #123")
def test_known_bug():
    """Test expected to fail."""
    pass
```

### Testing Exceptions

```python
import pytest

def test_invalid_size_raises():
    """Test that invalid cube size raises ValueError."""
    with pytest.raises(ValueError):
        Cube(-1)

def test_exception_message():
    """Test exception message content."""
    with pytest.raises(ValueError, match="size must be positive"):
        Cube(-1)
```

## Project Structure

```
cubesolve/
├── cube/                   # Main package
│   ├── algs/               # Algorithm definitions
│   ├── app/                # Application logic
│   ├── model/              # Cube model
│   ├── solver/             # Solvers (beginner, CFOP)
│   ├── viewer/             # GUI viewer
│   └── ...
├── tests/                  # Test directory (this folder)
│   ├── TESTING.md          # This file
│   ├── test_cube.py        # Core cube tests
│   ├── test_boy.py         # BOY orientation tests
│   ├── test_simplify.py    # Algorithm simplification tests
│   ├── test_indexes_slices.py  # Slice operations tests
│   ├── test_scramble_repeatable.py  # Scramble repeatability
│   ├── test_alg_slice_sequence.py   # Slice syntax tests
│   ├── test_cube_aggresive.py  # Stress tests (marked slow)
│   ├── test_perf.py        # Benchmarks (marked slow)
│   ├── bug_sanity_on.py    # Sanity check tests
│   └── gui/                # GUI tests (separate, require display)
├── pyproject.toml          # Project configuration
├── pytest.ini              # Pytest configuration
└── requirements*.txt       # Dependencies
```

## Configuration (pytest.ini)

The project's `pytest.ini` in the root directory:

```ini
[pytest]
testpaths = tests               # Where to find tests
python_files = test_*.py bug_*.py  # Test file patterns
python_functions = test_*       # Test function pattern

markers =
    slow: marks tests as slow
    benchmark: marks tests as benchmarks

addopts = --ignore=tests/gui    # Ignore GUI tests by default
```

## Installing for Development

To install the package in development mode (enables imports from anywhere):

```powershell
# Activate virtual environment
.\.venv314\Scripts\Activate.ps1

# Install in editable mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"
```

## Common Patterns in This Project

### Testing Cube State

```python
def test_cube_state():
    cube = Cube(3)

    # Save state
    state = cube.cqr.get_sate()

    # Do operations
    alg.play(cube)
    alg.prime.play(cube)  # Undo

    # Compare states
    assert cube.cqr.compare_state(state)
```

### Testing Solve

```python
def test_solve():
    app = AbstractApp.create_non_default(3, animation=False)
    cube = app.cube

    # Scramble
    alg = Algs.scramble(cube.size, seed=42)
    alg.play(cube)

    # Solve
    app.slv.solve()

    # Verify
    assert cube.solved
```

## Tips

1. **Run tests frequently** - catch issues early
2. **Use `-x`** to stop on first failure when debugging
3. **Use `-k`** to run specific tests by name pattern
4. **Use `-v`** to see which tests are running
5. **Use `-s`** to see print output during tests
6. **Mark slow tests** with `@pytest.mark.slow` so they can be skipped
7. **Use fixtures** for common setup code
8. **Keep tests independent** - each test should work alone

## Useful Links

- [pytest documentation](https://docs.pytest.org/)
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [pytest markers](https://docs.pytest.org/en/stable/mark.html)
- [pytest parametrize](https://docs.pytest.org/en/stable/parametrize.html)
