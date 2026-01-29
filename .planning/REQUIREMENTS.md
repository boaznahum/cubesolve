# Requirements: Big-LBL L3 Edges

**Defined:** 2025-01-29
**Core Value:** L3 edge pairing must NOT touch L1 or middle layer edges

## v1 Requirements

### Infrastructure

- [ ] **INFRA-01**: Create `_LBLL3Edges.py` helper class
- [ ] **INFRA-02**: Main method accepts `faces_tracker` parameter
- [ ] **INFRA-03**: Methods return `Alg` for undo via `.prime` operator
- [ ] **INFRA-04**: Logging with `self._logger.tab(lambda: ...)`

### Main Loop

- [ ] **LOOP-01**: Bring L3 to front at start
- [ ] **LOOP-02**: Loop 4x rotating cube around front center
- [ ] **LOOP-03**: Each iteration solves left edge
- [ ] **LOOP-04**: While loop with progress check (increase in solved edges)
- [ ] **LOOP-05**: Max iterations guard (raise error if exceeded)

### Source Matching

- [ ] **MATCH-01**: Skip already-solved wings
- [ ] **MATCH-02**: Find sources by `colors_id` match
- [ ] **MATCH-03**: Match index i or inv(i)
- [ ] **MATCH-04**: For odd cube middle wing, inv(i) == i

### Orientation Check

- [ ] **ORIENT-01**: Check source wing color on front vs L3 color
- [ ] **ORIENT-02**: If colors match: ti == si required
- [ ] **ORIENT-03**: If colors don't match: ti == inv(si), needs flip

### Case Handlers

- [ ] **CASE-01**: FR→FL: Setup + right CM + U rotate + left CM + rollback
- [ ] **CASE-02**: FU→FL: Setup + left CM + rollback
- [ ] **CASE-03**: FD→FL: Setup + F + (left CM)' + F' + rollback
- [ ] **CASE-04**: FL→FL: Setup + left CM x2 + flip + left CM + rollback

### Algorithms

- [ ] **ALG-01**: Left CM: `U' L' U M[k]' U' L U M[k]`
- [ ] **ALG-02**: Right CM: `U R U' M[k]' U R' U' M[k]`
- [ ] **ALG-03**: Flip FU (preserve FL): `U'² B' R' U`
- [ ] **ALG-04**: Flip FL: TBD
- [ ] **ALG-05**: Protect BU: bring FB to BU

### Integration

- [ ] **INTEG-01**: Called from `LayerByLayerNxNSolver._solve_layer3_edges()`
- [ ] **INTEG-02**: Works for 5x5, 6x6, 7x7+ cubes

## Out of Scope

| Feature | Reason |
|---------|--------|
| L3 corners | Separate solving step, not part of this |
| Performance optimization | Correctness first |
| Reducer solver changes | Different approach |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 1 | Pending |
| INFRA-02 | Phase 1 | Pending |
| INFRA-03 | Phase 1 | Pending |
| INFRA-04 | Phase 1 | Pending |
| LOOP-01 | Phase 2 | Pending |
| LOOP-02 | Phase 2 | Pending |
| LOOP-03 | Phase 2 | Pending |
| LOOP-04 | Phase 2 | Pending |
| LOOP-05 | Phase 2 | Pending |
| MATCH-01 | Phase 3 | Pending |
| MATCH-02 | Phase 3 | Pending |
| MATCH-03 | Phase 3 | Pending |
| MATCH-04 | Phase 3 | Pending |
| ORIENT-01 | Phase 3 | Pending |
| ORIENT-02 | Phase 3 | Pending |
| ORIENT-03 | Phase 3 | Pending |
| ALG-01 | Phase 4 | Pending |
| ALG-02 | Phase 4 | Pending |
| ALG-03 | Phase 4 | Pending |
| ALG-04 | Phase 4 | Pending |
| ALG-05 | Phase 4 | Pending |
| CASE-01 | Phase 5 | Pending |
| CASE-02 | Phase 5 | Pending |
| CASE-03 | Phase 5 | Pending |
| CASE-04 | Phase 5 | Pending |
| INTEG-01 | Phase 6 | Pending |
| INTEG-02 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0 ✓

---
*Requirements defined: 2025-01-29*
