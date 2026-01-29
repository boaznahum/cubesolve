# L3 Edge Cases - Diagrams

All cases: Source wing (S) → Target position (FL)
Helper edge: FD (front-down)

## Front Face Edge Layout

```
        ┌─────────┐
        │   FU    │  (front-up edge)
        │ 0  1  2 │  (wing indices for 5x5)
┌───────┼─────────┼───────┐
│  FL   │         │  FR   │
│ 0     │  FRONT  │     0 │
│ 1     │  FACE   │     1 │
│ 2     │  (L3)   │     2 │
└───────┼─────────┼───────┘
        │ 0  1  2 │
        │   FD    │  (front-down edge)
        └─────────┘
```

## Commutators Reference

```
LEFT CM:   FU → FL → BU → FU  (3-cycle)
           Alg: U' L' U M[k]' U' L U M[k]

RIGHT CM:  FU → FR → BU → FU  (3-cycle)
           Alg: U R U' M[k]' U R' U' M[k]

(LEFT CM)':  FU → BU → FL → FU  (reverse)
(RIGHT CM)': FU → BU → FR → FU  (reverse)
```

---

## Case 1: FR → FL (Source on Right Edge)

### Initial State
```
        ┌─────────┐
        │   FU    │
        │    ?    │
┌───────┼─────────┼───────┐
│  FL   │         │  FR   │
│  [T]  │  FRONT  │  [S]  │  ← S=Source, T=Target position
└───────┼─────────┼───────┘
        │   FD    │
        │   [H]   │  ← H=Helper (will go to BU)
        └─────────┘

BU: [ ? ]  (will be overwritten)
```

### Step 1: SETUP - Bring FD to BU
```
FD wing [H] → BU

        ┌─────────┐
        │   FU    │
        │    ?    │
┌───────┼─────────┼───────┐
│  FL   │         │  FR   │
│  [T]  │  FRONT  │  [S]  │
└───────┼─────────┼───────┘
        │   FD    │
        │   [?]   │  (changed)
        └─────────┘

BU: [ H ]  (helper now here)

STACK: [setup_alg]
```

### Step 2: (RIGHT CM)' - Reverse cycle: FR → FU
```
(RIGHT CM)': FU → BU → FR → FU

Before:  FU=[?], FR=[S], BU=[H]
After:   FU=[S], FR=[H], BU=[?]

        ┌─────────┐
        │   FU    │
        │   [S]   │  ← Source now here!
┌───────┼─────────┼───────┐
│  FL   │         │  FR   │
│  [T]  │  FRONT  │  [H]  │
└───────┼─────────┼───────┘

BU: [ ? ]

(no stack - this is work)
```

### Step 3: Check Orientation + Flip if needed
```
If source color on front ≠ L3 color:
   → FLIP FU (algorithm: U'² B' R' U)
   → STACK: [setup_alg, flip_alg]
```

### Step 4: LEFT CM - FU → FL
```
LEFT CM: FU → FL → BU → FU

Before:  FU=[S], FL=[T], BU=[?]
After:   FU=[?], FL=[S], BU=[T]

        ┌─────────┐
        │   FU    │
        │   [?]   │
┌───────┼─────────┼───────┐
│  FL   │         │  FR   │
│  [S]  │  FRONT  │  [H]  │  ← Source at target! ✓
└───────┼─────────┼───────┘

BU: [ T ]  (old target wing, will be handled later)

(no stack - this is work)
```

### Step 5: ROLLBACK
```
Undo flip_alg.prime (if was flipped)
Undo setup_alg.prime

RESULT: Source [S] is now at FL ✓
```

---

## Case 2: FU → FL (Source on Top Edge)

### Initial State
```
        ┌─────────┐
        │   FU    │
        │   [S]   │  ← Source already on top!
┌───────┼─────────┼───────┐
│  FL   │         │  FR   │
│  [T]  │  FRONT  │   ?   │
└───────┼─────────┼───────┘
        │   FD    │
        │   [H]   │
        └─────────┘

BU: [ ? ]
```

### Step 1: SETUP - Bring FD to BU
```
FD wing [H] → BU

BU: [ H ]

STACK: [setup_alg]
```

### Step 2: Check Orientation + Flip if needed
```
If source color on front ≠ L3 color:
   → FLIP FU
   → STACK: [setup_alg, flip_alg]
```

### Step 3: LEFT CM - FU → FL
```
LEFT CM: FU → FL → BU → FU

Before:  FU=[S], FL=[T], BU=[H]
After:   FU=[H], FL=[S], BU=[T]

        ┌─────────┐
        │   FU    │
        │   [H]   │
┌───────┼─────────┼───────┐
│  FL   │         │  FR   │
│  [S]  │  FRONT  │   ?   │  ← Source at target! ✓
└───────┼─────────┼───────┘

BU: [ T ]

(no stack - this is work)
```

### Step 4: ROLLBACK
```
Undo flip_alg.prime (if was flipped)
Undo setup_alg.prime

RESULT: Source [S] is now at FL ✓
```

---

## Case 3: FD → FL (Source on Bottom Edge)

### Initial State
```
        ┌─────────┐
        │   FU    │
        │    ?    │
┌───────┼─────────┼───────┐
│  FL   │         │  FR   │
│  [T]  │  FRONT  │   ?   │
└───────┼─────────┼───────┘
        │   FD    │
        │   [S]   │  ← Source on bottom
        └─────────┘

BU: [ ? ]
```

