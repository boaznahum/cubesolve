# RotatedBlock - Design Document

## Terminology

- **Kernel**: The normalized block from which all rotated variants are generated.
  A kernel always has `start.row <= end.row` AND `start.col <= end.col`.
  Every rotated block has exactly one kernel — its normalized form.

## Coordinate System (LTR)

- 7x7 face grid
- Row 0 at BOTTOM, row 6 at TOP
- Col 0 at LEFT, col 6 at RIGHT

## Face Layout

```
┌────┬────┬────┬────┬────┬────┬────┐
│ 60 │ 61 │ 62 │ 63 │ 64 │ 65 │ 66 │ ← top
├────┼────┼────┼────┼────┼────┼────┤
│ 50 │ 51 │ 52 │ 53 │ 54 │ 55 │ 56 │
├────┼────┼────┼────┼────┼────┼────┤
│ 40 │ 41 │ 42 │ 43 │ 44 │ 45 │ 46 │
├────┼────┼────┼────┼────┼────┼────┤
│ 30 │ 31 │ 32 │ 33 │ 34 │ 35 │ 36 │
├────┼────┼────┼────┼────┼────┼────┤
│ 20 │ 21 │ 22 │ 23 │ 24 │ 25 │ 26 │
├────┼────┼────┼────┼────┼────┼────┤
│ 10 │ 11 │ 12 │ 13 │ 14 │ 15 │ 16 │
├────┼────┼────┼────┼────┼────┼────┤
│ 00 │ 01 │ 02 │ 03 │ 04 │ 05 │ 06 │ ← bottom
└────┴────┴────┴────┴────┴────┴────┘
     ↑ col 0          col 6 ↑
```

## Block Example (Kernel)

**Kernel block:** `Block([1,2], [2,4])` - 2×3 block starting at row 1, col 2

```
┌────┬────┬────┬────┬────┬────┬────┐
│ 60 │ 61 │ 62 │ 63 │ 64 │ 65 │ 66 │
├────┼────┼────┼────┼────┼────┼────┤
│ 50 │ 51 │ 52 │ 53 │ 54 │ 55 │ 56 │
├────┼────┼────┼────┼────┼────┼────┤
│ 40 │ 41 │ 42 │ 43 │ 44 │ 45 │ 46 │
├────┼────┼────┼────┼────┼────┼────┤
│ 30 │ 31 │ 32 │ 33 │ 34 │ 35 │ 36 │
├────┼────┼────┼────┼────┼────┼────┤
│ 20 │ 21 │[22]│[23]│[24]│ 25 │ 26 │ ← row 2
├────┼────┼────┼────┼────┼────┼────┤
│ 10 │ 11 │[12]│[13]│[14]│ 15 │ 16 │ ← row 1
├────┼────┼────┼────┼────┼────┼────┤
│ 00 │ 01 │ 02 │ 03 │ 04 │ 05 │ 06 │
└────┴────┴────┴────┴────┴────┴────┘
          ↑ col 2
```

**Kernel cells:** `[12], [13], [14], [22], [23], [24]`

**Block.cells iterator yields (row by row):**
```
[1,2], [1,3], [1,4]  → cells 12, 13, 14
[2,2], [2,3], [2,4]  → cells 22, 23, 24
```

---

## Face Rotation - Step by Step

### Step 1: Kernel (before rotation)

**Format:** `cell_name@[current_coord]` | **BLOCK** cells highlighted

