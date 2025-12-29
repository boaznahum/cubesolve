# Parser Tests Task

## Status: Tests Implemented - Parser Bug Found

**Branch:** `parser-tests` (from `super-communicator`)
**Last Updated:** 2025-12-29

---

## Objective

Create comprehensive tests for the algorithm parser to verify that:
1. Algorithms can be converted to strings and back (round-trip)
2. Parsed algorithms produce the same cube state as original
3. Algorithm and its inverse return to solved state

**Strategy:** Start with short, simple sequences to find bugs quickly before testing complex scrambles.

---

## Code Analysis

### Key Files

| File | Purpose |
|------|---------|
| `src/cube/domain/algs/_parser.py` | `parse_alg(s: str) -> Alg` - parses algorithm strings |
| `src/cube/domain/algs/Alg.py` | Base class with `__str__()` -> `atomic_str()` |
| `src/cube/domain/algs/Algs.py` | `Algs.parse(s)`, `Algs.Simple`, `Algs.scramble()` |
| `src/cube/domain/algs/Scramble.py` | `_scramble()` - generates random scrambles |

### Parser Flow

```
String: "R U R' U'"
          ↓
    parse_alg(s)
          ↓
    re.split(pattern, s) → tokens
          ↓
    _Parser(tokens).parse()
          ↓
    _token_to_alg(token) for each token
          ↓
    SeqAlg (sequence of Alg objects)
```

### String Conversion

```python
alg = Algs.R + Algs.U + Algs.R.prime + Algs.U.prime
s = str(alg)  # calls alg.atomic_str()
parsed = Algs.parse(s)
```

### Algs.Simple List (used for scramble generation)

Current:
```python
Simple: Sequence[NSimpleAlg] = [
    L, Lw,
    R, Rw, X, M,
    U, Uw, E, Y,
    F, Fw, Z, S,
    B, Bw,
    D, Dw,
]
```

**Missing:** `f, u, r, l, d, b` (wide face algs for whole slice operations)

---

## Test Plan - Phase 1: Short Sequences

Start with simple tests to find and fix bugs before moving to complex scrambles.

### Level 1: Single Moves

```python
test_cases = [
    "R", "L", "U", "D", "F", "B",      # Basic face moves
    "R'", "L'", "U'", "D'", "F'", "B'", # Inverse moves
    "R2", "L2", "U2", "D2", "F2", "B2", # Double moves
    "M", "E", "S",                      # Slice moves
    "X", "Y", "Z",                      # Whole cube rotations
    "Rw", "Lw", "Uw", "Dw", "Fw", "Bw", # Double-layer moves
    "r", "l", "u", "d", "f", "b",       # Adaptive wide moves
]
```

### Level 2: Two-Move Sequences

```python
test_cases = [
    "R U", "R L", "R R",
    "R' U'", "R2 U2",
    "R U'", "R' U",
]
```

### Level 3: Four-Move Sequences

```python
test_cases = [
    "R U R' U'",      # Sexy move
    "R U R U",
    "R2 U2 R2 U2",
]
```

### Level 4: Grouped Sequences

```python
test_cases = [
    "(R U)",
    "(R U)2",
    "[R U R' U']",
    "(R U R' U')2",
]
```

### Level 5: Complex Sequences

Once all simple tests pass, move to scrambles.

---

## Test Plan - Phase 2: Full Scrambles

### Test 1: Round-Trip String Conversion

```python
def test_parse_round_trip(cube_size, seed):
    """
    1. Generate scramble
    2. Convert to string: str(scramble)
    3. Parse string: Algs.parse(string)
    4. Compare string representations
    """
    scramble = Algs.scramble(cube_size, seed)
    s1 = str(scramble)
    parsed = Algs.parse(s1)
    s2 = str(parsed)
    assert s1 == s2
```

### Test 2: Same Cube State

```python
def test_parse_same_state(cube_size, seed):
    """
    1. Create two cubes
    2. Apply original scramble to cube1
    3. Parse scramble string, apply to cube2
    4. Verify cube states are identical
    """
    app1 = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
    app2 = AbstractApp.create_non_default(cube_size=cube_size, animation=False)

    scramble = Algs.scramble(cube_size, seed)
    scramble.play(app1.cube)

    parsed = Algs.parse(str(scramble))
    parsed.play(app2.cube)

    # Compare cube states (all face colors)
    assert cubes_equal(app1.cube, app2.cube)
```

