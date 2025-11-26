# Quickstart: Testing Cache Lesson Exposition

**Feature**: Exposition caching for API cost reduction  
**Branch**: `002-cache-lesson-exposition`  
**Date**: 2025-11-25

## Overview

This guide shows how to verify that exposition caching is working correctly after implementation. The cache should reduce LLM API calls by ~90% and improve session start times from ~3s to < 0.5s for cached expositions.

---

## Prerequisites

1. **Feature implemented**: Code changes from this plan are applied
2. **Database migrated**: `cached_expositions` table exists
3. **Application running**: Bloom server started locally

---

## Verification Steps

### Step 1: Database Schema Check

Verify the new table exists:

```bash
sqlite3 bloom.db ".schema cached_expositions"
```

**Expected Output**:
```sql
CREATE TABLE cached_expositions (
    subtopic_id INTEGER PRIMARY KEY,
    exposition_content TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    model_identifier TEXT NOT NULL,
    FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
);
```

---

### Step 2: Clear Cache (Ensure Fresh Start)

Start with an empty cache to test cache miss behavior:

```bash
sqlite3 bloom.db "DELETE FROM cached_expositions;"
```

Or via Python:
```python
from bloom.database import get_connection

conn = get_connection("bloom.db")
conn.execute("DELETE FROM cached_expositions")
conn.commit()
conn.close()
print("✓ Cache cleared")
```

---

### Step 3: Test Cache Miss (First Session)

1. **Start the Bloom application**:
   ```bash
   uvicorn bloom.main:app --reload
   ```

2. **Open browser**: Navigate to `http://localhost:8000`

3. **Select a subtopic**: Click any subtopic (e.g., "Fractions")

4. **Observe**:
   - Session start takes ~3 seconds (LLM generation time)
   - Check logs for: `Cache MISS for subtopic X, generated and cached`
   - Exposition appears in chat interface

5. **Verify cache write**:
   ```bash
   sqlite3 bloom.db "SELECT subtopic_id, model_identifier, LENGTH(exposition_content) AS size_bytes FROM cached_expositions;"
   ```
   
   **Expected**: One row showing the subtopic ID, model used, and content size (~3000-4000 bytes)

---

### Step 4: Test Cache Hit (Second Session on Same Subtopic)

1. **Exit the session**: Click "Start Fresh" or close the chat

2. **Select the same subtopic again** (e.g., "Fractions")

3. **Observe**:
   - Session start takes < 0.5 seconds (instant)
   - Check logs for: `Cache HIT for subtopic X`
   - Exposition content is **identical** to first session

4. **Verify no new LLM call**: Check application logs—should show NO new API request to OpenAI/Anthropic

---

### Step 5: Test Content Consistency

Verify the cached exposition matches what's displayed:

1. **Copy exposition text** from the chat interface

2. **Query database**:
   ```bash
   sqlite3 bloom.db "SELECT exposition_content FROM cached_expositions WHERE subtopic_id = 101;" > cached_exposition.txt
   ```

3. **Compare**:
   ```bash
   # Should be identical (ignoring whitespace formatting)
   diff <(echo "COPIED_TEXT_FROM_CHAT") cached_exposition.txt
   ```

**Expected**: No differences (content is identical)

---

### Step 6: Test Multiple Subtopics

1. **Select different subtopic** (e.g., "Percentages")
   - Should be cache miss (generates new, caches it)

2. **Return to first subtopic** (e.g., "Fractions")
   - Should be cache hit (instant retrieval)

3. **Select second subtopic again** (e.g., "Percentages")
   - Should be cache hit (instant retrieval)

4. **Verify cache state**:
   ```bash
   sqlite3 bloom.db "SELECT subtopic_id, model_identifier, generated_at FROM cached_expositions ORDER BY generated_at;"
   ```
   
   **Expected**: Two rows (Fractions and Percentages), different timestamps

---

### Step 7: Test Model Identifier Tracking

Verify the model identifier is stored correctly:

```bash
sqlite3 bloom.db "SELECT subtopic_id, model_identifier FROM cached_expositions;"
```

**Expected Output** (example):
```
101|gpt-4
102|gpt-4
```

Or if using Claude:
```
101|claude-3-5-sonnet-20241022
102|claude-3-5-sonnet-20241022
```

Should match your `LLM_MODEL` environment variable.

---

## Performance Benchmarking

### Measure Cache Miss vs Cache Hit

Use browser DevTools Network tab or application logs:

```bash
# Enable timing logs (if implemented)
tail -f logs/bloom.log | grep "exposition_node"
```

**Expected Timings**:
- **Cache MISS**: 2500-3500 ms (LLM API call)
- **Cache HIT**: 5-50 ms (database lookup)

**Performance Improvement**: ~100x faster

---

## Admin Operations (Manual Cache Management)