<table>
  <tr>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">60@[6,0]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">61@[6,1]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">62@[6,2]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">63@[6,3]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">64@[6,4]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">65@[6,5]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">66@[6,6]</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">50@[5,0]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">51@[5,1]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">52@[5,2]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">53@[5,3]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">54@[5,4]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">55@[5,5]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">56@[5,6]</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">40@[4,0]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">41@[4,1]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">42@[4,2]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">43@[4,3]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">44@[4,4]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">45@[4,5]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">46@[4,6]</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">30@[3,0]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">31@[3,1]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">32@[3,2]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">33@[3,3]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">34@[3,4]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">35@[3,5]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">36@[3,6]</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">20@[2,0]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">21@[2,1]</td>
    <td style="border: 3px solid #2563eb; padding: 6px; min-width: 60px; text-align: center; background-color: #dbeafe; color: #1e3a8a;">22@[2,2]</td>
    <td style="border: 3px solid #2563eb; padding: 6px; min-width: 60px; text-align: center; background-color: #dbeafe; color: #1e3a8a;">23@[2,3]</td>
    <td style="border: 3px solid #2563eb; padding: 6px; min-width: 60px; text-align: center; background-color: #dbeafe; color: #1e3a8a;">24@[2,4]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">25@[2,5]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">26@[2,6]</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">10@[1,0]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">11@[1,1]</td>
    <td style="border: 3px solid #2563eb; padding: 6px; min-width: 60px; text-align: center; background-color: #dbeafe; color: #1e3a8a;">12@[1,2]</td>
    <td style="border: 3px solid #2563eb; padding: 6px; min-width: 60px; text-align: center; background-color: #dbeafe; color: #1e3a8a;">13@[1,3]</td>
    <td style="border: 3px solid #2563eb; padding: 6px; min-width: 60px; text-align: center; background-color: #dbeafe; color: #1e3a8a;">14@[1,4]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">15@[1,5]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">16@[1,6]</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">00@[0,0]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">01@[0,1]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">02@[0,2]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">03@[0,3]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">04@[0,4]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">05@[0,5]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">06@[0,6]</td>
  </tr>
</table>

**Kernel block:** `Block([1,2], [2,4])`

**BLOCK cells (at kernel positions):**
```
12@[1,2] │ 13@[1,3] │ 14@[1,4]
22@[2,2] │ 23@[2,3] │ 24@[2,4]
```

**cells iterator order (row by row):**
```
[1,2] → cell 12
[1,3] → cell 13
[1,4] → cell 14
[2,2] → cell 22
[2,3] → cell 23
[2,4] → cell 24
```

---

### Step 2: After 90° CW face rotation

**Rotation call:** `block.rotate_clockwise(n_slices=7, n_rotations=1)`

**Rotation formula:** `(r, c) → (6-c, r)`

**Result:** `Block([2,1], [4,2])` - 3×2 vertical block at cols 1-2, rows 2-4

**Format:** `cell_name@[new_coord]` | **BLOCK** cells highlighted

<table>
  <tr>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">00@[6,0]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">01@[6,1]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">02@[6,2]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">03@[6,3]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">04@[6,4]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">05@[6,5]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">06@[6,6]</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">10@[5,0]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">11@[5,1]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">12@[5,2]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">13@[5,3]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">14@[5,4]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">15@[5,5]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">16@[5,6]</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">20@[4,0]</td>
    <td style="border: 3px solid #2563eb; padding: 6px; min-width: 60px; text-align: center; background-color: #dbeafe; color: #1e3a8a;">12@[4,1]</td>
    <td style="border: 3px solid #2563eb; padding: 6px; min-width: 60px; text-align: center; background-color: #dbeafe; color: #1e3a8a;">22@[4,2]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">23@[4,3]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">24@[4,4]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">25@[4,5]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">26@[4,6]</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">30@[3,0]</td>
    <td style="border: 3px solid #2563eb; padding: 6px; min-width: 60px; text-align: center; background-color: #dbeafe; color: #1e3a8a;">13@[3,1]</td>
    <td style="border: 3px solid #2563eb; padding: 6px; min-width: 60px; text-align: center; background-color: #dbeafe; color: #1e3a8a;">23@[3,2]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">33@[3,3]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">34@[3,4]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">35@[3,5]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">36@[3,6]</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">40@[2,0]</td>
    <td style="border: 3px solid #2563eb; padding: 6px; min-width: 60px; text-align: center; background-color: #dbeafe; color: #1e3a8a;">14@[2,1]</td>
    <td style="border: 3px solid #2563eb; padding: 6px; min-width: 60px; text-align: center; background-color: #dbeafe; color: #1e3a8a;">24@[2,2]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">43@[2,3]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">44@[2,4]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">45@[2,5]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">46@[2,6]</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">50@[1,0]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">51@[1,1]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">52@[1,2]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">53@[1,3]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">54@[1,4]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">55@[1,5]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">56@[1,6]</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">60@[0,0]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">61@[0,1]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">62@[0,2]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">63@[0,3]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">64@[0,4]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">65@[0,5]</td>
    <td style="border: 1px solid #ccc; padding: 6px; min-width: 60px; text-align: center;">66@[0,6]</td>
  </tr>
