# Walking Info: 8 Cases Summary

## Coordinate Systems

**Face coordinates:** `(row, col)` with origin at bottom-left
- `row` increases upward (0 = bottom, n-1 = top)
- `col` increases rightward (0 = left, n-1 = right)

**Slice coordinates:** `(sindex, slot)`
- `sindex` = slice_index (0 = closest to rotating face)
- `slot` = position along the slice (0 = at entry edge)
- `inv(x)` = n-1 - x (where n = number of slices)

---

## Summary Table

| Case | Entry | Rotating | Orientation | Formula `(row, col)` | Reference ★ |
|------|-------|----------|-------------|----------------------|-------------|
| 1 | BOTTOM | LEFT | VERTICAL | `(slot, sindex)` | bottom-left |
| 2 | TOP | LEFT | VERTICAL | `(inv(slot), sindex)` | top-left |
| 3 | BOTTOM | RIGHT | VERTICAL | `(slot, inv(sindex))` | bottom-right |
| 4 | TOP | RIGHT | VERTICAL | `(inv(slot), inv(sindex))` | top-right |
| 5 | LEFT | BOTTOM | HORIZONTAL | `(sindex, slot)` | bottom-left |
| 6 | RIGHT | BOTTOM | HORIZONTAL | `(sindex, inv(slot))` | bottom-right |
| 7 | LEFT | TOP | HORIZONTAL | `(inv(sindex), slot)` | top-left |
| 8 | RIGHT | TOP | HORIZONTAL | `(inv(sindex), inv(slot))` | top-right |

---

## Pattern

**Entry BOTTOM/TOP → VERTICAL slices:**
- `sindex` determines **column** (which vertical strip)
- `slot` determines **row** (position along the strip)
- Formula: `(row, col) = (slot-variant, sindex-variant)`

**Entry LEFT/RIGHT → HORIZONTAL slices:**
- `sindex` determines **row** (which horizontal strip)
- `slot` determines **column** (position along the strip)
- Formula: `(row, col) = (sindex-variant, slot-variant)`

---

## Inversion Rules

| Condition | Result |
|-----------|--------|
| Entry is BOTTOM or LEFT | slot NOT inverted |
| Entry is TOP or RIGHT | slot IS inverted |
| Rotating is LEFT or BOTTOM | sindex NOT inverted |
| Rotating is RIGHT or TOP | sindex IS inverted |

---

## Files

- `_walking_info_case1_entry_bottom_rotating_left.md`
- `_walking_info_case2_entry_top_rotating_left.md`
- `_walking_info_case3_entry_bottom_rotating_right.md`
- `_walking_info_case4_entry_top_rotating_right.md`
- `_walking_info_case5_entry_left_rotating_bottom.md`
- `_walking_info_case6_entry_right_rotating_bottom.md`
- `_walking_info_case7_entry_left_rotating_top.md`
- `_walking_info_case8_entry_right_rotating_top.md`
