# Potential Issue: Tracker Majority Algorithm with Even Color Distribution

**STATUS: Investigated - Bug does NOT manifest in practice**

## Scenario

On a 4x4 cube where:
- WHITE face (U) is solved (all 4 centers are WHITE)
- YELLOW face (D) is solved (all 4 centers are YELLOW)
- Other 4 faces (F, B, L, R) have **even distribution** of remaining colors

```
        4x4 Cube with Even Distribution
        =================================

                 U (SOLVED)
               ┌───────────┐
               │  W  W     │
               │     W  W  │  ← All WHITE ✓
               └───────────┘

       L (EVEN)      F (EVEN)     R (EVEN)     B (EVEN)
      ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
      │  O  R   │  │  G  B   │  │  O  R   │  │  G  B   │
      │  G  B   │  │  O  R   │  │  G  B   │  │  O  R   │
      └─────────┘  └─────────┘  └─────────┘  └─────────┘
           ↑            ↑            ↑            ↑
      1 of each    1 of each    1 of each    1 of each
      O,R,G,B      O,R,G,B      O,R,G,B      O,R,G,B

                 D (SOLVED)
               ┌───────────┐
               │  Y  Y     │
               │     Y  Y  │  ← All YELLOW ✓
               └───────────┘
```

## The Bug

When tracker creation encounters **even distribution** (no clear majority):

```
    Majority Algorithm Behavior
    ============================

    Face F centers: [GREEN, BLUE, ORANGE, RED]
    Counts: {G:1, B:1, O:1, R:1}  ← ALL TIED!

    What should happen:
    ┌─────────────────────────────────────┐
    │  Pick color that maintains BOY      │
    │  F should be ORANGE (BOY standard)  │
    └─────────────────────────────────────┘

    What actually happens:
    ┌─────────────────────────────────────┐
    │  Pick first/arbitrary color         │
    │  F might get GREEN!                 │
    │                                     │
    │  Then R also tries to pick...       │
    │  R might ALSO get GREEN!  ← BUG!    │
    └─────────────────────────────────────┘
```

## Invalid Tracker Assignment Example

```
    Valid BOY:                    Invalid (Bug Result):
    ┌───┐                         ┌───┐
    │ W │                         │ W │
    ├───┼───┬───┬───┐             ├───┼───┬───┬───┐
    │ B │ O │ G │ R │             │ R │ G │ O │ G │  ← GREEN twice!
    ├───┼───┴───┴───┘             ├───┼───┴───┴───┘
    │ Y │                         │ Y │
    └───┘                         └───┘

    6 unique colors ✓             Only 5 colors! ✗
```

## Consequences

1. **Shadow cube created with invalid centers**
   - 3x3 solver tries to solve impossible state

2. **Pieces placed in wrong positions**
   - Corners/edges solved to match invalid tracker colors

3. **After Y rotation, check fails or gives wrong result**
   - face_colors mapping is internally consistent but wrong

## Test Case to Demonstrate

```python
def test_tracker_even_distribution_bug():
    """Demonstrate tracker bug with even color distribution."""
    # Create 4x4 with WHITE and YELLOW solved,
    # other faces have exactly 1 of each remaining color

    # 1. Setup cube with specific pattern
    # 2. Create trackers - check if assignment is valid BOY
    # 3. Solve L1
    # 4. Rotate Y
    # 5. Check L1 again - should still be solved
    # 6. Create NEW trackers - might get different assignment!
```

## Root Cause

`_find_face_with_max_colors` in `NxNCentersFaceTrackers` doesn't handle ties correctly:
- When multiple colors have same count, it picks arbitrarily
- No validation that resulting assignment is valid BOY layout
- Can assign same color to multiple faces

## Investigation Results

Testing revealed that the bug does NOT actually manifest because:

1. **track_no_1** finds faces with clear majority first (U=YELLOW:4, D=WHITE:4)
2. **_track_no_3** excludes already-used colors before searching remaining faces
3. **_track_two_last** uses BOY constraints to validate final assignment

The BOY constraint check in `_track_two_last` ensures the final layout is always
valid, even when earlier choices were arbitrary due to ties.

```python
# In _track_two_last, this check ensures valid BOY:
if cl.same(self.cube.original_layout):
    return True  # f/color make it a BOY
```

## Test Results

See: `tests/solvers/test_tracker_majority_bug.py`

All tests pass, confirming:
- Even distribution produces valid 6-color BOY layout
- L1 solved state is consistent after Y rotation
- Fresh trackers after rotation give equivalent BOY layout
- Random scrambles always produce valid trackers

## Original Proposed Fix (Not Needed)

The following fix was proposed but is NOT required:

1. When creating trackers, validate result is BOY-consistent
2. If tie in majority, use BOY constraints to break tie:
   - If U=WHITE, D must be YELLOW
   - If F=ORANGE, B must be RED
   - etc.
3. Or: For LBL L1, derive tracker colors from L1 corners (known colors)