</table>

**Rotated block (normalized):** `Block([2,1], [4,2])`

**BLOCK cells (at new positions):**
```
14@[2,1] │ 24@[2,2]
13@[3,1] │ 23@[3,2]
12@[4,1] │ 22@[4,2]
```

**cells iterator order (row by row on normalized block):**
```
[2,1] → cell 14
[2,2] → cell 24
[3,1] → cell 13
[3,2] → cell 23
[4,1] → cell 12
[4,2] → cell 22
```

---

### Key Observations

1. **Same format:** Both before and after use `cell@[coord]` format
2. **Rotation transformation:** `block.rotate_clockwise(7)` uses formula `(r, c) → (6-c, r)`
3. **Block shape changed:** 2×3 horizontal → 3×2 vertical
4. **All 6 cells preserved:** All kernel cells exist in the rotated block, but at different positions

---

### CRITICAL: cells Iterator Comparison

**Kernel** - `Block([1,2], [2,4])` - 2×3 block
```
cells iterator order:  [1,2], [1,3], [1,4], [2,2], [2,3], [2,4]
cells at positions:    12,    13,    14,    22,    23,    24
```

**After 90° CW** - `Block([2,1], [4,2])` - 3×2 block
```
cells iterator order:  [2,1], [2,2], [3,1], [3,2], [4,1], [4,2]
cells at positions:    14,    24,    13,    23,    12,    22
```

**KEY INSIGHT:**
1. Block shape changed (2×3 → 3×2)
2. All 6 kernel cells are preserved in the rotated block
3. Iterator yields all 6 positions, each with a block cell
4. Cell order in iterator: `14, 24, 13, 23, 12, 22` (completely different from kernel `12, 13, 14, 22, 23, 24`)
5. This is why `RotatedBlock.iterate_points` exists — it iterates in **kernel order** while yielding **rotated positions**

---

### Step 3: After 180° face rotation

**Rotation call:** `block.rotate_clockwise(n_slices=7, n_rotations=2)`

**Rotation formula:** `(r, c) → (6-r, 6-c)` (applies 90° rotation twice)

**Result:** `Block([4,2], [5,4])` - 2×3 horizontal block at cols 2-4, rows 4-5

**BLOCK cells (at new positions):**
```
14@[5,2] │ 13@[5,3] │ 12@[5,4]
24@[4,2] │ 23@[4,3] │ 22@[4,4]
```

**cells iterator order (row by row):**
```
[4,2] → cell 24
[4,3] → cell 23
[4,4] → cell 22
[5,2] → cell 14
[5,3] → cell 13
[5,4] → cell 12
```

---

### Step 4: After 270° CW face rotation (or 90° CCW)

**Rotation call:** `block.rotate_clockwise(n_slices=7, n_rotations=3)`

**Rotation formula:** `(r, c) → (c, 6-r)` (applies 90° rotation three times)

**Result:** `Block([2,4], [4,5])` - 3×2 vertical block at cols 4-5, rows 2-4

**BLOCK cells (at new positions):**
```
22@[2,4] │ 12@[2,5]
23@[3,4] │ 13@[3,5]
24@[4,4] │ 14@[4,5]
```

**cells iterator order (row by row):**
```
[2,4] → cell 22
[2,5] → cell 12
[3,4] → cell 23
[3,5] → cell 13
[4,4] → cell 24
[4,5] → cell 14
```

---

## Summary of All Rotations

| Rotation | Formula | Result Block | Shape | Cell Order (iterator) |
|----------|---------|--------------|-------|----------------------|
| 0° (kernel) | - | `Block([1,2], [2,4])` | 2×3 horizontal | 12, 13, 14, 22, 23, 24 |
| 90° CW | `(r,c) → (6-c, r)` | `Block([2,1], [4,2])` | 3×2 vertical | 14, 24, 13, 23, 12, 22 |
| 180° | `(r,c) → (6-r, 6-c)` | `Block([4,2], [5,4])` | 2×3 horizontal | 24, 23, 22, 14, 13, 12 |
| 270° CW | `(r,c) → (c, 6-r)` | `Block([2,4], [4,5])` | 3×2 vertical | 22, 12, 23, 13, 24, 14 |

