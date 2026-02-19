# claude: entries in this table should be nicely analyzed fromatted and moved to relevant todo file, including this comment

## New Entries

### A1: Revisit CacheManager design - name parameter seems redundant

**Category:** Architecture / Refactoring
**Priority:** Low
**Status:** New

**Summary:**
The current CacheManager design requires a `name` parameter when getting a cache, but this seems redundant. A simpler design with a single key might be sufficient.

**Current Usage:**

```python
cache = self._cube_layout.cache_manager.get("SliceLayout.does_slice_cut_rows_or_columns", CLGColRow)
return cache.compute(cache_key, compute)
```

**Proposed:**
Consider whether the name parameter is needed, or if a single-key cache would be simpler and sufficient.

**Context:**
Discovered while working on Issue #55 (geometry cleanup).

---

