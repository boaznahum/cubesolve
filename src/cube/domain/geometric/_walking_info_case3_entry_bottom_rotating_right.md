# Case 3: Entry BOTTOM, Rotating RIGHT

## Physical Setup

- **Entry edge:** BOTTOM (slice enters from bottom, exits at TOP)
- **Rotating edge:** RIGHT (the rotating face is on the right side)
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
                    ┌─────────────────────────────────┐        ROTATING
                    │   ▲         ▲         ▲         │           EDGE
                    │   ║         ║         ║         │          (RIGHT)
                    │   ║         ║         ║         │        slice[0]
                    │   ║         ║         ║         │        is here
                    │   ║         ║         ║         │            ║
                    │   ║         ║         ★         │            ║
                    │  si=2      si=1      si=0       │            ║
                    └─────────────────────────────────┘            ║
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
                slice[0] is at RIGHT (si increases toward LEFT).

                           col=0    col=1    col=2
                             │        │        │
                             ▼        ▼        ▼
                    ┌──────────────────────────────┐
                    │   ▲         ▲         ▲      │  slot=2
                    │   ║         ║         ║      │
                    │   ║         ║         ║      │  slot=1
                    │   ║         ║         ║      │
                    │   ║         ║         ★      │  slot=0
                    │  si=2      si=1      si=0    │
                    └──────────────────────────────┘
                    ◄────
                     +si

                    Legend:
                    ★ = Reference point (si=0, slot=0) at BOTTOM-RIGHT
                    ║▲ = Slice direction (slot increases going UP)


                    ┌─────────────────────────────────────┐
                    │                                     │
                    │   (row, col) = (sl, inv(si))        │
                    │                                     │
                    │   row = sl       (slot)             │
                    │   col = inv(si)  (slice_index inv)  │
                    │                                     │
                    └─────────────────────────────────────┘
```

---

## Why This Formula?

Since slices are **VERTICAL** columns:
- `slice_index (si)` determines **column**: si=0 → col=2 (rightmost, near rotating edge)
- `slot (sl)` determines **row**: slot=0 → row=0 (bottom, at entry edge), slot increases upward

Since si=0 is at RIGHT (col=n-1) and si increases toward LEFT:
- col = n-1 - si = inv(si)

Since slot=0 is at BOTTOM (row=0) and increases toward TOP:
- row = slot = sl

**Formula: (row, col) = (sl, inv(si))**

---

## Verification Table (n=3)

| si | slot | → | row | col=inv(si) | Position      |
|----|------|---|-----|-------------|---------------|
| 0  | 0    | → | 0   | 2           | bottom-right ★|
| 0  | 1    | → | 1   | 2           | middle-right  |
| 0  | 2    | → | 2   | 2           | top-right     |
| 1  | 0    | → | 0   | 1           | bottom-center |
| 2  | 2    | → | 2   | 0           | top-left      |