### Step 1: F rotation - Move source to FL, free up FD
```
F rotation cycles: FD → FL → FU → FR → FD

        ┌─────────┐
        │   FU    │
        │   [T]   │  ← Target wing moved here
┌───────┼─────────┼───────┐
│  FL   │         │  FR   │
│  [S]  │  FRONT  │   ?   │  ← Source now here!
└───────┼─────────┼───────┘
        │   FD    │
        │   [?]   │  ← FD is now FREE
        └─────────┘

STACK: [F]
```

### Step 2: SETUP - Bring FD to BU (FD is now free!)
```
FD wing → BU

BU: [ H ]  (from FD)

STACK: [F, setup_alg]
```

### Step 3: (LEFT CM)' - Reverse cycle: FL → FU
```
(LEFT CM)': FU → BU → FL → FU

Before:  FU=[T], FL=[S], BU=[H]
After:   FU=[S], FL=[H], BU=[T]

        ┌─────────┐
        │   FU    │
        │   [S]   │  ← Source now on top!
┌───────┼─────────┼───────┐
│  FL   │         │  FR   │
│  [H]  │  FRONT  │   ?   │
└───────┼─────────┼───────┘

BU: [ T ]

(no stack - this is work)
```

### Step 4: F' - Undo F rotation
```
F' rotation: FR → FU → FL → FD → FR

        ┌─────────┐
        │   FU    │
        │   [H]   │
┌───────┼─────────┼───────┐
│  FL   │         │  FR   │
│  [S]  │  FRONT  │   ?   │  ← Source at target! ✓
└───────┼─────────┼───────┘
        │   FD    │
        │   [?]   │
        └─────────┘

BU: [ T ]

(pop F from stack, now: [setup_alg])
```

### Step 5: Check Orientation + Flip if needed
```
If source needs flip:
   → FLIP FL (algorithm: L² B' U' L U)
   → STACK: [setup_alg, flip_fl_alg]
```

### Step 6: ROLLBACK
```
Undo flip_fl_alg.prime (if was flipped)
Undo setup_alg.prime

RESULT: Source [S] is now at FL ✓
```

---

## Case 4: FL → FL (Source on Same Edge as Target)

Source is on FL but at index inv(ti), not ti. Always needs flip.

### Initial State
```
        ┌─────────┐
        │   FU    │
        │    ?    │
┌───────┼─────────┼───────┐
│  FL   │         │  FR   │
│[T][S] │  FRONT  │   ?   │  ← Both on same edge!
│       │         │       │    T at index ti
└───────┼─────────┼───────┘    S at index inv(ti)
        │   FD    │
        │   [H]   │
        └─────────┘

BU: [ ? ]
```

### Step 1: SETUP - Bring FD to BU
```
BU: [ H ]

STACK: [setup_alg]
```

### Step 2: LEFT CM (first) - FL → BU
```
LEFT CM: FU → FL → BU → FU

Before:  FU=[?], FL has [T] and [S], BU=[H]
After:   Source [S] at FL moves to BU

        ┌─────────┐
        │   FU    │
        │   [H]   │  ← H moved here
┌───────┼─────────┼───────┐
│  FL   │         │  FR   │
│  [?]  │  FRONT  │   ?   │
└───────┼─────────┼───────┘

BU: [ S ]  ← Source now at BU

(no stack - this is work)
```

### Step 3: LEFT CM (second) - BU → FU
```
LEFT CM again: FU → FL → BU → FU

Before:  FU=[H], FL=[?], BU=[S]
After:   BU=[S] moves to FU

        ┌─────────┐
        │   FU    │
        │   [S]   │  ← Source now on top!
┌───────┼─────────┼───────┐
│  FL   │         │  FR   │
│  [H]  │  FRONT  │   ?   │
└───────┼─────────┼───────┘

BU: [ ? ]

(no stack - this is work)
```

### Step 4: FLIP FU (always required for this case)
```
FLIP FU: U'² B' R' U

Source [S] is now flipped at FU

STACK: [setup_alg, flip_alg]
```

### Step 5: LEFT CM (third) - FU → FL
```
LEFT CM: FU → FL → BU → FU

Before:  FU=[S flipped], FL=[H], BU=[?]
After:   FU=[S] moves to FL

        ┌─────────┐
        │   FU    │
        │   [?]   │
┌───────┼─────────┼───────┐
│  FL   │         │  FR   │
│  [S]  │  FRONT  │   ?   │  ← Source at target! ✓
└───────┼─────────┼───────┘

(no stack - this is work)
```

### Step 6: ROLLBACK
```
Undo flip_alg.prime
Undo setup_alg.prime

RESULT: Source [S] is now at FL ✓
```

---

## Summary Table

| Case | Source | Steps | Needs Flip Check |
|------|--------|-------|------------------|
| 1 | FR | Setup → (Right CM)' → [Flip?] → Left CM → Rollback | Yes |
| 2 | FU | Setup → [Flip?] → Left CM → Rollback | Yes |
| 3 | FD | F → Setup → (Left CM)' → F' → [Flip FL?] → Rollback | Yes (on FL) |
| 4 | FL | Setup → Left CM x2 → Flip → Left CM → Rollback | Always flip |

## Key Invariants

1. **FD is always the helper** - moved to BU to protect it
2. **Setup returns Alg** - for `.prime` undo
3. **CMs are "work"** - not rolled back
4. **Flip algorithms return Alg** - for `.prime` undo
5. **Source must be on front face** - assert this!