### Clear Specific Subtopic Cache

If you need to refresh a specific exposition:

```sql
DELETE FROM cached_expositions WHERE subtopic_id = 101;
```

Next session on that subtopic will regenerate and cache new content.

### Clear Cache by Model

If you switch LLM models and want to regenerate all expositions:

```sql
DELETE FROM cached_expositions WHERE model_identifier = 'gpt-4';
```

### View Cache Statistics

```sql
SELECT 
    COUNT(*) AS cached_subtopics,
    MIN(generated_at) AS oldest_cache,
    MAX(generated_at) AS newest_cache,
    SUM(LENGTH(exposition_content)) AS total_cache_size_bytes
FROM cached_expositions;
```

**Example Output**:
```
cached_subtopics|oldest_cache|newest_cache|total_cache_size_bytes
15|2025-11-25T10:30:00|2025-11-25T14:45:00|48000
```

### Inspect Cached Content

```sql
SELECT 
    ce.subtopic_id,
    st.name AS subtopic_name,
    ce.model_identifier,
    LENGTH(ce.exposition_content) AS size_bytes,
    SUBSTR(ce.exposition_content, 1, 100) || '...' AS preview
FROM cached_expositions ce
JOIN subtopics st ON st.id = ce.subtopic_id;
```

---

## Troubleshooting

### Issue: Cache always shows MISS

**Possible Causes**:
1. Table not created: Run `init_database()`
2. Cache check disabled in code: Verify `get_cached_exposition()` is called
3. Wrong subtopic ID: Check logs for actual subtopic ID being queried

**Debug**:
```python
# Add debug logging in exposition_node()
logger.info(f"Checking cache for subtopic_id: {state['subtopic_id']}")
cached = get_cached_exposition(state['subtopic_id'], DATABASE_PATH)
logger.info(f"Cache result: {'HIT' if cached else 'MISS'}")
```

### Issue: Content differs between sessions

**Possible Causes**:
1. Cache write failed: Check for database write errors
2. Different subtopic selected: Verify subtopic ID in logs
3. LLM non-determinism (if cache bypassed): Temperature should be stable

**Debug**:
```bash
# Check if content is actually cached
sqlite3 bloom.db "SELECT LENGTH(exposition_content) FROM cached_expositions WHERE subtopic_id = 101;"
# Should return content size (e.g., 3500)
```

### Issue: Performance not improved

**Possible Causes**:
1. Cache HIT still calling LLM: Check code for incorrect branching
2. Database slow: Check database file size and indexing (should be fast)
3. Network latency measured: Measure only backend processing time

**Debug**:
```python
import time

start = time.time()
cached = get_cached_exposition(subtopic_id, DATABASE_PATH)
elapsed = time.time() - start

logger.info(f"Cache lookup took {elapsed*1000:.2f}ms")
# Should be < 10ms
```

---

## Success Criteria Validation

Use this checklist to confirm all success criteria (SC-001 to SC-006) are met:

- [ ] **SC-001**: Cached session start < 0.5s (measure with browser DevTools)
- [ ] **SC-002**: Check logs show ~90% cache HIT rate after initial generation
- [ ] **SC-003**: No formatting errors or corruption in cached expositions (visual inspection)
- [ ] **SC-004**: 100% cache retrieval success in Step 6 (multiple subtopics test)
- [ ] **SC-005**: Verify API cost reduction by checking LLM provider billing (optional)
- [ ] **SC-006**: Blind test: show cached vs fresh to user, ask if they notice difference

---

## Deployment Checklist

Before merging to main:

- [ ] All verification steps pass
- [ ] No errors in application logs
- [ ] Database migration applied (table exists)
- [ ] Cache statistics show expected behavior (90%+ hit rate after warmup)
- [ ] Performance improvement confirmed (< 0.5s cache hits)
- [ ] Documentation updated (README includes cache feature)

---

## Next Steps

After successful verification:

1. **Monitor in production**: Track cache hit rates and API cost reduction
2. **Consider future enhancements** (FR-007 to FR-011 marked `[LATER]`):
   - FR-007: Validate cached content before use
   - FR-008: Auto-regenerate if corrupted
   - FR-009: Admin UI for cache management
   - FR-010: Cache hit/miss logging and metrics
   - FR-011: Cache version identifier for automatic invalidation

3. **Expand caching** (future features):
   - Cache Socratic hints (after pattern analysis)
   - Cache common question types (if deterministic)
   - Cache diagnostic feedback templates

---

## Summary

This quickstart guide covers:
- ✅ Database schema verification
- ✅ Cache miss/hit testing
- ✅ Content consistency validation
- ✅ Performance benchmarking
- ✅ Admin cache management
- ✅ Troubleshooting common issues

**Expected Outcome**: 90% reduction in LLM API calls, 6x faster session starts for cached content, no user-visible changes.