**Key Insight:** The cell order in the iterator changes with each rotation, even though all 6 cells are always preserved.
The kernel defines the canonical ordering; `iterate_points` restores this ordering for any rotation.

---

## Detecting Block Orientation

### Mathematical Foundation

**Definitions:**
- A **kernel** (normalized block) has: `start.row <= end.row` AND `start.col <= end.col`
- A **rotated** block (unnormalized) violates one or both of these constraints

**Corner Exchange During 90° CW Rotation:**

When a kernel block rotates 90° clockwise, the corners exchange positions:

| Kernel Corner | After 90° CW | New Corner Position |
|---------------|--------------|---------------------|
| Top-Left `[r1, c1]` | `[N-1-c1, r1]` | **Top-Right** |
| Bottom-Left `[r2, c1]` | `[N-1-c1, r2]` | **Bottom-Right** |
| Top-Right `[r1, c2]` | `[N-1-c2, r1]` | **Top-Left** |
| Bottom-Right `[r2, c2]` | `[N-1-c2, r2]` | **Bottom-Left** |

**Key Observation:** The rotated (unnormalized) block has:
- **start point** = the former **Top-Right corner** `[r1, c2]`
- **end point** = the former **Bottom-Left corner** `[r2, c1]`

### The Detection Signal

For a kernel with `r1 <= r2` and `c1 <= c2`, after rotation:

| Rotation | Start row vs End row | Start col vs End col |
|----------|---------------------|---------------------|
| 0° (kernel) | `r1 <= r2` | `c1 <= c2` |
| 90° CW | `r1 > r2` (when c1 < c2) or `r1 >= r2` | `c1 <= c2` |
| 180° | `r1 > r2` (when r1 < r2) or `r1 >= r2` | `c1 > c2` (when c1 < c2) or `c1 >= c2` |
| 270° CW | `r1 <= r2` | `c1 > c2` (when r1 < r2) or `c1 >= c2` |

### Detection Rules (as implemented)

```python
def detect_n_rotations(start, end) -> int:
    r1, c1 = start
    r2, c2 = end

    if r1 <= r2 and c1 <= c2: return 0  # kernel
    if r1 > r2  and c1 <= c2: return 1  # 90° CW
    if r1 <= r2 and c1 > c2:  return 3  # 270° CW
    return 2                              # 180°
```

**Note:** The conditions use non-strict inequalities (`<=`) to correctly handle
single-row blocks (r1 == r2) and single-column blocks (c1 == c2) after rotation.
For example, a single-column kernel rotated 90° CW produces `r1 > r2, c1 == c2`,
which must be detected as rot=1, not rot=2.

### Practical Application

**Detection Rule:**
```python
def is_rotated(block: Block) -> bool:
    """Detect if block is not a kernel (has been rotated)."""
    return block.start.row > block.end.row or block.start.col > block.end.col
```

**iterate_points behavior:**
- **Kernel block** (`r1 <= r2, c1 <= c2`): Iterate directly, no transform needed
- **Rotated block**: Recover kernel corners from rotated corners, iterate in kernel order, yield rotated positions — all inlined in one fused loop

This signal allows us to determine the correct iteration order without storing additional metadata!

---

## iterate_points — Optimized Kernel-Order Iteration

The `RotatedBlock.iterate_points(start, end, n_slices)` static method is the core
of the optimization. It fuses three steps into one loop per rotation case:

1. **Detect rotation** from corner relationships
2. **Recover kernel corners** via reverse rotation (baked into range bounds)
3. **Yield rotated positions** via forward rotation (baked into yield expression)

```
For rot=1 (90° CW):
  kernel corners: (c1, nm1-r1) to (c2, nm1-r2)    ← reverse rotation in range bounds
  yield: Point(nm1-c, r)                            ← forward rotation in yield

  for r in range(c1, c2+1):
      for c in range(nm1-r1, nm1-r2+1):
          yield Point(nm1-c, r)
```

No per-point function calls. No separate kernel recovery step. The kernel defines
the iteration order implicitly through the range bounds.
