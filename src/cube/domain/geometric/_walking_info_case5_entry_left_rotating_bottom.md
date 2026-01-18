# Case 5: Entry LEFT, Rotating BOTTOM

## Physical Setup

- **Entry edge:** LEFT (slice enters from left, exits at RIGHT)
- **Rotating edge:** BOTTOM (the rotating face is on the bottom)
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
     ENTRY EDGE                                              EXIT EDGE
       (LEFT)                                                 (RIGHT)
  Slice enters here                                      Slice exits here
   slot=0 starts here                                           │
          │                                                     ▼
          │         ┌─────────────────────────────────┐
          └────────►│   ════════════════════════►     │  si=2
                    │                                 │
                    │   ════════════════════════►     │  si=1
                    │                                 │
                    │   ★═══════════════════════►     │  si=0
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
                Slot increases from LEFT to RIGHT (same as +col).
                slice[0] is at BOTTOM (si increases upward).

                           col=0    col=1    col=2
                             │        │        │
                             ▼        ▼        ▼
                    ┌──────────────────────────────┐
                    │   ════════════════════════►  │  si=2
                    │                              │
                    │   ════════════════════════►  │  si=1
                    │                              │    ▲
                    │   ★══════════════════════►   │  si=0
                    └──────────────────────────────┘    │
                       slot=0  slot=1  slot=2         +si

                    Legend:
                    ★ = Reference point (si=0, slot=0) at BOTTOM-LEFT
                    ═══► = Slice direction (slot increases going RIGHT)


                    ┌─────────────────────────────────────┐
                    │                                     │
                    │   (row, col) = (si, sl)             │
                    │                                     │
                    │   row = si   (slice_index)          │
                    │   col = sl   (slot)                 │
                    │                                     │
                    └─────────────────────────────────────┘
```

---

## Why This Formula?

Since slices are **HORIZONTAL** rows:
- `slice_index (si)` determines **row**: si=0 → row=0 (bottom, near rotating edge)
- `slot (sl)` determines **column**: slot=0 → col=0 (left, at entry edge), slot increases rightward

Since si=0 is at BOTTOM (row=0) and si increases toward TOP:
- row = si

Since slot=0 is at LEFT (col=0) and increases toward RIGHT:
- col = slot = sl

**Formula: (row, col) = (si, sl)**

---

## Verification Table (n=3)

| si | slot | → | row | col | Position      |
|----|------|---|-----|-----|---------------|
| 0  | 0    | → | 0   | 0   | bottom-left ★ |
| 0  | 1    | → | 0   | 1   | bottom-center |
| 0  | 2    | → | 0   | 2   | bottom-right  |
| 1  | 0    | → | 1   | 0   | middle-left   |
| 2  | 2    | → | 2   | 2   | top-right     |
