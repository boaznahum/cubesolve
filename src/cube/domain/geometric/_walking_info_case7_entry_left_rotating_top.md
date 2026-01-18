# Case 7: Entry LEFT, Rotating TOP

## Physical Setup

- **Entry edge:** LEFT (slice enters from left, exits at RIGHT)
- **Rotating edge:** TOP (the rotating face is on the top)
- **Slice orientation:** HORIZONTAL (because slice travels left → right)

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
                              ════════════════
                              ROTATING EDGE (TOP)
                              slice[0] is here
                    ┌─────────────────────────────────┐
                    │   ★═══════════════════════►     │  si=0
                    │                                 │
                    │   ════════════════════════►     │  si=1
                    │                                 │
                    │   ════════════════════════►     │  si=2
          │         └─────────────────────────────────┘
          │                                                     │
          └────────►                                            ▼
     ENTRY EDGE                                              EXIT EDGE
       (LEFT)                                                 (RIGHT)
  Slice enters here                                      Slice exits here
   slot=0 starts here
```

---

## Slice Coordinate System

```
                The slice travels HORIZONTALLY through the face.
                Each horizontal strip is one slice.
                Slot increases from LEFT to RIGHT (same as +col).
                slice[0] is at TOP (si increases downward).

                           col=0    col=1    col=2
                             │        │        │
                             ▼        ▼        ▼
                    ┌──────────────────────────────┐
                    │   ★══════════════════════►   │  si=0
                    │                              │    │
                    │   ════════════════════════►  │  si=1
                    │                              │    │
                    │   ════════════════════════►  │  si=2
                    └──────────────────────────────┘    ▼
                       slot=0  slot=1  slot=2         +si

                    Legend:
                    ★ = Reference point (si=0, slot=0) at TOP-LEFT
                    ═══► = Slice direction (slot increases going RIGHT)


                    ┌─────────────────────────────────────┐
                    │                                     │
                    │   (row, col) = (inv(si), sl)        │
                    │                                     │
                    │   row = inv(si)  (slice_index inv)  │
                    │   col = sl       (slot)             │
                    │                                     │
                    └─────────────────────────────────────┘
```

---

## Why This Formula?

Since slices are **HORIZONTAL** rows:
- `slice_index (si)` determines **row**: si=0 → row=2 (top, near rotating edge)
- `slot (sl)` determines **column**: slot=0 → col=0 (left, at entry edge), slot increases rightward

Since si=0 is at TOP (row=n-1) and si increases toward BOTTOM:
- row = n-1 - si = inv(si)

Since slot=0 is at LEFT (col=0) and increases toward RIGHT:
- col = slot = sl

**Formula: (row, col) = (inv(si), sl)**

---

## Verification Table (n=3)

| si | slot | → | row=inv(si) | col | Position      |
|----|------|---|-------------|-----|---------------|
| 0  | 0    | → | 2           | 0   | top-left ★    |
| 0  | 1    | → | 2           | 1   | top-center    |
| 0  | 2    | → | 2           | 2   | top-right     |
| 1  | 0    | → | 1           | 0   | middle-left   |
| 2  | 2    | → | 0           | 2   | bottom-right  |
