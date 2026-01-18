# Case 6: Entry RIGHT, Rotating BOTTOM

## Physical Setup

- **Entry edge:** RIGHT (slice enters from right, exits at LEFT)
- **Rotating edge:** BOTTOM (the rotating face is on the bottom)
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
     EXIT EDGE                                               ENTRY EDGE
       (LEFT)                                                  (RIGHT)
  Slice exits here                                        Slice enters here
          │                                              slot=0 starts here
          ▼                                                     │
                    ┌─────────────────────────────────┐         │
                    │   ◄════════════════════════     │  si=2 ◄─┘
                    │                                 │
                    │   ◄════════════════════════     │  si=1
                    │                                 │
                    │   ◄═══════════════════════ ★    │  si=0
                    └─────────────────────────────────┘
                              ════════════════
                              ROTATING EDGE (BOTTOM)
                              slice[0] is here
```

---

## Slice Coordinate System

```
                The slice travels HORIZONTALLY through the face.
                Each horizontal strip is one slice.
                Slot increases from RIGHT to LEFT (opposite of +col).
                slice[0] is at BOTTOM (si increases upward).

                           col=0    col=1    col=2
                             │        │        │
                             ▼        ▼        ▼
                    ┌──────────────────────────────┐
                    │   ◄════════════════════════  │  si=2
                    │                              │
                    │   ◄════════════════════════  │  si=1
                    │                              │    ▲
                    │   ◄══════════════════════ ★  │  si=0
                    └──────────────────────────────┘    │
                       slot=2  slot=1  slot=0         +si

                    Legend:
                    ★ = Reference point (si=0, slot=0) at BOTTOM-RIGHT
                    ◄═══ = Slice direction (slot increases going LEFT)


                    ┌─────────────────────────────────────┐
                    │                                     │
                    │   (row, col) = (si, inv(sl))        │
                    │                                     │
                    │   row = si       (slice_index)      │
                    │   col = inv(sl)  (slot inverted)    │
                    │                                     │
                    └─────────────────────────────────────┘
```

---

## Why This Formula?

Since slices are **HORIZONTAL** rows:
- `slice_index (si)` determines **row**: si=0 → row=0 (bottom, near rotating edge)
- `slot (sl)` determines **column**: slot=0 → col=2 (right, at entry edge), slot increases leftward

Since si=0 is at BOTTOM (row=0) and si increases toward TOP:
- row = si

Since slot=0 is at RIGHT (col=n-1) and increases toward LEFT:
- col = n-1 - slot = inv(sl)

**Formula: (row, col) = (si, inv(sl))**

---

## Verification Table (n=3)

| si | slot | → | row | col=inv(sl) | Position      |
|----|------|---|-----|-------------|---------------|
| 0  | 0    | → | 0   | 2           | bottom-right ★|
| 0  | 1    | → | 0   | 1           | bottom-center |
| 0  | 2    | → | 0   | 0           | bottom-left   |
| 1  | 0    | → | 1   | 2           | middle-right  |
| 2  | 2    | → | 2   | 0           | top-left      |
