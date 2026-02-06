# RotatedBlock - Design Document

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

## Block Example

**Block:** `Block([1,2], [2,4])` - 2×3 block starting at row 1, col 2

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

**Block cells:** `[12], [13], [14], [22], [23], [24]`

**Block.cells iterator yields (row by row):**
```
[1,2], [1,3], [1,4]  → cells 12, 13, 14
[2,2], [2,3], [2,4]  → cells 22, 23, 24
```

---

## Face Rotation - Step by Step

### Step 1: Original face (before rotation)

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

**Original block:** `Block([1,2], [2,4])`

**BLOCK cells (at original positions):**
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

**Rotated block:** `Block([2,1], [4,2])`

**BLOCK cells (at new positions):**
```
14@[2,3] │ 24@[2,2]
12@[3,2] │ 13@[3,3]
22@[4,2] │ 23@[4,3]
```

**cells iterator order (row by row):**
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
4. **All 6 cells preserved:** All original cells exist in the rotated block, but at different positions

---

### CRITICAL: cells Iterator Comparison

**BEFORE rotation** - `Block([1,2], [2,4])` - 2×3 block
```
cells iterator order:  [1,2], [1,3], [1,4], [2,2], [2,3], [2,4]
cells at positions:    12,    13,    14,    22,    23,    24
```

**AFTER rotation** - `Block([2,1], [4,2])` - 3×2 block
```
cells iterator order:  [2,1], [2,2], [3,1], [3,2], [4,1], [4,2]
cells at positions:    14,    24,    13,    23,    12,    22
```

**⚠️ KEY INSIGHT:**
1. Block shape changed (2×3 → 3×2)
2. All 6 original cells are preserved in the rotated block
3. Iterator yields all 6 positions, each with a block cell
4. Cell order in iterator: `14, 24, 13, 23, 12, 22` (completely different from original `12, 13, 14, 22, 23, 24`)
