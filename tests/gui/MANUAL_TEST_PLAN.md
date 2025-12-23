# GUI Manual Test Plan

This document contains manual tests that should be performed to verify GUI functionality.
When a new GUI bug is found, add it here BEFORE fixing it.

## How to Use This Document

1. **Before each release:** Run through all tests marked with priority [HIGH] and [MEDIUM]
2. **When a bug is found:** Add it to the appropriate section BEFORE fixing
3. **After fixing:** Update the test status and add verification steps
4. **Mark tests:** Use checkboxes `[ ]` for pending, `[x]` for passed

---

## Test Environment

```bash
# Run the GUI
python -m cube.main_pyglet

# Or with debug
python -m cube.main_pyglet --debug-all
```

---

## 1. Marker/Annotation Tests [HIGH]

These tests verify solver annotations (markers showing source/destination).

### 1.1 Source and Destination Markers During Solve

**Bug Reference:** B10 - Markers don't show source/destination during commutator

**Steps:**
1. [ ] Start the application: `python -m cube.main_pyglet`
2. [ ] Press `R` to scramble the cube
3. [ ] Press `S` to start solving with animation
4. [ ] **Observe:** During F2L (First Two Layers), watch for corner/edge pairs being solved

**Expected:**
- [ ] **Source marker** (cyan/magenta ring) appears on the piece being moved
- [ ] **Destination marker** (different colored ring) appears on the target position
- [ ] Both markers visible simultaneously when annotate() is called with both Moved and FixedPosition

**Actual:** _______________

### 1.2 Marker Visibility on All Face Colors

**Steps:**
1. [ ] Scramble cube and start solve
2. [ ] Watch markers on different colored faces

**Expected:**
- [ ] Markers visible on RED faces (should be cyan)
- [ ] Markers visible on GREEN faces (should be magenta)
- [ ] Markers visible on BLUE faces (should be yellow)
- [ ] Markers visible on YELLOW faces (should be blue/purple)
- [ ] Markers visible on ORANGE faces (should be cyan)
- [ ] Markers visible on WHITE faces (should be dark magenta)

**Actual:** _______________

### 1.3 Markers During Commutator Algorithm

**Steps:**
1. [ ] Use commutator solver on a larger cube (4x4 or 5x5)
2. [ ] Watch for markers during center/edge pairing

**Expected:**
- [ ] Source pieces clearly marked
- [ ] Target positions clearly marked
- [ ] Markers follow pieces during rotation animation

**Actual:** _______________

---

## 2. Animation Tests [HIGH]

### 2.1 Solve Animation Plays (Not Instant)

**Bug Reference:** B9 - Solve completes instantly (animation skipped)

**Steps:**
1. [ ] Start application
2. [ ] Press `R` to scramble
3. [ ] Press `S` to solve

**Expected:**
- [ ] Each move animates visibly (not instant)
- [ ] Can see cube rotating face by face
- [ ] Animation speed controllable with `+`/`-` keys

**Actual:** _______________

### 2.2 Animation Abort (ESC key)

**Steps:**
1. [ ] Scramble and start solve
2. [ ] Press `ESC` during solve animation

**Expected:**
- [ ] Animation stops immediately
- [ ] Cube state is consistent (not corrupted)
- [ ] Can continue with manual moves or new solve

**Actual:** _______________

---

## 3. Basic Cube Operations [MEDIUM]

### 3.1 Face Rotations

**Steps:**
1. [ ] Press `F`, `R`, `U`, `L`, `D`, `B` for clockwise rotations
2. [ ] Press `Shift+F`, etc. for counter-clockwise
3. [ ] Press `Ctrl+F`, etc. for double rotations

**Expected:**
- [ ] All rotations animate correctly
- [ ] Colors move to correct positions

### 3.2 Scramble and Reset

**Steps:**
1. [ ] Press `R` to scramble
2. [ ] Verify cube is scrambled
3. [ ] Press `Ctrl+R` to reset

**Expected:**
- [ ] Scramble produces random state
- [ ] Reset returns to solved state

---

## 4. Visual Features [LOW]

### 4.1 Celebration Effect

**Bug Reference:** B6 - Celebration triggers on reset

**Steps:**
1. [ ] Scramble cube
2. [ ] Solve cube (manually or with solver)
3. [ ] Observe celebration effect
4. [ ] Reset cube

**Expected:**
- [ ] Celebration triggers ONLY when going from scrambled to solved
- [ ] Celebration does NOT trigger on reset/resize

### 4.2 Shadow Faces (F10/F11/F12)

**Steps:**
1. [ ] Press F10, F11, F12 to toggle shadow faces

**Expected:**
- [ ] Shadow faces appear at offset positions
- [ ] L, D, B faces visible in shadow mode

---

## Test Log

| Date | Tester | Tests Run | Pass/Fail | Notes |
|------|--------|-----------|-----------|-------|
| | | | | |

---

## Adding New Bugs

When you find a GUI bug:

1. **Add test case here FIRST** with steps to reproduce
2. **Add to `todo/__todo.md`** with bug ID (B#)
3. **Then fix the bug**
4. **Update test case** with verification that fix works