### Test 3: Inverse Returns to Solved

```python
def test_alg_inverse(cube_size, seed):
    """
    1. Start with solved cube
    2. Apply scramble
    3. Apply inverse of scramble
    4. Verify cube is solved
    """
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)

    scramble = Algs.scramble(cube_size, seed)
    scramble.play(app.cube)
    scramble.inv().play(app.cube)

    assert cube_is_solved(app.cube)
```

### Test 4: Parsed Inverse Returns to Solved

```python
def test_parsed_inverse(cube_size, seed):
    """
    1. Generate scramble, apply to cube
    2. Parse scramble string
    3. Apply inverse of parsed alg
    4. Verify cube is solved
    """
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)

    scramble = Algs.scramble(cube_size, seed)
    scramble.play(app.cube)

    parsed = Algs.parse(str(scramble))
    parsed.inv().play(app.cube)

    assert cube_is_solved(app.cube)
```

### Test 5: Cross Inverse (alg1 applied, alg2.inv applied)

```python
def test_cross_inverse(cube_size, seed):
    """
    1. Apply original scramble
    2. Parse to get alg2
    3. Apply alg2.inv()
    4. Should return to solved
    """
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)

    scramble = Algs.scramble(cube_size, seed)
    scramble.play(app.cube)

    parsed = Algs.parse(str(scramble))
    parsed.inv().play(app.cube)

    assert cube_is_solved(app.cube)
```

### Test Parameters

| Parameter | Values |
|-----------|--------|
| `cube_size` | 3, 4, 5, 6, 7, 8 |
| `seed` | 0-9, 101, 202, 303, random |

---

## Additional Tasks

### Task: Add Wide Algs to Algs.Simple

Add `f, u, r, l, d, b` to `Algs.Simple` so scramble generates them:

```python
# In Algs.py, update Simple list:
Simple: Sequence[NSimpleAlg] = [
    L, Lw,
    R, Rw, X, M,
    U, Uw, E, Y,
    F, Fw, Z, S,
    B, Bw,
    D, Dw,
    f, u, r, l, d, b,  # ADD THESE
]
```

**Note:** Need to verify `f, u, r, l, d, b` are `NSimpleAlg` type (they are `WideFaceAlg`).

---

## Helper Functions Needed

```python
def cubes_equal(cube1: Cube, cube2: Cube) -> bool:
    """Compare all face colors of two cubes."""
    for face_name in FaceName:
        f1 = cube1.face(face_name)
        f2 = cube2.face(face_name)
        # Compare all stickers
        ...
    return True

def cube_is_solved(cube: Cube) -> bool:
    """Check if cube is in solved state."""
    # Each face should have uniform color
    ...
```

---

## Implementation Progress

- [x] Create branch `parser-tests`
- [x] Analyze parser code
- [x] Analyze scramble code
- [x] Create test plan
- [x] Create algorithm notation documentation (`docs/algorithm_notation.md`)
- [ ] **Phase 1: Short Sequences**
  - [ ] Implement helper functions (`cubes_equal`, `cube_is_solved`)
  - [ ] Level 1: Single moves
  - [ ] Level 2: Two-move sequences
  - [ ] Level 3: Four-move sequences
  - [ ] Level 4: Grouped sequences
  - [ ] Fix any bugs found
- [ ] **Phase 2: Full Scrambles**
  - [ ] Round-trip test
  - [ ] Same state test
  - [ ] Inverse test
  - [ ] Cross inverse test
- [ ] Add `f, u, r, l, d, b` to `Algs.Simple`
- [ ] Run on all cube sizes (3-8)
- [ ] Final review

---

## Notes for Next Session

1. **Start with Phase 1, Level 1** - single moves
2. **Check WideFaceAlg compatibility** with `NSimpleAlg` type for `Algs.Simple`
3. **Edge cases to test:** empty string, invalid tokens, nested sequences
4. **Parser limitations:** See `_parser.py` docstring - doesn't support all notations
5. **Documentation created:** `docs/algorithm_notation.md` - notation reference

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `wip/parser-tests.md` | This task tracking file |
| `docs/algorithm_notation.md` | Algorithm notation user guide |
