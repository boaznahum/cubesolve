# Case 8: Entry RIGHT, Rotating TOP

## Physical Setup

- **Entry edge:** RIGHT (slice enters from right, exits at LEFT)
- **Rotating edge:** TOP (the rotating face is on the top)
- **Slice orientation:** HORIZONTAL (because slice travels right → left)

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
                    │     ◄═══════════════════════★   │  si=0
                    │                                 │
                    │     ◄═══════════════════════    │  si=1
                    │                                 │
                    │     ◄═══════════════════════    │  si=2
          │         └─────────────────────────────────┘
          │                                                     │
          ▼                                            ◄────────┘
     EXIT EDGE                                              ENTRY EDGE
       (LEFT)                                                 (RIGHT)
  Slice exits here                                       Slice enters here
                                                          slot=0 starts here
```

---

## Slice Coordinate System

```
                The slice travels HORIZONTALLY through the face.
                Each horizontal strip is one slice.
                Slot increases from RIGHT to LEFT (opposite of +col).
                slice[0] is at TOP (si increases downward).

                           col=0    col=1    col=2
                             │        │        │
                             ▼        ▼        ▼
                    ┌──────────────────────────────┐
                    │   ◄══════════════════════ ★  │  si=0
                    │                              │    │
                    │   ◄════════════════════════  │  si=1
                    │                              │    │
                    │   ◄════════════════════════  │  si=2
                    └──────────────────────────────┘    ▼
                       slot=2  slot=1  slot=0         +si

                    Legend:
                    ★ = Reference point (si=0, slot=0) at TOP-RIGHT
                    ◄═══ = Slice direction (slot increases going LEFT)


                    ┌─────────────────────────────────────┐
                    │                                     │
                    │   (row, col) = (inv(si), inv(sl))   │
                    │                                     │
                    │   row = inv(si)  (slice_index inv)  │
                    │   col = inv(sl)  (slot inverted)    │
                    │                                     │
                    └─────────────────────────────────────┘
```

---

## Why This Formula?

Since slices are **HORIZONTAL** rows:
- `slice_index (si)` determines **row**: si=0 → row=2 (top, near rotating edge)
- `slot (sl)` determines **column**: slot=0 → col=2 (right, at entry edge), slot increases leftward

Since si=0 is at TOP (row=n-1) and si increases toward BOTTOM:
- row = n-1 - si = inv(si)

Since slot=0 is at RIGHT (col=n-1) and increases toward LEFT:
- col = n-1 - slot = inv(sl)

**Formula: (row, col) = (inv(si), inv(sl))**

---

## Verification Table (n=3)

| si | slot | → | row=inv(si) | col=inv(sl) | Position      |
|----|------|---|-------------|-------------|---------------|
| 0  | 0    | → | 2           | 2           | top-right ★   |
| 0  | 1    | → | 2           | 1           | top-center    |
| 0  | 2    | → | 2           | 0           | top-left      |
| 1  | 0    | → | 1           | 2           | middle-right  |
| 2  | 2    | → | 0           | 0           | bottom-left   |
