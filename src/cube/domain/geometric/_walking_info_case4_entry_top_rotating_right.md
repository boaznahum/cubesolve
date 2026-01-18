# Case 4: Entry TOP, Rotating RIGHT

## Physical Setup

- **Entry edge:** TOP (slice enters from top, exits at BOTTOM)
- **Rotating edge:** RIGHT (the rotating face is on the right side)
- **Slice orientation:** VERTICAL (because slice travels top → bottom)

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
                               ENTRY EDGE (TOP)
                               Slice enters here
                               slot=0 starts here
                                      │
                                      ▼
                    ┌─────────────────────────────────┐        ROTATING
                    │   ║         ║         ★         │           EDGE
                    │   ║         ║         ║         │          (RIGHT)
                    │   ║         ║         ║         │        slice[0]
                    │   ║         ║         ║         │        is here
                    │   ║         ║         ║         │            ║
                    │   ▼         ▼         ▼         │            ║
                    │  si=2      si=1      si=0       │            ║
                    └─────────────────────────────────┘            ║
                                      │
                                      ▼
                               EXIT EDGE (BOTTOM)
```

---

## Slice Coordinate System

```
                The slice travels VERTICALLY through the face.
                Each vertical strip is one slice.
                Slot increases from TOP to BOTTOM (opposite of +row).
                slice[0] is at RIGHT (si increases toward LEFT).

                           col=0    col=1    col=2
                             │        │        │
                             ▼        ▼        ▼
                    ┌──────────────────────────────┐
                    │   ║         ║         ★      │  slot=0
                    │   ║         ║         ║      │
                    │   ║         ║         ║      │  slot=1
                    │   ║         ║         ║      │
                    │   ▼         ▼         ▼      │  slot=2
                    │  si=2      si=1      si=0    │
                    └──────────────────────────────┘
                    ◄────
                     +si

                    Legend:
                    ★ = Reference point (si=0, slot=0) at TOP-RIGHT
                    ║▼ = Slice direction (slot increases going DOWN)


                    ┌─────────────────────────────────────┐
                    │                                     │
                    │   (row, col) = (inv(sl), inv(si))   │
                    │                                     │
                    │   row = inv(sl)  (slot inverted)    │
                    │   col = inv(si)  (slice_index inv)  │
                    │                                     │
                    └─────────────────────────────────────┘
```

---

## Why This Formula?

Since slices are **VERTICAL** columns:
- `slice_index (si)` determines **column**: si=0 → col=2 (rightmost, near rotating edge)
- `slot (sl)` determines **row**: slot=0 → row=2 (top, at entry edge), slot increases downward

Since si=0 is at RIGHT (col=n-1) and si increases toward LEFT:
- col = n-1 - si = inv(si)

Since slot=0 is at TOP (row=n-1) and increases toward BOTTOM (row=0):
- row = n-1 - slot = inv(sl)

**Formula: (row, col) = (inv(sl), inv(si))**

---

## Verification Table (n=3)

| si | slot | → | row=inv(sl) | col=inv(si) | Position      |
|----|------|---|-------------|-------------|---------------|
| 0  | 0    | → | 2           | 2           | top-right ★   |
| 0  | 1    | → | 1           | 2           | middle-right  |
| 0  | 2    | → | 0           | 2           | bottom-right  |
| 1  | 0    | → | 2           | 1           | top-center    |
| 2  | 2    | → | 0           | 0           | bottom-left   |
