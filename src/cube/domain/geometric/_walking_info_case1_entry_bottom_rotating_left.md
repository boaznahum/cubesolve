# Case 1: Entry BOTTOM, Rotating LEFT

## Physical Setup

- **Entry edge:** BOTTOM (slice enters from bottom, exits at TOP)
- **Rotating edge:** LEFT (the rotating face is on the left side)
- **Slice orientation:** VERTICAL (because slice travels bottom → top)

---

## Face Coordinate System

```
                         col=0    col=1    col=2
                           │        │        │
                           ▼        ▼        ▼
                    ┌──────────────────────────────┐
                    │                              │
         row=2 ──►  │                              │  ▲
                    │                              │  │
                    │                              │  │ +row
         row=1 ──►  │                              │  │
                    │                              │  │
                    │                              │  │
         row=0 ──►  │                              │
                    │                              │
                    └──────────────────────────────┘
                              ───────►
                                +col
```

---

## Slice on the Face

```
                               EXIT EDGE (TOP)
                                      ▲
                                      │
        ROTATING        ┌─────────────────────────────────┐
           EDGE         │   ▲         ▲         ▲         │
          (LEFT)        │   ║         ║         ║         │
        slice[0]        │   ║         ║         ║         │
        is here         │   ║         ║         ║         │
            ║           │   ║         ║         ║         │
            ║           │   ★         ║         ║         │
            ║           │  si=0      si=1      si=2       │
            ║           └─────────────────────────────────┘
                                      ▲
                                      │
                               ENTRY EDGE (BOTTOM)
                               Slice enters here
                               slot=0 starts here
```

---

## Slice Coordinate System

```
                The slice travels VERTICALLY through the face.
                Each vertical strip is one slice.
                Slot increases from BOTTOM to TOP (same as +row).

                           col=0    col=1    col=2
                             │        │        │
                             ▼        ▼        ▼
                    ┌──────────────────────────────┐
                    │   ▲         ▲         ▲      │  slot=2
                    │   ║         ║         ║      │
                    │   ║         ║         ║      │  slot=1
                    │   ║         ║         ║      │
                    │   ★         ║         ║      │  slot=0
                    │  si=0      si=1      si=2    │
                    └──────────────────────────────┘
                                             ────►
                                              +si

                    Legend:
                    ★ = Reference point (si=0, slot=0) at BOTTOM-LEFT
                    ║▲ = Slice direction (slot increases going UP)


                    ┌─────────────────────────────────────┐
                    │                                     │
                    │   (row, col) = (sl, si)             │
                    │                                     │
                    │   row = sl   (slot)                 │
                    │   col = si   (slice_index)          │
                    │                                     │
                    └─────────────────────────────────────┘
```

---

## Why This Formula?

Since slices are **VERTICAL** columns:
- `slice_index (si)` determines **column**: si=0 → col=0 (leftmost, near rotating edge)
- `slot (sl)` determines **row**: slot=0 → row=0 (bottom, at entry edge), slot increases upward

Since slot=0 is at BOTTOM (row=0) and increases toward TOP (row=n-1):
- row = slot = sl

**Formula: (row, col) = (sl, si)**

---

## Verification Table (n=3)

| si | slot | → | row | col | Position     |
|----|------|---|-----|-----|--------------|
| 0  | 0    | → | 0   | 0   | bottom-left ★|
| 0  | 1    | → | 1   | 0   | middle-left  |
| 0  | 2    | → | 2   | 0   | top-left     |
| 1  | 0    | → | 0   | 1   | bottom-center|
| 2  | 2    | → | 2   | 2   | top-right    |
